# Module 1 — Reading, and the exam question

## Required, before Module 2

**Kreps, J. (2013). *The Log: What every software engineer should know about
real-time data's unifying abstraction*.**
<https://www.linkedin.com/blog/engineering/distributed-systems/log-what-every-software-engineer-should-know-about-real-time-datas-unifying>

Free, and about four pages of the clearest writing in the field. Read the first
two sections. You built a small version of this in Lab 4; the article tells you
why the idea generalises to everything from a database's internals to Apache
Kafka. The book-length form is **Kreps, J. (2014). *I Heart Logs: Event Data,
Stream Processing, and Data Integration*. O'Reilly. ISBN 978-1-491-90938-6** —
through the AAU library, optional.

## Recommended

**Helland, P. (2015). *Immutability Changes Everything*. ACM Queue 13(9).**
<https://doi.org/10.1145/2857274.2884038> — free. Why keeping originals
read-only is the cheapest insurance in a pipeline.

**Wang, R. Y. & Strong, D. M. (1996). *Beyond Accuracy: What Data Quality Means to
Data Consumers*. Journal of Management Information Systems 12(4), 5–33.**
<https://doi.org/10.1080/07421222.1996.11518099> — through the AAU library. The
paper that established quality as fitness for use, with many dimensions. Note
what it does not do: it names neither uniqueness nor validity. The five names you
measured in Lab 3 are the DAMA UK list below.

**Kleppmann, M. (2017). *Designing Data-Intensive Applications*, first edition,
chapter 11 "Stream Processing", sections "Transmitting Event Streams" and
"Databases and Streams" (~20 pages). O'Reilly.** Through the AAU library — the
book is licensed, so there is no file here and there will not be one. The second
edition (2026) renumbers the chapter to 12. This is where at-least-once delivery
plus de-duplication is spelled out, the guarantee Lab 2's collector gives.

**Huyen, C. (2022). *Designing Machine Learning Systems*, chapter 3 "Data
Engineering Fundamentals". O'Reilly.** Through the AAU library.

**Riley, J. (2017). *Understanding Metadata: What is Metadata, and What is it For?
A Primer*. NISO. ISBN 978-1-937522-72-8.**
<https://www.niso.org/publications/understanding-metadata-2017> — free and short.
It replaces the 2004 leaflet this course used to cite. Read the first ten pages
for what a data dictionary is for.

**Regulation (EU) 2016/679 (GDPR), Articles 4–6.**
<https://eur-lex.europa.eu/eli/reg/2016/679/oj> — read the definitions in
Article 4 and the six lawful bases in Article 6. Nothing else.

**Regulation (EU) 2024/1689, the Artificial Intelligence Act, Article 10.**
<https://eur-lex.europa.eu/eli/reg/2024/1689/oj> — free. One article, and only
the parts about data: paragraph 3, which says training, validation and testing
data must be relevant, sufficiently representative and, to the best extent
possible, free of errors and complete in view of the intended purpose; and
paragraph 2, points (f) and (h), the examination for bias and the identification
of data gaps and shortcomings. Read it after Lab 3 and notice that the profile
you wrote is what the article asks for. The obligations for the high-risk uses in
Annex III apply from 2 December 2027, moved there by **Regulation (EU) 2026/1744**,
the Digital Omnibus on artificial intelligence
(<https://eur-lex.europa.eu/eli/reg/2026/1744/oj>).

> Nothing licensed is redistributed in this repository. Where a reading is a
> commercial book you get a library link and a chapter number, which is what you
> would need anyway.

## The sources behind the definition cards

Every concept a lab grades has a definition card in the deck — the formula, the
choices, and the source — and the same formula sits in the stub under
"Definition graded by the check". These are the sources, in the order the labs
meet them; each is one paragraph on what to read it for.

**Box, G. E. P., Jenkins, G. M., Reinsel, G. C. & Ljung, G. M. (2015). *Time
Series Analysis: Forecasting and Control*, 5th edition, §2.1. Wiley. ISBN
978-1-118-67502-1.** Through the AAU library. Section 2.1 defines the
autocorrelation function of a stationary series and its sample estimate — the
r_k Lab 1 grades: one mean, one denominator, over the whole series.

**Hyndman, R. J. & Athanasopoulos, G. (2021). *Forecasting: Principles and
Practice*, 3rd edition, §2.8.** <https://otexts.com/fpp3/acf.html> — free. The
same formula printed in one line with a worked example; read it if the book
above is heavy going. Section 2.8 is two pages.

**Bayley, G. V. & Hammersley, J. M. (1946). *The "Effective" Number of Independent
Observations in an Autocorrelated Time Series*. Supplement to the Journal of the
Royal Statistical Society 8(2), 184–197.** <https://doi.org/10.2307/2983560> —
through the AAU library. Where n(1 − ρ)/(1 + ρ) comes from: 48,290 readings at
ρ = 0.997 are worth about 73 independent observations. Read the first two pages.

**Bergmeir, C. & Benítez, J. M. (2012). *On the use of cross-validation for time
series predictor evaluation*. Information Sciences 191, 192–213.**
<https://doi.org/10.1016/j.ins.2011.12.028> — through the AAU library. Why a
split has to respect time, and what blocked cross-validation is. Read the
introduction and the conclusions.

**Roberts, D. R. et al. (2017). *Cross-validation strategies for data with
temporal, spatial, hierarchical, or phylogenetic structure*. Ecography 40(8),
913–929.** <https://doi.org/10.1111/ecog.02881> — free. The same argument made
for every kind of structure at once: no test observation may be a neighbour of a
training one. Read the first section and look at Figure 1.

**Fielding, R., Nottingham, M. & Reschke, J. (2022). *HTTP Semantics*. Request
for Comments (RFC) 9110, Internet Engineering Task Force.** (HTTP is the
Hypertext Transfer Protocol.)
<https://www.rfc-editor.org/rfc/rfc9110> — free. Section 9.2.2 (idempotent
methods), 10.2.3 (Retry-After), 15.5.5 (404 Not Found), 15.6.1 (500 Internal
Server Error): the four rules Lab 2's collector implements, in the words of the
standard.

**Nottingham, M. & Fielding, R. (2012). *Additional HTTP Status Codes*. Request
for Comments 6585, Internet Engineering Task Force.**
<https://www.rfc-editor.org/rfc/rfc6585> — free. Section 4 defines 429 Too Many
Requests, the refusal Lab 2's mock raises as Throttled.

**DAMA UK Working Group (2013). *The Six Primary Dimensions for Data Quality
Assessment*. DAMA UK, October 2013.** A white paper of the Data Management
Association UK; copies circulate freely and the DAMA UK site holds it for
members. The list Lab 3 measures — completeness, uniqueness, validity,
consistency, timeliness — is this list minus accuracy, which the archive cannot
measure without a second instrument. Read the one-page definition of each.

**Pipino, L. L., Lee, Y. W. & Wang, R. Y. (2002). *Data Quality Assessment*.
Communications of the Association for Computing Machinery (ACM) 45(4), 211–218.** <https://doi.org/10.1145/505248.506010>
— through the AAU library. Where the dimensions become ratios you can compute:
one minus the fraction of undesirable outcomes. Read the section on the simple
ratio.

**Batini, C., Cappiello, C., Francalanci, C. & Maurino, A. (2009).
*Methodologies for Data Quality Assessment and Improvement*. ACM Computing
Surveys 41(3), Art. 16.** <https://doi.org/10.1145/1541880.1541883> — through
the AAU library. The survey of the field; optional, for the mini-project.

**Gebru, T., Morgenstern, J., Vecchione, B., Vaughan, J. W., Wallach, H., Daumé
III, H. & Crawford, K. (2021). *Datasheets for Datasets*. Communications of the
ACM 64(12), 86–92.** <https://doi.org/10.1145/3458723> — free. The data
dictionary scaled from a field to a whole dataset: motivation, composition,
collection, uses, maintenance. Read the questions in section 3 and try them on
the archive.

**IEEE & The Open Group (2018). *The Open Group Base Specifications Issue 7,
2018 edition, IEEE Std 1003.1-2017*: rename().** (IEEE is the Institute of
Electrical and Electronics Engineers.)
<https://pubs.opengroup.org/onlinepubs/9699919799/functions/rename.html> — free.
The one sentence Lab 4 depends on: when the new name already exists, it stays
visible throughout the operation and refers either to the old file or to the
new one — never to neither. That is what makes write, fsync, rename atomic.

**NIST (2015). *Secure Hash Standard (SHS)*. Federal Information Processing
Standards Publication 180-4.** <https://doi.org/10.6028/NIST.FIPS.180-4> — free.
The National Institute of Standards and Technology's standard that defines the
Secure Hash Algorithm (SHA) in its 256-bit form, SHA-256, the checksum in Lab 4's
manifest. Nobody
reads it end to end; know that it exists and what it fixes.

**Haerder, T. & Reuter, A. (1983). *Principles of Transaction-Oriented Database
Recovery*. ACM Computing Surveys 15(4), 287–317.**
<https://doi.org/10.1145/289.291> — through the AAU library. Where the four
letters of atomicity, consistency, isolation, durability (ACID) were coined and
defined. Read the first three pages; atomicity
and durability are the two Lab 4 buys without a database.

**Zeng, X., Hui, Y., Shen, J., Pavlo, A., McKinney, W. & Zhang, H. (2023). *An
Empirical Evaluation of Columnar Storage Formats*. Proceedings of the Very Large Data
Bases (VLDB) Endowment 17(2), 148–161.** <https://doi.org/10.14778/3626292.3626298> — free.
The citable version of "measure the format on your own data": Parquet and the Optimized Row
Columnar (ORC) format measured against each other at scale. Read the introduction and the summary of
findings.

## Also cited in the deck

**Prelipcean, A. C., Gidófalvi, G. & Susilo, Y. O. (2018). *MEILI: A travel
diary collection, annotation and automation system*. Computers, Environment and
Urban Systems 70, 24–34.** <https://doi.org/10.1016/j.compenvurbsys.2018.01.011>
— through the AAU library. The source of "acceptable truth": the labels are a
measurement too.

**Servizi, V., Persson, D. R., Pereira, F. C., Villadsen, H., Bækgaard, P.,
Peled, I. & Nielsen, O. A. (2023). *"Is Not the Truth the Truth?": Analyzing
the Impact of User Validations for Bus In/Out Detection in Smartphone-Based
Surveys*. IEEE Transactions on Intelligent Transportation Systems 24(11),
11905–11920.** <https://doi.org/10.1109/TITS.2023.3291493> — through the AAU
library. The label error measured on this very trial.

**Simpson, E. H. (1951). *The Interpretation of Interaction in Contingency
Tables*. Journal of the Royal Statistical Society, Series B 13(2), 238–241.**
<https://doi.org/10.1111/j.2517-6161.1951.tb00088.x> — through the AAU library.
Why pooling the two shuttles on day one against one on day two can reverse a
difference. Module 2 works it through; Module 4 records the sign flip.

**Marz, N. & Warren, J. (2015). *Big Data: Principles and Best Practices of
Scalable Real-Time Data Systems*. Manning. ISBN 978-1-61729-034-3.** Through the
AAU library. The batch and speed layers — the cold and warm paths of the storage
slide.

**Armbrust, M. et al. (2021). *Lakehouse: A New Generation of Open Platforms that
Unify Data Warehousing and Advanced Analytics*. CIDR.**
<https://www.cidrdb.org/cidr2021/papers/cidr2021_paper17.pdf> — free. The
lakehouse only; it contains neither the medallion names nor the cold and warm
paths.

**Schmiester, L., Schälte, Y., Bergmann, F. T., et al. (2021). *PEtab —
interoperable specification of parameter estimation problems in systems
biology*. PLOS Computational Biology 17(1), e1008646.**
<https://doi.org/10.1371/journal.pcbi.1008646> — free. Read the introduction and
the "scope" section only. It is from a different discipline on purpose. A
community standardised the *problem* — model, conditions, observables,
measurements, bounds — so that different solvers became interchangeable, and
deliberately did not standardise the *measurement record*: units, assay method,
provenance, and what was left blank on purpose. That is exactly the gap your data
dictionary and Module 3's contract are trying to fill, described by people who
solved half of it and said which half.

**Hucka, M., Finney, A., Sauro, H. M., et al. (2003). *The Systems Biology
Markup Language (SBML)*. Bioinformatics 19(4), 524–531.**
<https://doi.org/10.1093/bioinformatics/btg015> — free. Optional, and short.
Reproducibility as a format problem rather than a library problem, from the
canonical case. Lab 4 measured what a format costs in megabytes and seconds; this
is what a format costs when nobody agrees on one.

## The exam question for Module 1

> **A colleague hands you a two-day export from a fleet of sensors and says the
> data is clean. Describe what you would measure before accepting that claim,
> and what each measurement would tell you. Then name one defect that no amount
> of measurement would reveal, and say what would.**

Twenty minutes of the oral covers your mini-project and one published question
per module. This is Module 1's. You are expected to answer it with reference to
what you measured in the labs, not in the abstract.

A strong answer names the five quality dimensions and what each is computed
from — as the ratios and counts on the definition cards; distinguishes a missing
value from a missing *record*; checks that the timestamp is monotone before
computing anything that depends on order; and recognises that the defect
measurement cannot reveal is one where the data is internally consistent and
means something other than its name says — for which the answer is the data
dictionary, obtained from whoever owns the field.

<!-- sync-back-test: edited directly in the module repo, expect a PR on the monorepo -->
