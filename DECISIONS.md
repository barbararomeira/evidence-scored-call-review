# Decisions log

Why this is shaped the way it is. Each entry records what was chosen, what was genuinely considered, and what the choice costs — because the cost is the part that tells you whether to copy it.

**Note on names.** Every company, rep and quote in this repo is invented. `R-02` is an opaque id, not a person.

---

## 1. Read the transcript once; every metric reads the call record, not the transcript

**Chose:** one extraction pass emits one call record per call. The message score, the engagement score, the coaching and any future consumer read only that record.

**Considered:** a separate pass per metric, so each analysis stays self-contained and can evolve without touching the others.

**Why:** the transcript is the expensive input and the only non-deterministic step. One pass makes cost linear in calls rather than calls × metrics — but the real reason is consistency. Two passes over the same call can disagree about whether the rep named the category, and then a coaching message contradicts the summary a manager is reading. The record becomes the single fact base. The price is that adding a new signal means re-extracting the archive; that is the right price, and it is cheap because the archive is on disk.

This is also what made the original system worth building at all: those calls were already being read every morning for an unrelated purpose. The second question cost one extra step, not a new pipeline.

---

## 2. Calls that were never a pitch get no message score — not a zero

**Chose:** a scope gate runs before message scoring. Pricing, scheduling, implementation and pure scoping calls return `message: None` with the reason printed next to it. They still get an engagement score.

**Considered:** score every call with the same elements and let unmet ones come out `absent`. Comparable across all calls, no call-type classification needed, much simpler.

**Why:** because the simpler version produces a specific, damaging lie. A rubric that forces "did they frame the problem?" onto a pricing negotiation will mark it absent, and the call scores zero — not because the rep did anything wrong, but because the question didn't apply. Put three of those in one rep's week and a manager reads that they failed most of their calls.

A score that can only be produced when the question applies is worth more than one that is always available and sometimes meaningless.

The cost is that call-type classification becomes load-bearing: a misclassified pitch escapes scoring silently. That is mitigated by printing the refusal and its reason on the face of the report, so a gate firing too often is visible rather than hidden.

---

## 3. No quote, no credit — and no quote, no penalty either

**Chose:** every element verdict carries a verbatim quote, checked by substring match against that call's own transcript. `delivered` needs one. So does `absent`: the passage where the element should have appeared.

**Considered:** requiring evidence only for positive verdicts. Cheaper, and absence is genuinely harder to evidence than presence.

**Why:** one-directional evidence builds a scorer that is rigorous about praise and casual about blame, which is exactly backwards for something a person will be assessed on. Requiring the model to point at *where* something was missing forces it to look rather than assume, and it turns every disputed score into a thirty-second conversation about a specific line instead of an argument about the model.

The check is deliberately dumb — normalised substring matching, no fuzzy similarity. A quote that has been paraphrased into something the buyer never said is exactly what should fail.

Cost: longer records, and occasional rejected verdicts needing a re-ask.

---

## 4. Two scores, never blended into one

**Chose:** message delivered and engagement are reported side by side, never averaged, weighted together, or combined into a ranking.

**Considered:** a single "call quality" score. Easier to sort, chart, and set a target against.

**Why:** they answer different questions with different owners. Message is whether the rep said what the company decided to say — a training question. Engagement is whether the buyer leaned in — partly the rep, largely the account they were handed. Blending them lets a great meeting with an off-message pitch hide inside a decent average, and that combination is precisely what the system was built to surface.

Cost: no single number for a leaderboard. Intentional.

---

## 5. Echo is recorded and deliberately not scored

**Chose:** when a buyer repeats your framing in their own words, capture it and display it. `score: false` in the rubric file.

**Considered:** folding it into the message score as a seventh element, or into engagement as a fifth component. It is arguably the best evidence the message actually landed.

**Why:** which is exactly why it must not count. The moment echo scores points, reps fish for it — "so would you say this is about X?" — and the signal is destroyed by the act of measuring it. Kept as an observation it stays honest, and it remains useful for judging whether the positioning itself is any good, as distinct from whether people are delivering it.

Revisit only if there is a way to distinguish spontaneous echo from prompted echo.

---

## 6. The framing pair is reported separately, not weighted into the score

**Chose:** report whether the two framing elements landed *together* as its own flag, alongside the coverage percentage.

**Considered:** weighting those two elements more heavily inside the coverage score.

**Why:** this exists because a calibration failed. Checking the scorer against calls that had been read by hand, one disagreed: an off-message call still scored well, because four promises landed cleanly while the frame around them was the previous pitch. Coverage scoring is structurally blind to this — it counts elements, and the frame is a property of the combination.

Re-weighting only moves the number; it doesn't create the distinction. A separate flag answers "did this call carry the new message" rather than "how many boxes were ticked". Look at `R-02` in the fixtures: 4 of 6 delivered, and the framing pair never lands. A coverage score alone calls that a good week.

---

## 7. Print n always; suppress the verdict below five

**Chose:** every aggregate shows its sample size. Below five, the number still prints, but any interpretation is replaced by `not enough data yet`.

**Considered:** hiding thin aggregates entirely, or showing them with a confidence interval.

**Why:** hiding them teaches the reader that the report is unreliable, and they start asking for the raw data — which defeats the report. Confidence intervals are the correct statistics and the wrong interface: they get read as "the number is fine, there's just a squiggle". Showing the number with the verdict withheld is the honest middle — the reader sees exactly what is known and is told, in words, not to act on it yet.

Five is a judgment call about a weekly cadence with a handful of pitches per rep. It lives in one constant, `MIN_N_FOR_VERDICT`, so it can be argued with.

---

## 8. Short calls are bucketed on raw counts, not extrapolated

**Chose:** below fifteen minutes, back-and-forth uses the raw count of questions and substantive turns rather than the per-30-minute rate.

**Considered:** normalising everything, for comparability.

**Why:** a nine-minute scheduling call with four exchanges extrapolates to thirteen per half hour, which lands in the top bucket. The maths is right and the conclusion is nonsense: nothing about that call was highly engaged. Rate metrics on short samples manufacture signal, and the shortest calls are exactly the ones where it matters least.

Cost: a discontinuity at fifteen minutes. Accepted, and visible in the rubric file rather than buried in code.

---

## 9. Coaching content is selected deterministically; only extraction is model-shaped

**Chose:** which moment to praise, which miss to name and which single improvement to ask for are chosen by Python from the scored record. The model's only job is turning a transcript into structured evidence.

**Considered:** handing the model the record and letting it write the whole message. It would read better and take much less code.

**Why:** a model choosing which weakness to raise drifts toward whatever is most narratable rather than most consequential, varies week to week for the same rep, and cannot be tested. Deterministic selection means the same evidence always produces the same coaching, the rule is reviewable, and a rep asking "why this one?" gets an answer rather than a shrug.

There is a real bug this prevented, kept here because it is instructive: an early version fell back to an *excitement* quote when no echo existed, while keeping the sentence "they gave your framing back to you". It claimed evidence that did not exist, in a system whose entire argument is that evidence is required. A phrasing pass over fixed content would be a reasonable addition. The *selection* stays in code.

---

## 10. Stdlib only, and the quickstart runs offline

**Chose:** zero runtime dependencies. `git clone` then one command, with no install step, no key and no network.

**Considered:** pandas for the aggregation, pydantic for the schema, jinja2 for rendering. All three would make the code shorter.

**Why:** the first thirty seconds decide whether anyone copies this. A dependency list is a reason to close the tab, and an API key is a reason to never start. Making the *model* the only optional part — mocked by default — means the whole system is inspectable without spending anything.

Cost: hand-rolled front-matter parsing and bucket logic that a library would do better. Contained, and tested.
