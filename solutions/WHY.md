# Why these solutions look like this

Read the code, but read this first. The examinable content of Module 1 is in the
reasoning, not the syntax. Every solution runs on its own — `python3
solutions/lab_0K.py` from `exercises/`, or `make demo` for all four — and
narrates what it loads, each number it measures with its unit, and what the
check will look for, then writes its figure under `out/`.

## Lab 1 — order first, then the mean

Two lessons, and the first one has to come first.

**The rows are not in time order.** 11,143 of the 48,289 consecutive row pairs in
`bus_slice.csv.gz` step backwards in `utc_time`, and the largest step backwards
is 3102.5 seconds. The file ships that way on purpose: it is how the file arrived
from the trial, and sorting it for you would teach you to trust files. Nothing
announces the disorder — it loads, the columns are sensible, the row count is
right, and every function you call still returns a number.

A lag is a shift by position. It only means a shift in time when the positions
are in time order. Measured on the same speed column of the same slice, lag one
gives about **0.9608** as the file ships and about **0.9970** once the rows are
sorted by `utc_time`. Neither number is a mistake; they answer two different
questions, and only the timestamp tells you which one you asked. That is the
monotone-timestamp rule on its definition slide, and why `lag_one_both_ways`
reports both numbers instead of one.

Note the direction. The disorder pushes the correlation *down*, towards what
independent draws would look like. A distortion that makes data look messier gets
investigated. A distortion that makes data look more independent than it is gets
believed, because it licenses the convenient decision — a random split.

The rule that prevents all of it costs a single line: ask whether the timestamp
is monotonically increasing before you compute anything that depends on order —
a lag, a difference, a rolling average, a split by date.

**The estimator is the one on the slide.** The definition slide states the
Box–Jenkins sample autocorrelation (Box, Jenkins, Reinsel & Ljung 2015 §2.1;
Hyndman & Athanasopoulos 2021 §2.8):

    r_k = Σ_{t=k+1}^{n} (x_t − x̄)(x_{t−k} − x̄) / Σ_{t=1}^{n} (x_t − x̄)²

— one mean and one denominator over the whole series. `pandas.Series.autocorr`
computes something else: the Pearson correlation of the two shifted copies, each
with its own mean and spread over the overlap. The two agree to four decimals at
lag 1 on this data and differ by about 4.5e-4 at lag 120 (0.0874 against 0.0878
as the file ships), which is past the check's tolerance — so the check names the
estimator it grades, and tells a student who wrote the other one exactly which
one they wrote. Both are legitimate statistics; the point of a definition card is
that everybody computes the same one, and that the number a student reads off a
textbook or a library matches the number on the slide.

**The mean is not optional.** Correlation measures how the values vary *around
their centre*. Multiply raw values and you measure magnitude instead, which on a
mostly-positive series returns something near 1 no matter what the data does.
The check runs a shuffled control for exactly this reason.

The stated choices matter as much as the arithmetic. A pair enters the numerator
only when both of its members are present *where they stand*; dropping the
missing values first and closing the gap pairs readings that were never
neighbours. And below thirty surviving pairs the function refuses to answer,
because two points always lie on a line: a correlation from a handful of pairs
is +1 or −1 whatever the data does. That last rule is one `pandas.Series.autocorr`
does not implement, which is why calling it here is not merely against the rules
but wrong.

The measured answer — consecutive readings, in time order, correlating at about
0.997 — is the argument for splitting by time (Bergmeir & Benítez 2012; Roberts
et al. 2017). It is not a convention. A random split places a reading and its own
neighbour on opposite sides of the boundary, so the test set is a paraphrase of
the training set. And 48,290 rows at that autocorrelation are worth about 73
independent observations (Bayley & Hammersley 1946) — resolution, not evidence.

## Lab 2 — read the error before deciding what to do about it

Three exceptions, three correct and different responses, and each is a status
code of the hypertext transfer protocol standard: Throttled is a 429 Too Many
Requests carrying Retry-After (RFC 6585 §4; RFC 9110 §10.2.3), ServerBusy a 500
(RFC 9110 §15.6.1), NoSuchDay a 404 (RFC 9110 §15.5.5). The failure the lab hunts
is `except Exception: retry`, which catches the permanent error along with the
temporary ones and loops forever while looking diligent.

Also note what is absent: no break on a short page. The loop ends when the
provider says there is no next cursor, and only then. Stopping early gives you
three quarters of a day and no warning at all — the worst failure mode in
collection, because nothing complains. "Every record once, in order" is the
idempotence of RFC 9110 §9.2.2 seen from the collector's side; at-least-once
delivery plus de-duplication by identifier is the achievable guarantee
(Kleppmann 2017, ch. 11 of the first edition).

The five attempts on a temporary failure are a stated choice; the check grades
that a permanent error is never repeated, not the number.

## Lab 3 — describe, do not repair

Every instinct to fix something is postponed. The negative speeds stay; the
ceiling values stay. A profile that has quietly cleaned its subject describes a
dataset nobody has.

The five dimensions are the DAMA UK (2013) list minus accuracy, each written as
a ratio or a count after Pipino, Lee & Wang (2002), and each has its own
definition card: completeness as a share per column (not rounded, because a
column complete on all but one row in fifty thousand is not complete);
uniqueness as two counts against a stated key; validity as counts against
stated rules, with 65535 named as the sentinel it is; consistency as the set of
offsets between two clocks; timeliness as a median and a count within a day.

Validity is the interesting one. `speed` below zero is only invalid if the field
is a speed. If it is a signed velocity, the vehicle is reversing and the rows are
correct. You cannot decide without the data dictionary — so count them, and say
which question you could not answer. That is also why the profile document has a
fixed format: it is read by a program, and a fact under a name nobody thinks to
look for is a fact nobody checks (Riley 2017; Gebru et al. 2021).

### The declaration is a commitment, and both ends of it are work

`DATA_PROFILE.md` persuades a person. `out/data_profile.json` instructs a
program, and it is the file Module 2 loads before it touches a row — the schema
is fixed in `HANDOFF.md` and neither module may change it quietly.

Turning a measurement into a rule is where the thinking is. A range is widened
from what was observed by five per cent of the observed span and a column is
allowed one percentage point of absence beyond what it showed; both numbers are
choices, both are printed beside what they produce, and both are the whole
difference between a profile that cries wolf every morning and one that never
barks. Declare too tightly and tomorrow's ordinary day is reported broken until
nobody believes the alarm. Declare too loosely and nothing can ever violate it —
a range admitting a shuttle at 999 metres per second is not a range, and the
check lands exactly that day on you.

Two entries are deliberately empty. `payload` and `mileage` carry `"unit": null`
because nobody ever wrote a unit down for them, and inventing one would put a
guess into a file the next module believes. A null in a profile is a finding.

`check_against()` runs its rules in a fixed order — presence, type, range,
missing share, step — and the order is part of the contract because each rule
assumes what the one before it established. A column that is absent has no type.
A column of the wrong type cannot be range-checked without raising, and a crash
is not a complaint. Every line begins with the field it concerns, because
whoever reads it at seven in the morning needs the name before the sentence.

### The verdict is the only place the check does not know the answer

`fitness_verdict()` returns a call — `use`, `use with a caveat`, `do not use` —
and the argument for it. The check holds no threshold of its own. It reads the
`FITNESS_LIMITS` you declared and grades whether your five verdicts obey your own
boundary and each other: the day that is at least as good as every other on all
five quantities must not be refused, the day at least as bad on all five must not
be used, a day with any quantity outside your own limits may not be called `use`,
a day no worse than another on any quantity may not receive the harsher call, and
every number in your reason must be one of the numbers you were handed.

The reference boundary in `lab_03.py` is mine and is not the answer. What it owes
the room is five sentences, one per limit: a column absent on more than one row
in twenty is a column you would be imputing rather than using; a gap longer than
ten minutes means any average across it describes a window that did not exist;
more than one consecutive pair in fifty out of time order is a file whose order
carries no information; fewer than a hundred independent readings is one
observation rather than a sample (Bayley & Hammersley 1946); more than one row in
fifty outside your own declared ranges and the data is not the thing your profile
describes.

The split that matters is not those five numbers but the two tiers. Three of the
breaches name an operation, so a caveat repairs them: sort the rows, exclude the
window around the long gap, widen every interval to the effective number of
independent readings. Two do not. A column that is absent has no subset of the
day where it is present, so there is no window to exclude; and rows outside the
declared range cannot be dropped without knowing which rows they are. Nothing
breached, use it; a fatal quantity breached, refuse it; anything else, use it
with the breach written down as a condition specific enough for Module 2 to act
on.

The slice comes out `use with a caveat`, and the caveat — order it, exclude the
long gap, do not treat 48,290 rows as 48,290 observations — is exactly what the
next module needs to be told. Quality is fitness for use and it has many
dimensions (Wang & Strong 1996; Batini et al. 2009); the five numbers are the
evidence, and the verdict is the measurement that matters.

## Lab 4 — the invariant is what you are protecting

Write, flush, fsync, rename, record. At every instant the manifest is a subset of
what is really on disk. Any other order breaks that:

- manifest first — after a kill you claim data you do not have, and nobody goes
  looking for it because the record says it arrived
- no fsync — the rename is atomic but the bytes may still be buffered
- straight to the destination — a kill leaves half a file, permanently, unmarked

The rename's atomicity within one filesystem is not folklore: the portable
operating system interface standard promises that when the new name already
exists it stays visible throughout the operation and refers to the old file or
the new, never to neither (IEEE & The Open Group 2018, rename()). Atomicity and
durability are two of the four database promises (Haerder & Reuter 1983), had
here without a database.

The three manifest key names — `file`, `records`, `sha256` — are fixed by the
lab rather than left to taste, and the checksum is SHA-256 (NIST 2015, FIPS
180-4). The check treats a missing `sha256` as a failed integrity test rather
than a test to skip. A manifest is read by somebody who did not write it, months
later and possibly by a program. A checksum filed under a name nobody thinks to
look for is a checksum nobody checks, which is the same as not having one while
feeling as though you do.

There is a fifth step, and it is a property rather than an action: land the same
payload twice and the manifest must hold one entry, not two. After a kill you
cannot know whether the manifest line was appended, so the only safe move is to
land it again — and that is only safe if landing it again changes nothing. The
landing's identifier is the pair (file name, checksum), which is what makes the
distinction the check tests: the same bytes under the same name are a repeat and
are recorded once, while different bytes under the same name are a second landing
and are recorded, or the manifest quietly describes a file that has been
replaced. This is the other half of Lab 2's bargain — at-least-once delivery is
only usable because the receiving step is idempotent (Fielding, Nottingham &
Reschke 2022, §9.2.2; Kleppmann 2017).

Replay takes a byte offset, not a record number (Kreps 2013): one seek, no
re-read, and one record per line so that a byte offset and a record boundary
coincide.

The format measurement usually surprises: the smallest file is not the fastest to
read. Report what you measured, especially when it contradicts what you expected
(Zeng et al. 2023 do the same at scale).

## References

- Box, G. E. P., Jenkins, G. M., Reinsel, G. C. & Ljung, G. M. (2015). *Time
  Series Analysis: Forecasting and Control*, 5th ed., §2.1. Wiley.
- Hyndman, R. J. & Athanasopoulos, G. (2021). *Forecasting: Principles and
  Practice*, 3rd ed., §2.8. OTexts.
- Bayley, G. V. & Hammersley, J. M. (1946). *The "Effective" Number of Independent
  Observations in an Autocorrelated Time Series.* Suppl. J. Roy. Statist. Soc. 8(2).
- Bergmeir, C. & Benítez, J. M. (2012). *On the use of cross-validation for time
  series predictor evaluation.* Information Sciences 191.
- Roberts, D. R. et al. (2017). *Cross-validation strategies for data with temporal,
  spatial, hierarchical, or phylogenetic structure.* Ecography 40(8).
- Fielding, R., Nottingham, M. & Reschke, J. (2022). *HTTP Semantics.* RFC 9110;
  Nottingham, M. & Fielding, R. (2012). *Additional HTTP Status Codes.* RFC 6585.
- Kleppmann, M. (2017). *Designing Data-Intensive Applications*, 1st ed., ch. 11. O'Reilly.
- DAMA UK Working Group (2013). *The Six Primary Dimensions for Data Quality Assessment.*
- Pipino, L. L., Lee, Y. W. & Wang, R. Y. (2002). *Data Quality Assessment.* CACM 45(4).
- Wang, R. Y. & Strong, D. M. (1996). *Beyond Accuracy: What Data Quality Means to
  Data Consumers.* Journal of Management Information Systems 12(4).
- Batini, C., Cappiello, C., Francalanci, C. & Maurino, A. (2009). *Methodologies for
  Data Quality Assessment and Improvement.* ACM Computing Surveys 41(3).
- Riley, J. (2017). *Understanding Metadata.* NISO; Gebru, T. et al. (2021).
  *Datasheets for Datasets.* CACM 64(12).
- IEEE & The Open Group (2018). IEEE Std 1003.1-2017, rename().
- NIST (2015). *Secure Hash Standard.* FIPS 180-4.
- Haerder, T. & Reuter, A. (1983). *Principles of Transaction-Oriented Database
  Recovery.* ACM Computing Surveys 15(4).
- Kreps, J. (2013). *The Log: What every software engineer should know about
  real-time data's unifying abstraction.*
- Zeng, X. et al. (2023). *An Empirical Evaluation of Columnar Storage Formats.* PVLDB 17(2).
