# Decisions log

Why this is shaped the way it is. Each entry records what was chosen, what was genuinely considered, and what the choice costs — because the cost is the part that tells you whether to copy it.

**Note on names.** Every company, person and quote in this repo is invented. The reps are called Ana, Ben and Chloe; the buyers are companies that do not exist. Nothing here is drawn from a real call.

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

Re-weighting only moves the number; it doesn't create the distinction. A separate flag answers "did this call carry the new message" rather than "how many boxes were ticked". Look at Ana in the fixtures: 4 of 6 delivered, and the framing pair never lands. A coverage score alone calls that a good week.

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

---

## 11. The transcript decides who was on the call, not the invite

**Chose:** a rep is only scored and coached on calls where the transcript contains at least one turn attributed to them. If the rep a call is filed under never speaks, the call leaves the pipeline before extraction: no score, no engagement figure, no coaching line, and the exclusion is printed with its reason.

**Considered:** trusting the metadata. The meeting title, the calendar invitee list, the "recorded by" field and the CRM owner all name a rep, they are already structured, and reading them costs nothing. Also considered scoring the call but flagging it, which keeps the data and lets a human sort it out later.

**Why:** metadata says who was *invited*; only the artifact shows who was *there*. A call booked on one rep's calendar and run by a colleague is completely ordinary, and it produces a record that looks perfectly well-formed — right account, right date, real quotes, a plausible score — while being about the wrong person.

This one is not hypothetical. In production, a call titled `"<Prospect> and <Rep A>"` with Rep A on the invite was run entirely by Rep B. The pipeline credited both. Rep A was sent a coaching message that praised them for opening on the problem in the first seconds and criticised them for never landing the differentiator. Both sentences described Rep B. Every quote in it was real, every score was arithmetically correct, and the whole thing was about a conversation Rep A was not in.

Flagging instead of excluding was tempting and wrong. A flag on a row that still carries a number means the number reaches the median, the trend and the rep's own "where you land" line, and the flag is the first thing that gets skimmed past. The call has to leave, or it is in.

Two things make the rule hold rather than merely exist. The record carries `rep_turns` — a count per rep — so a zero is visible in the file without re-reading a transcript. And a test asserts that no fixture scores a rep who never spoke, so the property is checked on every run rather than trusted.

The generalisation is the useful part, because this is not really about sales calls: **whoever the record says was involved is a claim, and the artifact is the evidence.** Ticket assignees, PR authors, "reported by" fields, shift rotas and attendance lists all describe who was supposed to be there. Before a system attaches a number to a person's name, it should have to find that person in the thing it is measuring.

---

## 12. A quote has to come from the right mouth, and the transcript has to know whose it is

**Chose:** two further attribution checks. A message element may only be marked *delivered* if its quote comes from a turn the **rep** spoke; engagement evidence must come from a turn the **buyer** spoke. And a transcript that returns fewer than two distinct speaker labels is refused outright — no message score, no engagement score, no coaching.

**Considered:** trusting the extractor, which is reading the transcript and can see who is talking. Also considered scoring merged transcripts with a confidence flag, since the model can usually reconstruct who said what from context and it very nearly always looks right.

**Why:** Decision 4 required a verbatim quote and the checker looked for it *anywhere in the call*. That is a different question from the one that matters. The buyer saying "we need a shopfloor management system" is the single best thing that can happen on a call — it is the echo, which Decision 5 deliberately refuses to score because measuring it destroys it. Under a quote-exists check, that same sentence scores as the rep **delivering** the category. The most valuable signal in the system arrives through the back door as a point for the wrong person.

The mirror matters as much. Engagement measures what the buyer did; if the rep says "everyone gets excited about this bit", that is not excitement, it is a sales line. Scored from the wrong mouth it becomes buyer enthusiasm that never happened.

The diarisation gate came from a production call that returned as one continuous twenty-minute block under a single speaker label. Every quote in it was real. Who said any of them was reconstructed from context by the model, and the call was scored 83 for message coverage and 87 for engagement — both sides of a conversation the transcript could not actually distinguish. The confidence-flag version is the trap here: a flag on a row that still carries two numbers means both numbers reach the rep's average and the flag gets skimmed, which is the same mistake as Decision 11 in a new costume.

**What it cost:** the engagement check found a fixture in this repo whose quote read *"And contract renewals sitting with legal"* where the buyer had said *"Contract renewals sitting with legal"*. A fabricated leading word, invisible for months, because nothing had ever verified engagement evidence at all. That is the argument for the check in one line: the invariants nothing tests are the ones quietly untrue.

---

## 13. The score has to be able to go down, and it is not called coaching

**Chose:** engagement carries a **reservations** deduction — explicit hedges, deferrals, no-urgency statements and unresolved objections, each with a verbatim buyer quote, counting double in the last third of the call. Message elements that are the *point* of a given meeting are declared per call type and never reported as "what worked". And the per-rep artifact is a **message check**, not a coaching message.

**Considered:** leaving engagement as it was and telling reps to read it as "how much the buyer engaged" rather than "how well it went". Also considered a model-scored sentiment or warmth field, which is the obvious fix and the one every demo reaches for.

**Why:** the first version could only go up. Every component was a count of something positive, so a buyer who said three warm things and then spent the rest of the call explaining why not scored as an engaged call. A real one did: 74 out of 100 on a conversation the rep wanted to disqualify. His words — *"yes he said that, the entire rest of the call was the 'but'"*.

Telling people to reinterpret the number does not work. If a report says *your strongest call, 74/100* about a call that ended in a polite no, the rep has to argue with the report, and that costs more attention than the report saves. A measure that cannot represent a "no" is not measuring the thing anyone cares about.

Sentiment scoring was the tempting fix and would have been the third version of the same mistake this repo keeps making: a confident number with nothing verifiable underneath. Reservations are counted the way everything else here is counted — a quote, or it did not happen. Late ones count double because that is where a call lands: enthusiasm followed by a "but" is a no, and a "but" followed by enthusiasm is a maybe.

The call-type expectations came from the same conversation. Opening on the customer's problem during a *proposal* meeting is not an achievement, it is the meeting. Scoring it as a win is noise, and noise in a report about someone's work is what teaches them to stop reading it.

**On the name.** It was called coaching, and that word claims something the artifact cannot deliver. Coaching implies someone who watched, who holds context, who is accountable for your development. This reads a transcript. The rep who pushed back put it exactly: *"I am up for coaching, if a coach is present and is willing to watch the calls for context. I'm kind of against having an AI scan my calls with no context and give me advice."* He is right, and the honest fix is not a better tone — it is a smaller claim. **Message check**: here is what the agreed message did and did not do on this call, with the quotes; you decide what it means. Everything the artifact actually does survives the rename. Only the authority it was borrowing goes away.

---

## 14. The daily message carries no scores, and compares the rep to nobody

**Chose:** the daily message states how many calls were analysed and then says only what happened — objections, what worked, one thing to do differently, moments worth re-hearing, and what the system could not see. No score of any kind, and no comparison to a colleague or a team figure. Scores appear once a week, next to that rep's *own* previous week.

**Considered:** keeping a rolling seven-day figure in the daily so the number always had a reasonable sample behind it. Also considered keeping the team median, which had been the only comparison shown and felt like the safe, impersonal one.

**Why:** the rolling window was a workaround for a question nobody asked. A rep reading a daily message wants to know what to do today; the number was there because it was easy to compute, and it invited them to argue with the sample instead of reading the evidence. One to four calls cannot support a number about a person, and printing one anyway teaches the reader that the message is padded.

The team median turned out to be worse than useless at small headcount. With two or three people actually pitching, "the team" is one colleague wearing a disguise: the strongest rep reads his own number labelled as everyone's, and everyone else reads his. It looks impersonal and functions as a ranking. The only comparison that survives is a rep against their own last week, which is also the only one that answers a question they have.

**What prompted it.** A rep pushed back on the whole artifact, and the two specific things he named were both true (Decision 13). The third thing he said was quieter and mattered more: *"I then have to spend my mental energy trying to correct it."* A wrong line in a report is not neutral — it costs the attention the report was supposed to save. Everything above follows from taking that seriously. Strip anything the evidence cannot carry, and what remains is worth reading.

He also asked for something we had not built: the objections he faced, in the buyer's words, with what he said back. That is now the second section of every message, and the deliberate omission is the answer — the system reports what was asked and never invents what should have been said, because a system improvising product claims at scale is a far worse failure than a bad score.

**The generalisation:** *a measure earns its place by changing what someone does.* Coverage scores, team medians and rolling averages all survive in reporting systems because they are cheap to compute and look rigorous, not because anyone acts on them. The test is not "is this number correct" but "if this number were different, would the reader do something different today". Most numbers in most reports fail it.

---

## 15. A message that was written is not a message that arrived

**Chose:** treat *ran* and *arrived* as two separate states. Every run writes a delivery receipt naming each message it intended to send and whether the send call actually succeeded. A separate job reads those receipts, and treats **a missing receipt as an alarm in its own right**. The alarm reaches the operator through a channel the pipeline does not use.

**Considered:** the obvious thing, which is what was already there — the run reports success or failure at the end, and sends an alert if it fails. Also considered simply checking the run's exit code, which is what most schedulers give you for free.

**Why:** exit codes describe the process, not the outcome. A run can read every call, score it correctly, write the message, archive it, and exit zero, having delivered nothing to anybody. That is not a hypothetical — it happened, and the run's own summary said it had completed. Green process, empty inbox. Nobody found out for five hours, and only by asking.

The worse version is the one that happened twice. The failure alert used the same channel as the messages, so when that channel was unavailable the messages did not send **and** nothing said so. An alarm that shares a failure mode with the thing it is watching is not an alarm; it is a second copy of the same risk. If the pipeline sends over Slack, the alarm must not. Ours now raises a desktop notification and writes a file, and reaches for the shared channel only as a bonus.

**Four traps found while building the check**, all of which are easier to fall into than to spot:

**A guard that can never pass.** The pre-send check required a field that only began being recorded partway through the project. Every message citing an older call would have failed it — silently, for ever, because "withheld" looked identical to "nothing was due". A guard must be able to succeed on the data it will actually see, and the way to find out is to run it against last week rather than against a fixture.

**An alarm that cries wolf.** The first version treated a missing receipt as a failure every day, including the days the system deliberately sends nothing. It would have fired twice a week, every week, and within a fortnight the operator would have learned to dismiss it — at which point it would not work on the day it mattered. **The cost of a false alarm is not the interruption; it is the credibility of every future alarm.**

**A test that is indistinguishable from the real thing.** Verifying the alarm meant firing it, which put a genuine-looking alert in front of the operator for a fabricated failure. If an alarm is worth building it is worth building a dry-run mode, because the first thing anyone does with a new alarm is test it.

**A receipt with more than one author.** Three jobs run on different schedules, and each was told to write the receipt by overwriting it. That is fine four days a week and wrong on the fifth, when two of them run on the same day: the later one erases the earlier one's evidence before anything has archived it, and the check quietly falls back to inferring delivery from logs — the exact fallback the receipts were built to replace. Nothing had been lost when this was found, because the schedules had not yet collided; it was found by reading the writers rather than the data. **A record that several writers share is not a record until you decide what happens when two of them write.** Now the archive merges on (recipient, kind) instead of replacing, and each run archives its own receipt the moment it finishes rather than waiting for a reader that may be days away.

**The generalisation, which is not about messages:** *instrument the outcome you actually care about, not the step you happen to be able to measure.* Exit codes, HTTP 200s and "job completed" are all proxies for delivery, and each of them is satisfied by systems that delivered nothing. The same mistake in a different costume: earlier the same day, a page was confirmed live because the URL returned 200 — it did, and it was serving the wrong content the whole time.
