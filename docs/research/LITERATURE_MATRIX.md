# Focused literature comparison

Search date: **29 September 2026**. Status: AI-assisted research preparation,
awaiting a team member's source check. This is a focused scoping comparison, not a
systematic review, an exhaustive patent search or proof of first-ever novelty.

## Main finding

Skill extraction, semantic job matching, assessment-informed recommendations,
knowledge graphs, learning paths and externally sourced jobs already appear in
prior work. R7 describes a particularly close combination of quizzes, learning
roadmaps, project activity and live job retrieval. The proposed study must evaluate
a specific decision policy rather than claim that assembling these features is new.

Our narrower question concerns the consequences of treating **missing assessment
evidence separately from observed errors**, while retaining the source records
behind each recommendation. The search has not established that this distinction
is absent from all earlier systems. It is a candidate contribution to investigate.

## Comparison matrix

“Not established” means the inspected material did not substantiate that point;
it does not mean the authors' system definitely lacks it. Results from different
tasks, datasets and metrics cannot be ranked against our pilot's F1.

| ID / work | Inputs and reported approach | Assessment, learning and uncertainty | Evaluation / reading limits | Consequence for our project |
| --- | --- | --- | --- | --- |
| R1 — Sentence-BERT, Reimers & Gurevych (2019) | Sentence representations for efficient semantic similarity using cosine similarity. | A representation method, not a candidate-testing or roadmap system. | Official abstract and metadata inspected; similarity/transfer benchmarks. | Cite the methodological foundation. A pretrained sentence encoder is not our new algorithm. |
| R2 — SkillSpan, Zhang et al. (2022) | Expert-annotated hard/soft skill spans in job postings, with extraction baselines. | Job text annotation; candidate diagnostic evidence and course decisions are outside the described task. | Official abstract and author dataset description inspected. Span extraction differs from our ten-concept, whole-job labels. | Skill extraction is established. Do not compare its span metrics directly with our job-skill-cell metrics. |
| R3 — Extreme Multi-Label Skill Extraction, Decorte et al. (2023) | Synthetic labelled training examples and contrastive learning link literal/implicit job skills to an ontology. | Training-label generation; independent assessment of candidate proficiency is not established by this source. | Abstract and author benchmark repository inspected; benchmark extraction evaluation reported. | Synthetic training data can be a method, but agreeing with AI-generated evaluation labels does not establish our model's accuracy. |
| R4 — JobEdKG, Fettach et al. (2024) | Job/course information in an uncertain knowledge graph supports skill-demand prediction and course selection. | Uncertainty concerns graph facts; it should not be equated with our skipped-question state. | Publisher-indexed abstract/description and author repository inspected; full publisher text was inaccessible. | External job data, course links and uncertainty already overlap. Candidate-test handling requires full-text verification before an absence claim. |
| R5 — Psychometric course recommender, Pinos Ullauri et al. (2025) | Tutor-assessed soft skills and course histories drive model-based course-set optimisation. | Direct evidence-informed learning recommendations; different skill domain and timescale. | Full Methods and Limitations inspected. Tutor assessments cover three cohorts; the paper discloses that its test subset is also in the training data. | We cannot claim assessment-informed course recommendation is new. Keep our evaluation independent and distinguish predicted benefit from observed learning gains. |
| R6 — CareerPathKG, Le et al. (2026) | Taxonomies, CVs and job descriptions support graph-based matching and career guidance. | “CV assessment” scores document suitability; the inspected method is not a candidate knowledge test. | PDF §§3.2–4 inspected; expert-rated CV/guidance evaluation and retrieval evaluation are reported. | Structured explanations and job-informed career advice overlap. Our evaluation target is a topic-level learning action, not a CV score or job ranking. |
| R7 — GenAI Skill Analyser, Vardhan et al. (2026) | Describes multi-source profiles, adaptive quizzes, staged roadmaps, projects, follow-up tests and Adzuna job retrieval. | Strong feature-level overlap with the original project vision. Treatment of unanswered items as a separate recommendation state is not established in inspected sections. | PDF abstract, implementation and conclusion inspected. The inspected results section gives qualitative claims without a reproducible comparative sample/metric account. Treat reported features separately from demonstrated effectiveness. | Avoid “first platform combining assessment, learning and live jobs.” Cite this overlap and test the narrower policy explicitly. |
| R8 — Multilingual skill matching, Kavas et al. (2025) | Skills from vacancies and candidate experiences are aligned to ESCO and a multilingual knowledge graph. | Candidate experience descriptions provide text evidence; quiz-based proficiency verification is not established in the inspected abstract. | Official abstract and bibliographic record inspected; numerical results/full methods not audited. | ESCO normalisation, embeddings and candidate/job alignment are existing approaches. Our English-only prototype has a much narrower vocabulary. |

## How we searched and screened

Discovery queries included `"skill gap" "course recommendation" paper`,
`"career" "assessment" "learning path" recommender research`,
`"job recommendation" "uncertainty" skills evidence paper`, and exact-title
lookups for SkillSpan, JobEdKG and the assessment/roadmap system. Two search
engines were used, followed by primary publisher, proceedings and author pages.
Some searches expanded the wording; irrelevant results were discarded.

Included: directly overlapping career/learning systems and the extraction/embedding
methods needed to distinguish dependency from contribution. Excluded: generic
career advice, commercial marketing claims used as research results, and reviews
used as substitutes for inspecting primary work. Search coverage is incomplete,
especially for paywalled works, products and non-English research.

This matrix is not a head-to-head benchmark. R1–R3 concern methods/data; R4–R8
concern adjacent or overlapping systems. The proposed simple study baselines are
researcher-defined controls, not reproductions of these papers.

## Sources and inspection notes

- **R1** [Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks](https://aclanthology.org/D19-1410/), EMNLP-IJCNLP 2019, DOI `10.18653/v1/D19-1410`.
- **R2** [SkillSpan: Hard and Soft Skill Extraction from English Job Postings](https://aclanthology.org/2022.naacl-main.366/), NAACL 2022, DOI `10.18653/v1/2022.naacl-main.366`; [author repository](https://github.com/kris927b/SkillSpan).
- **R3** [Extreme Multi-Label Skill Extraction Training using Large Language Models](https://arxiv.org/abs/2307.10778), 2023; [author benchmark repository](https://github.com/jensjorisdecorte/Skill-Extraction-benchmark). Repository distinguishes TECH/HOUSE span labels from TECHWOLF sentence labels and specifies ESCO 1.1.0.
- **R4** [JobEdKG](https://doi.org/10.1016/j.engappai.2023.107779), *Engineering Applications of Artificial Intelligence* 131, article 107779, 2024; [author repository](https://github.com/BahajAdil/JobEd). Publication year is 2024 despite the DOI containing 2023.
- **R5** [A Recommender System of Postgraduate Courses Based on Soft Skills: A Psychometric-inspired Approach](https://link.springer.com/article/10.1007/s40593-025-00463-z), *International Journal of Artificial Intelligence in Education* 35, 2117–2153, 2025. Inspect Methods → Data / Training and Test sets, and Discussion and Limitations.
- **R6** [CareerPathKG: Knowledge Graph Integrated Framework for Career Intelligence](https://aclanthology.org/2026.eacl-industry.60/), EACL Industry Track 2026, DOI `10.18653/v1/2026.eacl-industry.60`; [PDF](https://aclanthology.org/2026.eacl-industry.60.pdf). PDF and landing-page author order differ; the bibliography here follows the PDF title page.
- **R7** [Publisher record](https://ijcrt.org/viewfull.php?paper=IJCRT2604855) and [paper PDF](https://www.ijcrt.org/papers/IJCRT2604855.pdf), IJCRT 14(4), h311–h321, April 2026. The record title includes “Gap”; the PDF title omits it and lists an additional author, Mrs. Ramana. Bibliography follows the PDF; verify metadata before final submission. Citation acknowledges overlap, not independent verification of its effectiveness or references.
- **R8** [Multilingual Skill Extraction for Job Vacancy–Job Seeker Matching in Knowledge Graphs](https://aclanthology.org/2025.genaik-1.15/), GenAIK 2025, pp. 146–155.

## Team source-check tasks

Check the full text of R3, R4 and R8 before describing what their systems lack.
Confirm R6/R7 bibliography discrepancies. Extend the search specifically for
abstention, missing evidence, diagnostic testing and uncertainty in educational
recommendation. Record contrary findings as well as supporting ones. The existence
of an overlapping prior method would change our positioning, not justify hiding it.
