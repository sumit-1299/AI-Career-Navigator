"""
Practical Skill Assessment & Hands-On Task Engine for AI Career Navigator.
Phase 12 Module 12.3: Practical Skill Assessment & Hands-On Task Engine.

This service provides:
1. An immutable, deterministic task bank mapping practical technical tasks across
   the 10 canonical IT career tracks.
2. Multi-factor deterministic task prioritization integrating:
   - Missing career skills (via student profile or track requirements)
   - Job vacancy missing skills (via Phase 12.2 Live Jobs)
   - Phase 11.1 Explainable Skill ROI
   - Phase 11.2 Portfolio & Capstone Projects
   - Phase 11.3 Academic Benchmarks
   - Phase 11.4 Industry Demand Signals
   - Phase 11.5 Career Trajectory Pathways
   - Phase 11.6 Interview Competencies
3. Deterministic, in-memory evaluation of practical student submissions:
   - Concept Coverage (40%)
   - Requirement Coverage (25%)
   - Evaluation Criteria Coverage (20%)
   - Completeness (10%)
   - Structure (5%)
4. Formative result banding:
   - 85-100: STRONG_PRACTICAL_MASTERY
   - 70-84:  PRACTICE_READY
   - 55-69:  NEEDS_REINFORCEMENT
   - 0-54:   FOUNDATION_REQUIRED
5. Temporary skill evidence synthesis with remaining gaps and recommended next tasks.

SAFETY & DESIGN GUARANTEES:
- Strictly in-memory evaluation. ZERO database writes, ZERO schema mutations.
- No code execution, no eval(), no subprocess calls.
- Strictly non-predictive educational assessment disclaimer.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
import re

from models.career import Career
from models.skill import Skill
from services.skill_roi_service import SkillRoiService
from services.portfolio_project_service import PortfolioProjectService
from services.academic_benchmark_service import AcademicBenchmarkService
from services.industry_demand_service import IndustryDemandService
from services.career_trajectory_service import CareerTrajectoryService
from services.live_jobs_service import LiveJobsService
from utils.normalization import normalize_skill_name


class PracticalTaskService:
    """
    Deterministic practical assessment and hands-on task engine.
    """

    SAFETY_DISCLAIMER = (
        "Practical task scores are deterministic educational assessment signals "
        "and do not represent employment probability, interview probability, "
        "or guaranteed job readiness."
    )

    MAX_ANSWER_LENGTH = 25000  # Characters

    # Result bands
    BAND_STRONG_MASTERY = "STRONG_PRACTICAL_MASTERY"
    BAND_PRACTICE_READY = "PRACTICE_READY"
    BAND_NEEDS_REINFORCEMENT = "NEEDS_REINFORCEMENT"
    BAND_FOUNDATION_REQUIRED = "FOUNDATION_REQUIRED"

    # Evidence strength
    EVIDENCE_STRONG = "STRONG"
    EVIDENCE_MODERATE = "MODERATE"
    EVIDENCE_LIMITED = "LIMITED"
    EVIDENCE_INSUFFICIENT = "INSUFFICIENT"

    # Canonical 30-task practical task bank across the 10 careers
    TASK_BANK: List[Dict[str, Any]] = [
        # =====================================================================
        # Career 1: Software Developer (id=1)
        # =====================================================================
        {
            "id": "pt-sd-01",
            "title": "Input Validation & Error Handling for REST Endpoints",
            "career_id": 1,
            "career_title": "Software Developer",
            "skill": "Python",
            "category": "API_DEVELOPMENT",
            "difficulty": "BEGINNER",
            "estimated_minutes": 20,
            "scenario": (
                "You are developing a user registration API endpoint. Untrusted JSON payloads "
                "often contain missing attributes, invalid email formats, or SQL injection vectors."
            ),
            "objective": "Design an input validation and error handling routine for incoming payload fields.",
            "requirements": [
                "Validate that required fields ('email', 'username', 'age') exist in payload",
                "Ensure age is a positive integer and email follows a valid format",
                "Return HTTP 400 with a structured error response specifying missing or invalid fields",
                "Sanitize strings against injection and disallow unexpected extra fields"
            ],
            "expected_concepts": [
                "validation", "type checking", "http 400", "error response", "sanitization"
            ],
            "evaluation_criteria": [
                "Provides structured error format with field-level details",
                "Handles boundary cases such as non-numeric age or empty strings",
                "Separates validation logic from core business logic"
            ],
            "hints": [
                "Consider defining a schema or validator dictionary mapping fields to type checkers.",
                "Return a unified JSON structure like {'errors': [{'field': 'email', 'message': '...'}]}."
            ],
            "expected_outcome": "A robust validation function returning clean HTTP status codes and structured field errors.",
            "learning_objective": "Master defensive API input validation and uniform error reporting in backend services.",
            "portfolio_relevance": "Directly enhances robustness in backend REST API capstone projects.",
            "interview_relevance": "Frequently assessed in backend coding interviews to evaluate defensive programming."
        },
        {
            "id": "pt-sd-02",
            "title": "Debug Thread-Unsafe In-Memory Cache",
            "career_id": 1,
            "career_title": "Software Developer",
            "skill": "Java",
            "category": "DEBUGGING",
            "difficulty": "INTERMEDIATE",
            "estimated_minutes": 30,
            "scenario": (
                "A shared in-memory LRU cache in a multi-threaded service intermittently corrupts keys "
                "or throws ConcurrentModificationException during peak traffic spikes."
            ),
            "objective": "Diagnose the concurrency flaw and propose a thread-safe synchronization strategy.",
            "requirements": [
                "Identify the race condition during concurrent read-modify-write cache operations",
                "Explain why non-thread-safe collections fail under concurrent thread interleaving",
                "Implement synchronization or use thread-safe concurrency primitives (ConcurrentHashMap, ReentrantReadWriteLock)",
                "Ensure cache eviction maintains O(1) complexity without deadlock"
            ],
            "expected_concepts": [
                "race condition", "synchronization", "concurrency", "thread safety", "atomic", "locks"
            ],
            "evaluation_criteria": [
                "Correctly pinpoints shared mutable state without synchronization",
                "Balances thread safety with read throughput using fine-grained locks or concurrent collections",
                "Addresses memory visibility and volatile semantics"
            ],
            "hints": [
                "ReentrantReadWriteLock allows multiple concurrent readers while serializing writers.",
                "Atomic primitives or ConcurrentHashMap.computeIfAbsent avoid manual block synchronization."
            ],
            "expected_outcome": "A synchronized cache architecture that preserves thread safety without deadlocks.",
            "learning_objective": "Understand multi-threaded shared state synchronization and lock contention.",
            "portfolio_relevance": "Crucial for high-throughput distributed caching capstones.",
            "interview_relevance": "Core topic in senior software engineering systems and concurrency interviews."
        },
        {
            "id": "pt-sd-03",
            "title": "Design Scalable Cursor-Based Paginated Feed",
            "career_id": 1,
            "career_title": "Software Developer",
            "skill": "Data Structures",
            "category": "SYSTEM_DESIGN",
            "difficulty": "ADVANCED",
            "estimated_minutes": 45,
            "scenario": (
                "An activity feed endpoint using traditional SQL 'OFFSET' degrades from 5ms to 3200ms "
                "as page depth reaches 50,000 items due to deep sequential B-tree scanning."
            ),
            "objective": "Design an efficient cursor-based (keyset) pagination architecture.",
            "requirements": [
                "Explain the O(N) performance degradation of OFFSET / LIMIT queries at high offsets",
                "Formulate a deterministic cursor encoding (e.g., base64 encoded created_at + item_id)",
                "Construct the indexed SQL query leveraging composite indexes (created_at DESC, id DESC)",
                "Handle edge cases such as newly inserted records and identical timestamps"
            ],
            "expected_concepts": [
                "cursor pagination", "offset", "indexing", "b-tree", "latency", "limit"
            ],
            "evaluation_criteria": [
                "Contrasts offset-based vs keyset pagination mechanics",
                "Ensures tie-breaking via unique identifier to prevent missing items",
                "Details index utilization to achieve constant O(1) page lookup time"
            ],
            "hints": [
                "A cursor pointing to the last evaluated item allows WHERE (created_at, id) < (last_time, last_id).",
                "Ensure the composite database index matches the exact ORDER BY direction."
            ],
            "expected_outcome": "An efficient cursor pagination protocol capable of sub-10ms latency regardless of page depth.",
            "learning_objective": "Architect high-performance database querying and deterministic API pagination.",
            "portfolio_relevance": "Demonstrates production engineering quality in real-world full-stack portfolio apps.",
            "interview_relevance": "Top-tier system design interview topic for backend and platform roles."
        },

        # =====================================================================
        # Career 2: Web Developer (id=2)
        # =====================================================================
        {
            "id": "pt-wd-01",
            "title": "Build Accessible Responsive Form Component",
            "career_id": 2,
            "career_title": "Web Developer",
            "skill": "HTML",
            "category": "CODING",
            "difficulty": "BEGINNER",
            "estimated_minutes": 20,
            "scenario": (
                "A customer intake form fails WCAG 2.1 AA accessibility audits because input fields "
                "lack explicit labels, keyboard focus states are invisible, and mobile viewports cause horizontal overflow."
            ),
            "objective": "Construct semantic, accessible HTML markup with responsive viewport styling.",
            "requirements": [
                "Use semantic HTML elements (<form>, <label>, <input>, <fieldset>, <button>)",
                "Link every input element explicitly to its corresponding label using 'for' and 'id'",
                "Provide ARIA attributes (aria-describedby, aria-invalid) for error announcements",
                "Implement a responsive layout that adapts gracefully from mobile (320px) to desktop without overflow"
            ],
            "expected_concepts": [
                "semantic html", "aria", "label", "validation", "responsive", "media query"
            ],
            "evaluation_criteria": [
                "Strict semantic structure without redundant <div> tag soup",
                "Explicit label association and screen-reader accessibility",
                "Responsive flexbox or grid CSS rules with clear focus indicators"
            ],
            "hints": [
                "Use the 'for' attribute on <label> matching the input's 'id'.",
                "Include 'aria-live' or 'aria-describedby' to inform screen readers of dynamic error messages."
            ],
            "expected_outcome": "A responsive, accessible form component adhering to WCAG AA accessibility standards.",
            "learning_objective": "Master accessible frontend markup and responsive design principles.",
            "portfolio_relevance": "Elevates web application portfolio projects to professional accessibility standards.",
            "interview_relevance": "Standard practical challenge in frontend developer technical evaluations."
        },
        {
            "id": "pt-wd-02",
            "title": "Fix Asynchronous State Desynchronization in React",
            "career_id": 2,
            "career_title": "Web Developer",
            "skill": "React",
            "category": "DEBUGGING",
            "difficulty": "INTERMEDIATE",
            "estimated_minutes": 25,
            "scenario": (
                "A search autocomplete component triggers fast keystroke requests. When users type 'cat' "
                "followed by 'dog', the results for 'cat' occasionally resolve AFTER 'dog', displaying obsolete data."
            ),
            "objective": "Eliminate race conditions in React useEffect using AbortController and cleanup functions.",
            "requirements": [
                "Diagnose the asynchronous race condition caused by out-of-order network responses",
                "Implement an AbortController instance to cancel in-flight HTTP requests when dependencies change",
                "Provide a useEffect cleanup function to abort pending fetches on unmount or re-render",
                "Prevent setting state on unmounted components and avoid stale closure traps"
            ],
            "expected_concepts": [
                "useeffect", "state closure", "race condition", "cleanup", "rerender", "dependencies"
            ],
            "evaluation_criteria": [
                "Correctly demonstrates AbortController.abort() inside the useEffect cleanup",
                "Explains why out-of-order network promises overwrite fresh component state",
                "Handles AbortError gracefully without triggering unhandled promise rejections"
            ],
            "hints": [
                "Pass controller.signal to the fetch call, and call controller.abort() in the return callback.",
                "Catch errors and ignore 'AbortError' so intentional cancellations do not flash errors."
            ],
            "expected_outcome": "A clean React hook that guarantees UI consistency by cancelling stale network requests.",
            "learning_objective": "Master React hook lifecycles, effect cleanup, and asynchronous race condition mitigation.",
            "portfolio_relevance": "Demonstrates sophisticated asynchronous state handling in frontend portfolio apps.",
            "interview_relevance": "Extremely frequent senior React interview question on hook mechanics."
        },
        {
            "id": "pt-wd-03",
            "title": "Implement Client-Side Virtualized Infinite Scroll",
            "career_id": 2,
            "career_title": "Web Developer",
            "skill": "JavaScript",
            "category": "CODING",
            "difficulty": "ADVANCED",
            "estimated_minutes": 40,
            "scenario": (
                "Rendering 10,000 product cards in the browser DOM consumes 450MB of RAM and causes "
                "jank (frame drops below 15 FPS) during fast page scrolling."
            ),
            "objective": "Design a virtualized DOM list renderer using IntersectionObserver to only render visible viewport items.",
            "requirements": [
                "Calculate total scrollable container height based on total items and fixed/estimated row height",
                "Determine the visible start and end index slice based on current scrollTop and viewport height",
                "Render only the visible items plus a buffer (overscan) window in the active DOM tree",
                "Position visible items using absolute transforms (translateY) to eliminate DOM layout thrashing"
            ],
            "expected_concepts": [
                "intersection observer", "virtualization", "dom recycling", "debounce", "viewport"
            ],
            "evaluation_criteria": [
                "Accurate calculation of start/end indices and offset translation",
                "Avoids expensive layout recalculations during continuous scroll events",
                "Maintains 60 FPS smooth scrolling performance with thousands of items"
            ],
            "hints": [
                "Math.floor(scrollTop / rowHeight) gives the startIndex.",
                "Use a total phantom container with height = totalCount * rowHeight so the scrollbar remains natural."
            ],
            "expected_outcome": "A high-performance virtualized list maintaining a constant number of DOM nodes (~20) for 10,000 items.",
            "learning_objective": "Master advanced browser rendering performance, DOM virtualization, and memory optimization.",
            "portfolio_relevance": "Top-tier demonstration of frontend performance engineering for senior developer roles.",
            "interview_relevance": "Standard frontend architecture question at leading tech companies."
        },

        # =====================================================================
        # Career 3: Data Analyst (id=3)
        # =====================================================================
        {
            "id": "pt-da-01",
            "title": "Data Cleaning & Missing Value Imputation",
            "career_id": 3,
            "career_title": "Data Analyst",
            "skill": "Python",
            "category": "DATA_ANALYSIS",
            "difficulty": "BEGINNER",
            "estimated_minutes": 20,
            "scenario": (
                "A customer purchase dataset has 12% missing income values, negative transaction amounts, "
                "and inconsistent state abbreviation strings ('NY', 'New York', 'ny')."
            ),
            "objective": "Build a robust data cleaning and validation pipeline in Python.",
            "requirements": [
                "Detect and summarize missing value distributions across columns",
                "Impute numerical missing values using median (to resist outlier skewness) or flag with indicator",
                "Filter or rectify invalid negative transaction amounts",
                "Standardize categorical string representations to canonical codes"
            ],
            "expected_concepts": [
                "imputation", "null values", "mean", "median", "drop", "outliers"
            ],
            "evaluation_criteria": [
                "Justifies median over mean imputation based on skewed financial distributions",
                "Preserves data integrity without dropping excessive rows",
                "Includes validation assertions to verify clean output dataset"
            ],
            "hints": [
                "Use df.fillna() with median or an explicit missing indicator column.",
                "A mapping dictionary or uppercase strip regex cleans state values deterministically."
            ],
            "expected_outcome": "A clean, reproducible data cleaning script that prepares dirty raw data for downstream BI modeling.",
            "learning_objective": "Develop systematic exploratory data audit and defensive data hygiene habits.",
            "portfolio_relevance": "Fundamental prerequisite for all data analytics portfolio projects.",
            "interview_relevance": "Core technical test in entry-level data analyst technical screenings."
        },
        {
            "id": "pt-da-02",
            "title": "Multi-Table Cohort Revenue Calculation in SQL",
            "career_id": 3,
            "career_title": "Data Analyst",
            "skill": "SQL",
            "category": "DATABASE",
            "difficulty": "INTERMEDIATE",
            "estimated_minutes": 30,
            "scenario": (
                "The business operations team needs a monthly cohort analysis tracking customer retention "
                "and cumulative revenue across users' first 6 months following registration."
            ),
            "objective": "Construct an analytical SQL query computing cohort retention and monthly revenue progression.",
            "requirements": [
                "Determine each user's signup cohort month using DATE_TRUNC or DATE_FORMAT",
                "Join users and transactions tables to compute relative month indices (Month 0, Month 1, etc.)",
                "Aggregate distinct active users and total transaction revenue per cohort-month pair",
                "Use window functions or pivoting to display retention rate percentages alongside revenue"
            ],
            "expected_concepts": [
                "window function", "group by", "cohort", "inner join", "aggregate", "datediff"
            ],
            "evaluation_criteria": [
                "Accurate calculation of elapsed month index without date arithmetic off-by-one errors",
                "Correct aggregation of distinct active paying users vs total revenue",
                "Structured presentation suitable for executive reporting"
            ],
            "hints": [
                "Use a Common Table Expression (CTE) to find user first_order_date or registration_date.",
                "Calculate month_number as (YEAR(order) - YEAR(first))*12 + (MONTH(order) - MONTH(first))."
            ],
            "expected_outcome": "An analytical SQL query delivering a complete cohort retention matrix with revenue metrics.",
            "learning_objective": "Master advanced SQL analytical reporting, Common Table Expressions, and cohort analysis.",
            "portfolio_relevance": "Adds high-impact business intelligence deliverables to an analytics portfolio.",
            "interview_relevance": "The single most common advanced SQL question asked in data analyst interviews."
        },
        {
            "id": "pt-da-03",
            "title": "Statistical Outlier Detection & Anomaly Diagnosis",
            "career_id": 3,
            "career_title": "Data Analyst",
            "skill": "Statistics",
            "category": "DATA_ANALYSIS",
            "difficulty": "ADVANCED",
            "estimated_minutes": 35,
            "scenario": (
                "An e-commerce marketplace experiences flash sale spikes and suspect bot orders. "
                "The analytics team needs to distinguish genuine high-value purchases from bot anomalies."
            ),
            "objective": "Formulate a statistical outlier detection strategy combining IQR, Z-score, and domain rules.",
            "requirements": [
                "Calculate parametric metrics (mean, standard deviation, Z-score) and non-parametric metrics (Q1, Q3, IQR)",
                "Identify statistical outliers (values beyond Q3 + 1.5*IQR or |Z| > 3.0)",
                "Explain the limitations of Z-scores on highly skewed, non-normal distributions",
                "Propose diagnostic business checks (checkout speed, IP entropy) before filtering or flagging anomalies"
            ],
            "expected_concepts": [
                "z-score", "interquartile range", "iqr", "distribution", "variance", "standard deviation"
            ],
            "evaluation_criteria": [
                "Recognizes distribution assumptions (normality for Z-score vs distribution-free IQR)",
                "Calculates upper and lower outlier fences accurately",
                "Distinguishes statistical anomalies from fraudulent behavior with domain context"
            ],
            "hints": [
                "IQR = Q3 - Q1. Upper fence = Q3 + 1.5 * IQR.",
                "For skewed log-normal transaction sizes, consider log transformation before parametric analysis."
            ],
            "expected_outcome": "A comprehensive outlier detection methodology with automated flagging and diagnostic recommendations.",
            "learning_objective": "Apply rigorous statistical reasoning to real-world business anomaly detection.",
            "portfolio_relevance": "Provides statistical credibility in analytics case studies and dashboard reports.",
            "interview_relevance": "Evaluates statistical literacy and analytical problem solving in senior analyst interviews."
        },

        # =====================================================================
        # Career 4: Data Scientist (id=4)
        # =====================================================================
        {
            "id": "pt-ds-01",
            "title": "Feature Engineering & Scaling Pipeline",
            "career_id": 4,
            "career_title": "Data Scientist",
            "skill": "Pandas",
            "category": "DATA_ANALYSIS",
            "difficulty": "BEGINNER",
            "estimated_minutes": 25,
            "scenario": (
                "A predictive modeling dataset contains categorical job titles, continuous income with wide variance, "
                "and timestamp columns. You must engineer features without data leakage."
            ),
            "objective": "Construct a clean Scikit-Learn / Pandas feature transformation pipeline.",
            "requirements": [
                "Split dataset into train and test partitions BEFORE applying transformations to prevent leakage",
                "Apply One-Hot Encoding or Target Encoding to low-cardinality categorical variables",
                "Standardize numerical features using StandardScaler or RobustScaler fitted ONLY on training data",
                "Extract cyclical or elapsed temporal features from timestamp columns (hour of day, day of week)"
            ],
            "expected_concepts": [
                "standardization", "normalization", "one-hot encoding", "scaler", "pandas", "data frame"
            ],
            "evaluation_criteria": [
                "Strict isolation of test set to eliminate data leakage",
                "Appropriate scaler choice based on feature distribution and outliers",
                "Clean pipeline or transformation chaining"
            ],
            "hints": [
                "Always call scaler.fit_transform(X_train) and then scaler.transform(X_test).",
                "Use ColumnTransformer to apply different scalers and encoders to numeric and categorical columns."
            ],
            "expected_outcome": "A leakage-free feature engineering pipeline ready for estimator consumption.",
            "learning_objective": "Master production feature preprocessing hygiene and eliminate subtle train-test data leakage.",
            "portfolio_relevance": "Essential foundation for all machine learning and data science portfolio projects.",
            "interview_relevance": "Frequent testing point in machine learning engineering and data science interviews."
        },
        {
            "id": "pt-ds-02",
            "title": "Diagnose & Mitigate Model Overfitting",
            "career_id": 4,
            "career_title": "Data Scientist",
            "skill": "Machine Learning",
            "category": "MACHINE_LEARNING",
            "difficulty": "INTERMEDIATE",
            "estimated_minutes": 30,
            "scenario": (
                "A decision tree model achieves 99.4% accuracy on training data but drops to 61.2% "
                "on cross-validation test folds, demonstrating severe variance and overfitting."
            ),
            "objective": "Diagnose the overfitting mechanism and implement regularization and validation techniques.",
            "requirements": [
                "Analyze the training vs validation error gap to diagnose high variance (overfitting)",
                "Implement K-fold cross-validation to establish reliable generalization bounds",
                "Apply model regularization (L1 Lasso, L2 Ridge, tree max_depth pruning, min_samples_leaf)",
                "Evaluate feature importance to prune redundant or noisy predictor variables"
            ],
            "expected_concepts": [
                "cross validation", "regularization", "l1", "l2", "overfitting", "train test split"
            ],
            "evaluation_criteria": [
                "Clearly explains bias-variance tradeoff dynamics",
                "Applies concrete regularization hyperparameter tuning",
                "Demonstrates reduced generalization gap on held-out validation sets"
            ],
            "hints": [
                "In tree models, limit max_depth or increase min_samples_split.",
                "In linear models, tune alpha or C parameter to penalize large regression weights."
            ],
            "expected_outcome": "A regularized model configuration showing stable generalization across cross-validation splits.",
            "learning_objective": "Master bias-variance tradeoff management, cross-validation, and model regularization.",
            "portfolio_relevance": "Demonstrates scientific rigor and mature evaluation in machine learning capstones.",
            "interview_relevance": "Mandatory foundational concept probed in every data science technical interview."
        },
        {
            "id": "pt-ds-03",
            "title": "Evaluate Imbalanced Classification via PR-AUC",
            "career_id": 4,
            "career_title": "Data Scientist",
            "skill": "Statistics",
            "category": "MACHINE_LEARNING",
            "difficulty": "ADVANCED",
            "estimated_minutes": 35,
            "scenario": (
                "A financial fraud detection model achieves 99.1% accuracy on a dataset where fraud occurs in "
                "0.9% of transactions. A naive dummy model predicting 'never fraud' matches that accuracy."
            ),
            "objective": "Design an evaluation framework for severe class imbalance using Precision-Recall curves and cost matrices.",
            "requirements": [
                "Explain why ROC-AUC and Accuracy provide misleading signals in extreme class imbalance (e.g. <1% positive rate)",
                "Construct and interpret a Precision-Recall (PR) curve and compute PR-AUC (Average Precision)",
                "Formulate a cost-sensitive decision threshold optimization based on False Positive vs False Negative business costs",
                "Recommend resampling strategies (SMOTE, class weighting) or focal loss to improve minority recall"
            ],
            "expected_concepts": [
                "precision", "recall", "f1 score", "roc-auc", "confusion matrix", "class imbalance"
            ],
            "evaluation_criteria": [
                "Details how large true negative counts artificially inflate ROC-AUC specificity",
                "Explicitly ties threshold selection to asymmetric business failure costs",
                "Provides balanced metrics (F-beta, PR-AUC) suited for rare-event detection"
            ],
            "hints": [
                "ROC-AUC's False Positive Rate denominator includes all negatives (huge number), skewing the curve.",
                "Use precision_recall_curve and average_precision_score from sklearn.metrics."
            ],
            "expected_outcome": "A rigorous evaluation report detailing threshold tuning, cost-utility tradeoffs, and PR-AUC validation.",
            "learning_objective": "Master evaluation methodology for highly skewed, rare-event classification problems.",
            "portfolio_relevance": "Separates novice machine learning projects from industry-grade data science work.",
            "interview_relevance": "Key differentiator in machine learning and data science technical case interviews."
        },

        # =====================================================================
        # Career 5: AI/ML Engineer (id=5)
        # =====================================================================
        {
            "id": "pt-ai-01",
            "title": "Build Safe Token Preprocessing Pipeline",
            "career_id": 5,
            "career_title": "AI/ML Engineer",
            "skill": "Python",
            "category": "MACHINE_LEARNING",
            "difficulty": "BEGINNER",
            "estimated_minutes": 20,
            "scenario": (
                "An NLP classifier crashes on batches containing irregular input strings, emojis, "
                "and variable sequence lengths exceeding maximum context window dimensions."
            ),
            "objective": "Build a robust tokenization, truncation, and padding pipeline in Python.",
            "requirements": [
                "Tokenize arbitrary input text while handling special tokens (<pad>, <unk>, <cls>)",
                "Enforce a maximum sequence length via deterministic truncation",
                "Pad shorter sequences uniformly with padding tokens to create rectangular batch tensors",
                "Generate binary attention masks distinguishing valid tokens from padded positions"
            ],
            "expected_concepts": [
                "tokenization", "padding", "truncation", "vocab", "embedding", "preprocessing"
            ],
            "evaluation_criteria": [
                "Generates correct attention masks (1 for actual tokens, 0 for pad tokens)",
                "Handles edge cases like empty strings or out-of-vocabulary inputs",
                "Produces uniform 2D tensor representations suitable for transformer or embedding layers"
            ],
            "hints": [
                "Attention mask is simply [1 if token != PAD_ID else 0 for token in padded_tokens].",
                "Ensure truncation retains essential prefix context or classification tokens."
            ],
            "expected_outcome": "A resilient token preprocessing pipeline producing padded tensors and corresponding attention masks.",
            "learning_objective": "Understand sequence batching mechanics, attention masking, and vocabulary indexing in modern NLP.",
            "portfolio_relevance": "Essential component in LLM fine-tuning, embeddings, and NLP capstone projects.",
            "interview_relevance": "Standard baseline technical check in AI/ML engineering interviews."
        },
        {
            "id": "pt-ai-02",
            "title": "Diagnose Training Loss Spikes & Vanishing Gradients",
            "career_id": 5,
            "career_title": "AI/ML Engineer",
            "skill": "Deep Learning",
            "category": "DEBUGGING",
            "difficulty": "INTERMEDIATE",
            "estimated_minutes": 30,
            "scenario": (
                "During deep network training, loss values abruptly diverge to NaN at epoch 14 after a series "
                "of erratic loss spikes, while earlier layer gradients approach 0.00000."
            ),
            "objective": "Diagnose gradient instability (vanishing/exploding gradients) and implement stabilization strategies.",
            "requirements": [
                "Identify root causes of numerical instability and exploding gradients (large learning rates, unclipped gradients)",
                "Implement Gradient Clipping (norm-based clipping) in the training loop",
                "Incorporate normalization layers (Batch Normalization or Layer Normalization) and residual skip connections",
                "Apply learning rate scheduling (warmup followed by cosine decay) and weight initialization (He/Xavier)"
            ],
            "expected_concepts": [
                "gradient clipping", "learning rate", "batch normalization", "loss explosion", "adam"
            ],
            "evaluation_criteria": [
                "Explains mathematical mechanism of vanishing/exploding gradients across deep layers",
                "Demonstrates practical gradient clipping implementation (e.g. torch.nn.utils.clip_grad_norm_)",
                "Combines learning rate warmup with normalization layers for numerical convergence"
            ],
            "hints": [
                "Clip gradients to a max norm like 1.0 before optimizer.step().",
                "Check for division by zero in custom loss functions or unconstrained exponential operations."
            ],
            "expected_outcome": "A stabilized deep neural network training loop that maintains finite gradients and steady loss reduction.",
            "learning_objective": "Master deep learning optimization mechanics, gradient dynamics, and numerical stability.",
            "portfolio_relevance": "Shows genuine deep learning engineering competency beyond running default scripts.",
            "interview_relevance": "Primary focus of deep learning theory and debugging technical interviews."
        },
        {
            "id": "pt-ai-03",
            "title": "Design Low-Latency Real-Time Model Inference Service",
            "career_id": 5,
            "career_title": "AI/ML Engineer",
            "skill": "TensorFlow",
            "category": "SYSTEM_DESIGN",
            "difficulty": "ADVANCED",
            "estimated_minutes": 45,
            "scenario": (
                "A computer vision model requires 380ms per prediction, but the production SLA mandates "
                "p99 latency below 35ms at 2,000 requests per second."
            ),
            "objective": "Design an optimized inference architecture combining quantization, dynamic batching, and model compilation.",
            "requirements": [
                "Propose model quantization (INT8 post-training quantization or FP16) to reduce model weight footprint and memory bandwidth",
                "Explain model graph compilation (TensorRT or ONNX Runtime) to fuse operator kernels",
                "Architect a dynamic micro-batching mechanism (e.g., Triton Inference Server) balancing batch throughput and latency",
                "Design CPU/GPU memory pinning and asynchronous worker queues to eliminate host-to-device transfer bottlenecks"
            ],
            "expected_concepts": [
                "batching", "quantization", "latency", "gpu memory", "onnx", "throughput"
            ],
            "evaluation_criteria": [
                "Quantifies tradeoff between precision loss (INT8/FP16) and inference speedup",
                "Accurately diagrams dynamic batching queue mechanics with timeout thresholds",
                "Satisfies both latency SLA (sub-35ms) and throughput requirements (2,000 RPS)"
            ],
            "hints": [
                "TensorRT fuses Conv + BatchNorm + ReLU into a single GPU kernel, dramatically lowering kernel launch overhead.",
                "Dynamic batching collects requests over a 2-5ms window to maximize GPU tensor core utilization."
            ],
            "expected_outcome": "A complete real-time inference architecture blueprint achieving a 10x reduction in inference latency.",
            "learning_objective": "Architect high-throughput, low-latency machine learning systems for enterprise deployment.",
            "portfolio_relevance": "Distinguishes high-level research prototypes from production-grade ML engineering systems.",
            "interview_relevance": "Key evaluation topic in senior AI/ML platform and MLOps system design rounds."
        },

        # =====================================================================
        # Career 6: Cloud Engineer (id=6)
        # =====================================================================
        {
            "id": "pt-cl-01",
            "title": "Configure Secure Multi-AZ VPC Architecture",
            "career_id": 6,
            "career_title": "Cloud Engineer",
            "skill": "Networking",
            "category": "CLOUD",
            "difficulty": "BEGINNER",
            "estimated_minutes": 25,
            "scenario": (
                "A company needs to host web servers and databases in the cloud. Public users should reach web servers, "
                "but database instances must never be assigned public IP addresses or be accessible from the internet."
            ),
            "objective": "Design a multi-Availability Zone VPC topology with public and private subnets.",
            "requirements": [
                "Partition a /16 CIDR block into public and private subnets across at least 2 Availability Zones",
                "Attach an Internet Gateway to the VPC and configure public subnet route tables to direct 0.0.0.0/0 to it",
                "Place database nodes in private subnets with routes pointing outbound internet traffic through a NAT Gateway",
                "Define Network ACLs (NACLs) and Security Groups implementing stateful defense-in-depth"
            ],
            "expected_concepts": [
                "vpc", "subnet", "internet gateway", "nat gateway", "route table", "cidr"
            ],
            "evaluation_criteria": [
                "Correct CIDR math without overlapping subnet ranges",
                "Clear separation of public vs private route table associations",
                "Enforces least privilege security groups (e.g. database port 5432 only accessible from web security group)"
            ],
            "hints": [
                "Public subnets require a route table with 0.0.0.0/0 -> igw-xxxx.",
                "Private subnets require 0.0.0.0/0 -> nat-xxxx to allow patch updates without incoming public access."
            ],
            "expected_outcome": "A fault-tolerant, secure Multi-AZ cloud networking architecture with isolated database tiers.",
            "learning_objective": "Master core cloud networking primitives, CIDR allocation, and perimeter security.",
            "portfolio_relevance": "Baseline architecture for all cloud infrastructure and IaC capstone projects.",
            "interview_relevance": "Ubiquitous cloud engineering interview question for AWS, Azure, and GCP roles."
        },
        {
            "id": "pt-cl-02",
            "title": "Design Auto-Scaling Compute Tier with Health Checks",
            "career_id": 6,
            "career_title": "Cloud Engineer",
            "skill": "AWS",
            "category": "CLOUD",
            "difficulty": "INTERMEDIATE",
            "estimated_minutes": 30,
            "scenario": (
                "Traffic to an e-commerce API spikes tenfold during marketing campaigns. Single-instance nodes crash, "
                "causing 502 Bad Gateway errors for shoppers."
            ),
            "objective": "Design an elastic auto-scaling compute architecture behind an Application Load Balancer.",
            "requirements": [
                "Configure an Application Load Balancer (ALB) with HTTPS listener and Target Group health checks",
                "Define an Auto Scaling Group (ASG) with min, max, and desired capacity spanning multiple AZs",
                "Formulate target tracking scaling policies based on metric alarms (e.g. average CPU > 70% or request count per target)",
                "Implement graceful instance termination and lifecycle hooks to drain active connections before instance shutdown"
            ],
            "expected_concepts": [
                "autoscaling group", "load balancer", "target group", "health check", "scale out", "cpu utilization"
            ],
            "evaluation_criteria": [
                "Deep health check endpoint design (e.g. /health verifying DB connectivity vs shallow ping)",
                "Details connection draining (deregistration delay) to prevent dropped inflight transactions",
                "Establishes realistic cooldown periods to prevent rapid scaling oscillation (thrashing)"
            ],
            "hints": [
                "ALB health checks send periodic GET /health requests; failing 3 consecutive checks triggers replacement.",
                "Deregistration delay allows existing in-flight connections 30-60 seconds to finish before terminating."
            ],
            "expected_outcome": "An elastic auto-scaling cloud cluster that automatically scales capacity with zero dropped requests.",
            "learning_objective": "Master cloud elasticity, load balancing, health monitoring, and graceful lifecycle management.",
            "portfolio_relevance": "Demonstrates enterprise-grade resilience in cloud deployment portfolios.",
            "interview_relevance": "Standard scenario-based design challenge in cloud solutions architect interviews."
        },
        {
            "id": "pt-cl-03",
            "title": "Remediate S3 Bucket Data Exfiltration Vulnerability",
            "career_id": 6,
            "career_title": "Cloud Engineer",
            "skill": "Linux",
            "category": "SECURITY",
            "difficulty": "ADVANCED",
            "estimated_minutes": 35,
            "scenario": (
                "A cloud security audit reveals that a production object storage bucket containing customer PII "
                "has public read permissions, lacks server-side encryption, and allows unauthenticated HTTP downloads."
            ),
            "objective": "Formulate and execute a security remediation plan for cloud object storage.",
            "requirements": [
                "Enable 'Block Public Access' at both the bucket and account level immediately",
                "Enforce Server-Side Encryption with Customer Managed KMS Keys (SSE-KMS) and bucket key caching",
                "Attach an IAM bucket policy strictly enforcing TLS (aws:SecureTransport: true) and denying unencrypted PUTs",
                "Configure access logging, CloudTrail data events, and VPC endpoint routing to isolate traffic from the public internet"
            ],
            "expected_concepts": [
                "iam policy", "bucket policy", "encryption", "public access block", "kms", "least privilege"
            ],
            "evaluation_criteria": [
                "Explicit TLS enforcement in bucket policy using aws:SecureTransport Condition",
                "Applies KMS least-privilege key policy to prevent unauthorized cross-account decryption",
                "Validates remediation using CloudTrail audit logs and security posture checks"
            ],
            "hints": [
                "A bucket policy with Effect: Deny and Condition: {Bool: {aws:SecureTransport: false}} blocks insecure HTTP.",
                "Enabling S3 Gateway VPC endpoints ensures internal EC2-to-S3 traffic never traverses the public internet."
            ],
            "expected_outcome": "A hardened cloud storage policy completely preventing public access, enforcing encryption, and auditing reads.",
            "learning_objective": "Master cloud security hardening, encryption key policies, and least-privilege IAM guardrails.",
            "portfolio_relevance": "Highlights security-first mindset essential for senior cloud infrastructure engineers.",
            "interview_relevance": "High-priority security topic in cloud engineering and DevSecOps interviews."
        },

        # =====================================================================
        # Career 7: DevOps Engineer (id=7)
        # =====================================================================
        {
            "id": "pt-do-01",
            "title": "Write Production Multi-Stage Dockerfile",
            "career_id": 7,
            "career_title": "DevOps Engineer",
            "skill": "Docker",
            "category": "DEVOPS",
            "difficulty": "BEGINNER",
            "estimated_minutes": 20,
            "scenario": (
                "A developer's Docker container image for a simple Go/Node service is 1.4GB in size, "
                "runs as root user, and includes build toolchains, compilers, and source code in the production image."
            ),
            "objective": "Rebuild the container image using a secure, lightweight multi-stage Dockerfile.",
            "requirements": [
                "Implement multi-stage build (Stage 1: build/compile environment, Stage 2: minimal runtime)",
                "Use a minimal runtime base image (such as alpine, distroless, or scratch) to reduce image size < 50MB",
                "Create and switch to a non-root user (USER appuser) for runtime security",
                "Optimize Docker layer caching order by copying dependency lockfiles before source code"
            ],
            "expected_concepts": [
                "multi-stage", "layer caching", "non-root user", "alpine", "minimal image", "dockerfile"
            ],
            "evaluation_criteria": [
                "Strict isolation of compiler artifacts from the final production stage",
                "Eliminates root privilege vulnerability in container runtime",
                "Optimizes layer caching to avoid unnecessary package rebuilds on code changes"
            ],
            "hints": [
                "Use 'COPY --from=builder /app/binary /app/binary' in the final stage.",
                "Run 'adduser -D appuser && USER appuser' before CMD/ENTRYPOINT."
            ],
            "expected_outcome": "A minimal, secure multi-stage Dockerfile producing an image under 50MB running as non-root.",
            "learning_objective": "Master container security hardening, multi-stage compilation, and layer cache optimization.",
            "portfolio_relevance": "Demonstrates production DevOps standards in containerized application portfolios.",
            "interview_relevance": "Standard hands-on test in DevOps and platform engineering technical interviews."
        },
        {
            "id": "pt-do-02",
            "title": "Debug Failing CI/CD Pipeline & Flaky Test Runner",
            "career_id": 7,
            "career_title": "DevOps Engineer",
            "skill": "CI/CD",
            "category": "DEBUGGING",
            "difficulty": "INTERMEDIATE",
            "estimated_minutes": 30,
            "scenario": (
                "A GitHub Actions CI/CD pipeline fails intermittently with exit code 137 (OOM killed), "
                "leaks secret credentials in verbose step logs, and takes 28 minutes to execute due to un-cached dependencies."
            ),
            "objective": "Diagnose the CI/CD failures, fix container resource constraints, and optimize build caching.",
            "requirements": [
                "Identify root cause of exit code 137 as container memory exhaustion and increase memory limit or adjust test runner parallel workers",
                "Implement dependency caching (actions/cache for npm/pip/cargo) reducing pipeline runtime from 28m to < 4m",
                "Mask secrets and replace hardcoded environment variables with encrypted repository secrets",
                "Separate test execution into parallel matrix jobs with deterministic failure isolation"
            ],
            "expected_concepts": [
                "exit code", "artifact caching", "environment variable", "isolation", "retry", "pipeline"
            ],
            "evaluation_criteria": [
                "Correctly diagnoses Linux exit code 137 (128 + 9 SIGKILL / Out of Memory)",
                "Implements effective hash-based cache keying for dependencies",
                "Enforces secret masking and prevents credentials from leaking to stdout"
            ],
            "hints": [
                "Exit code 137 indicates the OS OOM killer terminated the process.",
                "Use cache keys like ${{ runner.os }}-build-${{ hashFiles('**/package-lock.json') }}."
            ],
            "expected_outcome": "A resilient, secure CI/CD pipeline with sub-5-minute execution and robust error isolation.",
            "learning_objective": "Diagnose containerized build failures, optimize caching strategies, and secure CI/CD pipelines.",
            "portfolio_relevance": "Adds production-grade automated deployment pipelines to student capstones.",
            "interview_relevance": "Frequent practical debugging scenario in DevOps engineer technical screens."
        },
        {
            "id": "pt-do-03",
            "title": "Design Zero-Downtime Blue-Green Kubernetes Rollout",
            "career_id": 7,
            "career_title": "DevOps Engineer",
            "skill": "Kubernetes",
            "category": "DEVOPS",
            "difficulty": "ADVANCED",
            "estimated_minutes": 45,
            "scenario": (
                "Deploying a major database-connected API update causes 5-minute outages and 500 errors "
                "because new pods accept traffic before database migrations finish or caches warm up."
            ),
            "objective": "Design a zero-downtime deployment strategy in Kubernetes using readiness probes and blue-green routing.",
            "requirements": [
                "Configure readinessProbe and livenessProbe parameters with appropriate initialDelaySeconds and failureThreshold",
                "Define RollingUpdate strategy parameters (maxSurge: 25%, maxUnavailable: 0) to ensure continuous capacity",
                "Implement initContainers to sequence pre-flight database schema migrations before app container start",
                "Architect a Blue-Green deployment or Service selector swap verifying green health before traffic cutover"
            ],
            "expected_concepts": [
                "rolling update", "ingress", "readiness probe", "liveness probe", "service selector", "blue-green"
            ],
            "evaluation_criteria": [
                "Differentiates readinessProbe (traffic routing) from livenessProbe (pod restart)",
                "Uses initContainer to prevent app containers from running on un-migrated schemas",
                "Provides clear rollback mechanism if smoke tests fail on the new release"
            ],
            "hints": [
                "Setting maxUnavailable: 0 ensures Kubernetes never terminates old pods before new ones pass readiness checks.",
                "Readiness probes prevent ingress traffic from routing to unready pods."
            ],
            "expected_outcome": "A zero-downtime Kubernetes deployment manifest blueprint with safe health checks and instant rollback.",
            "learning_objective": "Master advanced Kubernetes deployment patterns, probe lifecycles, and traffic switching.",
            "portfolio_relevance": "Major credential for Kubernetes and cloud-native DevOps career portfolios.",
            "interview_relevance": "Premier topic in senior DevOps and Site Reliability Engineering (SRE) technical interviews."
        },

        # =====================================================================
        # Career 8: Cybersecurity Analyst (id=8)
        # =====================================================================
        {
            "id": "pt-sec-01",
            "title": "Audit & Remediate SQL Injection in Web Form",
            "career_id": 8,
            "career_title": "Cybersecurity Analyst",
            "skill": "Cybersecurity",
            "category": "SECURITY",
            "difficulty": "BEGINNER",
            "estimated_minutes": 20,
            "scenario": (
                "A login verification function constructs SQL queries via string concatenation: "
                "\"SELECT * FROM users WHERE user = '\" + input + \"'\". An attacker bypasses auth using \"' OR '1'='1\"."
            ),
            "objective": "Audit the vulnerability and implement parameterized queries to prevent SQL injection.",
            "requirements": [
                "Explain the mechanics of SQL injection where untrusted input breaks out of the SQL data literal context",
                "Demonstrate how malicious input alters query logic to evaluate to true or extract unauthorized data",
                "Rewrite the vulnerable query using parameterized prepared statements (bind variables)",
                "Establish defensive input validation and least-privilege database user permissions"
            ],
            "expected_concepts": [
                "parameterized query", "sql injection", "prepared statements", "input sanitization", "owasp"
            ],
            "evaluation_criteria": [
                "Clearly explains why string escaping alone is insufficient compared to parameterized queries",
                "Provides correct prepared statement syntax separating query execution plan from parameters",
                "Mentions principle of least privilege for the database application account"
            ],
            "hints": [
                "Prepared statements compile the SQL command structure before binding parameters as literals.",
                "Never use formatted f-strings or string concatenation to build SQL statements."
            ],
            "expected_outcome": "A secure, parameterized implementation that neutralizes SQL injection vulnerabilities completely.",
            "learning_objective": "Understand OWASP Top 10 injection vulnerabilities and defensive secure coding patterns.",
            "portfolio_relevance": "Crucial proof of security-conscious development in software and security portfolios.",
            "interview_relevance": "Fundamental technical check in application security and junior security analyst interviews."
        },
        {
            "id": "pt-sec-02",
            "title": "Investigate Suspicious SIEM Log Brute-Force Activity",
            "career_id": 8,
            "career_title": "Cybersecurity Analyst",
            "skill": "SIEM",
            "category": "SECURITY",
            "difficulty": "INTERMEDIATE",
            "estimated_minutes": 30,
            "scenario": (
                "A Security Operations Center (SOC) SIEM platform triggers an alert: 4,200 failed SSH login attempts "
                "from a single external IP address within 8 minutes, followed by a successful login and sudo escalation."
            ),
            "objective": "Conduct an incident investigation, reconstruct the attack timeline, and propose containment actions.",
            "requirements": [
                "Analyze the authentication logs (Event ID 4625 / auth.log) to identify source IP, targeted accounts, and timestamps",
                "Reconstruct the attack progression: automated credential stuffing/brute force followed by unauthorized access",
                "Identify evidence of privilege escalation (sudo command executions, new user additions)",
                "Propose immediate containment (isolate host, revoke credentials, block IP) and long-term remediation (MFA, SSH key only)"
            ],
            "expected_concepts": [
                "ip address", "failed login", "threshold", "event correlation", "soc alert", "incident response"
            ],
            "evaluation_criteria": [
                "Follows NIST incident response lifecycle (Identification, Containment, Eradication, Recovery)",
                "Correlates disparate log events into a coherent chronological attack narrative",
                "Prioritizes host isolation to prevent lateral movement across the internal network"
            ],
            "hints": [
                "Check for successful login Event ID 4624 / Accepted password immediately after repeated failures.",
                "Containment requires severing network connectivity before collecting volatile memory evidence."
            ],
            "expected_outcome": "A structured incident triage report detailing attacker IOCs, timeline, containment steps, and root-cause fix.",
            "learning_objective": "Master SIEM alert triage, log correlation, and tactical incident response methodology.",
            "portfolio_relevance": "Outstanding evidence of real-world SOC analyst capabilities in a cybersecurity portfolio.",
            "interview_relevance": "Primary scenario-based interview question for SOC Analyst and Incident Responder roles."
        },
        {
            "id": "pt-sec-03",
            "title": "Design Role-Based Access Control (RBAC) Matrix",
            "career_id": 8,
            "career_title": "Cybersecurity Analyst",
            "skill": "Linux",
            "category": "SYSTEM_DESIGN",
            "difficulty": "ADVANCED",
            "estimated_minutes": 35,
            "scenario": (
                "An enterprise healthcare system with doctors, nurses, billing clerks, and external auditors "
                "suffers from privilege creep: 40% of employees possess full database admin rights."
            ),
            "objective": "Design an enterprise Role-Based Access Control (RBAC) matrix enforcing least privilege and separation of duties.",
            "requirements": [
                "Define distinct roles (Doctor, Nurse, Billing, Auditor, Admin) and atomic permissions (Read_Medical, Write_Medical, Read_Billing, etc.)",
                "Enforce the Principle of Least Privilege: users only receive permissions strictly required for their job function",
                "Implement Separation of Duties (e.g. an auditor cannot edit records; billing cannot access medical diagnostic details)",
                "Establish audit logging requirements to record all authorization decisions and administrative privilege grants"
            ],
            "expected_concepts": [
                "least privilege", "role-based access", "rbac", "permissions", "audit trail", "authorization"
            ],
            "evaluation_criteria": [
                "Prevents excessive privilege assignments across roles",
                "Separates authentication (who you are) from authorization (what you can do)",
                "Specifies periodic access review and automated deprovisioning on role changes"
            ],
            "hints": [
                "Create a permissions matrix table mapping Roles on the vertical axis to atomic Capabilities on the horizontal axis.",
                "Separation of duties prevents any single user from initiating and approving sensitive financial or health records."
            ],
            "expected_outcome": "A complete RBAC policy framework and authorization matrix satisfying compliance and security standards.",
            "learning_objective": "Master identity and access management (IAM), RBAC architectures, and compliance governance.",
            "portfolio_relevance": "Demonstrates security architecture and governance competence for senior security analysts.",
            "interview_relevance": "Core question in security architecture and enterprise identity governance interviews."
        },

        # =====================================================================
        # Career 9: Network Engineer (id=9)
        # =====================================================================
        {
            "id": "pt-net-01",
            "title": "Subnet a Class C Network for 4 Department LANs",
            "career_id": 9,
            "career_title": "Network Engineer",
            "skill": "Networking",
            "category": "NETWORKING",
            "difficulty": "BEGINNER",
            "estimated_minutes": 20,
            "scenario": (
                "An office receives a single /24 IPv4 network block: 192.168.10.0/24. "
                "The organization must divide this into 4 separate department subnets supporting up to 50 hosts each."
            ),
            "objective": "Calculate subnet masks, network IDs, usable host ranges, and broadcast addresses.",
            "requirements": [
                "Determine the required subnet prefix length (/26) allowing at least 4 subnets with 62 usable host addresses each",
                "List the subnet mask in dotted-decimal notation (255.255.255.192)",
                "Calculate the network address, first usable IP, last usable IP, and broadcast IP for all 4 subnets",
                "Explain why 2 addresses per subnet (network and broadcast) are reserved and cannot be assigned to hosts"
            ],
            "expected_concepts": [
                "subnet mask", "cidr", "usable hosts", "broadcast address", "network id", "vlsm"
            ],
            "evaluation_criteria": [
                "Accurate binary/decimal subnet boundary calculations without overlapping IP ranges",
                "Correct identification of reserved network and broadcast addresses",
                "Clear documentation of default gateway assignments per department"
            ],
            "hints": [
                "Borrowing 2 bits from the host portion gives 2^2 = 4 subnets. Host bits remaining = 6 (2^6 - 2 = 62 usable hosts).",
                "Prefix is /26 (24 + 2). Block size is 64."
            ],
            "expected_outcome": "A complete subnet allocation table detailing network IDs, usable ranges, and broadcast addresses for all 4 LANs.",
            "learning_objective": "Master IPv4 binary subnetting, CIDR notation, and IP address space management.",
            "portfolio_relevance": "Fundamental technical proof of network engineering literacy in networking portfolios.",
            "interview_relevance": "Universal initial technical test in CCNA and junior network engineering technical rounds."
        },
        {
            "id": "pt-net-02",
            "title": "Diagnose Asymmetric Routing & Packet Loss",
            "career_id": 9,
            "career_title": "Network Engineer",
            "skill": "Routing and Switching",
            "category": "DEBUGGING",
            "difficulty": "INTERMEDIATE",
            "estimated_minutes": 30,
            "scenario": (
                "Users report that SSH connections drop after 30 seconds, while ICMP pings succeed. "
                "Traceroute reveals traffic travels outbound via ISP 1 but return traffic arrives via ISP 2."
            ),
            "objective": "Diagnose asymmetric routing across multi-homed firewalls and formulate a remediation plan.",
            "requirements": [
                "Analyze traceroute and routing tables to identify asymmetric routing across dual WAN paths",
                "Explain why stateful firewalls drop return packets in asymmetric flows (missing TCP SYN state in connection table)",
                "Propose routing solutions (BGP AS-Path prepending, policy-based routing, or source NAT) to enforce symmetric paths",
                "Verify MTU/MSS settings to eliminate fragmentation issues on VPN and tunnel interfaces"
            ],
            "expected_concepts": [
                "traceroute", "ping", "routing table", "default gateway", "asymmetric routing", "mtu"
            ],
            "evaluation_criteria": [
                "Correctly pinpoints stateful firewall connection tracking as the reason TCP drops while ICMP succeeds",
                "Outlines policy-based routing or BGP routing metric adjustments to enforce symmetry",
                "Provides verification commands to confirm bidirectional path symmetry"
            ],
            "hints": [
                "Stateful firewalls expect TCP handshakes on the same interface where outbound SYN was observed.",
                "Policy-based routing (PBR) routes return packets out the interface where traffic arrived."
            ],
            "expected_outcome": "A comprehensive network troubleshooting report identifying the stateful drop cause and restoring symmetric routing.",
            "learning_objective": "Master multi-homed WAN routing, stateful inspection interactions, and path asymmetry troubleshooting.",
            "portfolio_relevance": "Demonstrates advanced routing and enterprise infrastructure troubleshooting skills.",
            "interview_relevance": "Classic enterprise network engineering scenario question asked in mid/senior network interviews."
        },
        {
            "id": "pt-net-03",
            "title": "Configure Stateful Firewall Rules & NAT Traversal",
            "career_id": 9,
            "career_title": "Network Engineer",
            "skill": "Network Security",
            "category": "NETWORKING",
            "difficulty": "ADVANCED",
            "estimated_minutes": 40,
            "scenario": (
                "A corporate branch office needs to permit internal employees to browse the web via NAT, "
                "host a public HTTPS web service on an internal DMZ server, and strictly isolate IoT devices."
            ),
            "objective": "Formulate a firewall security rulebase and Port Address Translation (PAT) policy.",
            "requirements": [
                "Define zone-based security architecture (Trust/LAN, DMZ, Untrust/WAN, IoT)",
                "Configure Source NAT (PAT/Overload) allowing Trust users outbound internet access using a single public IP",
                "Configure Destination NAT (Port Forwarding) mapping public TCP 443 to the internal DMZ web server IP",
                "Construct stateful firewall ACL rules enforcing default-deny and permitting only established return connections"
            ],
            "expected_concepts": [
                "stateful inspection", "access control list", "acl", "nat", "pat", "port forwarding"
            ],
            "evaluation_criteria": [
                "Enforces strict Default-Deny rule at the bottom of the ACL rulebase",
                "Restricts DMZ-to-Trust traffic to eliminate compromise propagation",
                "Accurately configures Destination NAT translation and matching firewall security policy"
            ],
            "hints": [
                "Destination NAT translates public IP -> private IP; the security policy must inspect the pre-NAT or post-NAT IP depending on firewall vendor.",
                "Isolate IoT devices into their own VLAN with zero access to internal LAN subnets."
            ],
            "expected_outcome": "A complete firewall policy rulebase and NAT configuration ensuring perimeter security and zone isolation.",
            "learning_objective": "Master zone-based firewalling, stateful inspection, and NAT/PAT translation architecture.",
            "portfolio_relevance": "Provides tangible network security configuration proof for senior network engineer roles.",
            "interview_relevance": "Critical assessment area in network security and perimeter engineering interviews."
        },

        # =====================================================================
        # Career 10: Database Administrator (id=10)
        # =====================================================================
        {
            "id": "pt-dba-01",
            "title": "Diagnose Slow Query & Create Composite B-Tree Index",
            "career_id": 10,
            "career_title": "Database Administrator",
            "skill": "SQL",
            "category": "DATABASE",
            "difficulty": "BEGINNER",
            "estimated_minutes": 20,
            "scenario": (
                "A query: 'SELECT * FROM orders WHERE customer_id = 4821 AND status = 'PENDING' ORDER BY order_date DESC' "
                "takes 4.8 seconds on a 12-million row table, causing CPU saturation on the primary database."
            ),
            "objective": "Analyze the EXPLAIN execution plan and design an optimal composite index.",
            "requirements": [
                "Interpret the EXPLAIN ANALYZE output identifying sequential table scans (Seq Scan) and high cost",
                "Explain why single-column indexes on customer_id or status alone provide sub-optimal selectivity",
                "Construct the optimal composite index: CREATE INDEX idx_orders_cust_status_date ON orders (customer_id, status, order_date DESC)",
                "Explain the index column ordering rule: equality filters first, followed by range/sorting columns"
            ],
            "expected_concepts": [
                "explain analyze", "sequential scan", "index scan", "composite index", "b-tree", "query plan"
            ],
            "evaluation_criteria": [
                "Correctly orders columns in composite index (equality before sort/range)",
                "Explains why index eliminates both table filter overhead and expensive in-memory sort",
                "Validates performance gain from sequential scan to index scan"
            ],
            "hints": [
                "Equality columns (customer_id, status) must precede sorting columns (order_date) in composite B-tree indexes.",
                "Using EXPLAIN ANALYZE shows actual execution time and rows vs planner estimates."
            ],
            "expected_outcome": "An optimized composite index DDL statement reducing query execution time from 4800ms to < 2ms.",
            "learning_objective": "Master query plan analysis, B-tree composite indexing mechanics, and execution plan optimization.",
            "portfolio_relevance": "Demonstrates measurable database performance optimization in DBA and backend portfolios.",
            "interview_relevance": "The single most common practical DBA interview question asked across all tech companies."
        },
        {
            "id": "pt-dba-02",
            "title": "Resolve Deadlock in Concurrent Financial Transactions",
            "career_id": 10,
            "career_title": "Database Administrator",
            "skill": "PostgreSQL",
            "category": "DATABASE",
            "difficulty": "INTERMEDIATE",
            "estimated_minutes": 30,
            "scenario": (
                "Concurrent fund transfer operations intermittently fail with PostgreSQL error 'deadlock detected': "
                "Transaction A locks Account 1 and waits for Account 2, while Transaction B locks Account 2 and waits for Account 1."
            ),
            "objective": "Diagnose the circular wait condition and implement deterministic lock acquisition ordering.",
            "requirements": [
                "Explain the four conditions required for deadlock (mutual exclusion, hold and wait, no preemption, circular wait)",
                "Identify how arbitrary row locking order produces circular waits between concurrent worker threads",
                "Implement deterministic lock acquisition ordering (e.g. always lock accounts in ascending order by account_id: MIN(id) then MAX(id))",
                "Utilize SELECT ... FOR UPDATE row-level locking with appropriate application retry handling"
            ],
            "expected_concepts": [
                "deadlock", "transaction isolation", "acid", "row lock", "select for update", "rollback"
            ],
            "evaluation_criteria": [
                "Eliminates circular wait by strictly enforcing global resource ordering",
                "Uses SELECT FOR UPDATE to acquire locks explicitly and defensively",
                "Includes exponential backoff application retry logic for transient serialization conflicts"
            ],
            "hints": [
                "If both transactions lock the lower account ID first, the second transaction will queue rather than deadlock.",
                "Always keep transactions as short as possible to minimize lock duration."
            ],
            "expected_outcome": "A deadlock-free transaction execution pattern that completely eliminates circular lock deadlocks.",
            "learning_objective": "Master ACID transaction isolation, row-level locking mechanisms, and deadlock elimination.",
            "portfolio_relevance": "Proves deep relational database reliability and concurrency mastery.",
            "interview_relevance": "Top-tier database engineering and backend systems interview question."
        },
        {
            "id": "pt-dba-03",
            "title": "Design Point-in-Time Recovery (PITR) Backup Strategy",
            "career_id": 10,
            "career_title": "Database Administrator",
            "skill": "Database Security",
            "category": "SYSTEM_DESIGN",
            "difficulty": "ADVANCED",
            "estimated_minutes": 40,
            "scenario": (
                "A catastrophic accidental 'DROP TABLE users CASCADE' runs at 14:23:18 UTC. "
                "The business requires restoring the database to exactly 14:23:17 UTC with zero data loss prior to the drop."
            ),
            "objective": "Architect a Point-in-Time Recovery (PITR) strategy combining base backups and Write-Ahead Log (WAL) archiving.",
            "requirements": [
                "Explain the mechanics of Write-Ahead Logging (WAL) and how continuous WAL archiving complements base backups",
                "Formulate backup schedules satisfying business RPO (Recovery Point Objective < 1 minute) and RTO (Recovery Time Objective < 30 minutes)",
                "Document the step-by-step restoration workflow (restore base backup, configure recovery.signal, set recovery_target_time)",
                "Verify database consistency upon replay completion and validate against split-brain scenarios"
            ],
            "expected_concepts": [
                "wal archiving", "write-ahead log", "base backup", "pitr", "rpo", "rto"
            ],
            "evaluation_criteria": [
                "Accurate recovery.signal and recovery_target_time configuration",
                "Distinguishes physical WAL archiving from logical pg_dump backups",
                "Establishes automated backup verification testing procedures"
            ],
            "hints": [
                "Base backup + continuous WAL replay allows rolling forward to any arbitrary second.",
                "Setting recovery_target_action = 'pause' allows DBAs to inspect the database before promoting to primary."
            ],
            "expected_outcome": "A comprehensive enterprise Point-in-Time Recovery blueprint capable of sub-second restore precision.",
            "learning_objective": "Master mission-critical database disaster recovery, WAL architecture, and enterprise RPO/RTO planning.",
            "portfolio_relevance": "Cornerstone demonstration of production enterprise database administration capabilities.",
            "interview_relevance": "Key senior DBA technical architecture and disaster recovery evaluation question."
        }
    ]

    # Index tasks by ID for fast O(1) retrieval
    _TASK_MAP: Dict[str, Dict[str, Any]] = {t["id"]: t for t in TASK_BANK}

    # =========================================================================
    # Task Retrieval & Multi-Factor Deterministic Prioritization
    # =========================================================================

    @classmethod
    def get_task_by_id(cls, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific practical task by its unique ID."""
        task = cls._TASK_MAP.get(str(task_id).strip())
        return dict(task) if task else None

    @classmethod
    def list_tasks(
        cls,
        career_id: Optional[int] = None,
        difficulty: Optional[str] = None,
        skill: Optional[str] = None,
        category: Optional[str] = None,
        job_source: Optional[str] = None,
        job_id: Optional[str] = None,
        user_id: Optional[int] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Retrieves practical tasks with deterministic filtering and multi-factor prioritization.
        Integrates:
        1. Missing career skills for candidate
        2. Job vacancy missing skills (if job_source and job_id provided)
        3. Phase 11.1 Skill ROI ranking
        4. Phase 11.2 Portfolio capstone skills
        5. Phase 11.3 Academic deficit skills
        6. Phase 11.4 High industry demand skills
        7. Phase 11.5 Trajectory bridge skills
        """
        # 1. Filter tasks by explicit criteria
        candidates: List[Dict[str, Any]] = list(cls.TASK_BANK)

        if career_id:
            try:
                cid = int(career_id)
                candidates = [t for t in candidates if t["career_id"] == cid]
            except (ValueError, TypeError):
                pass

        if difficulty:
            diff_norm = str(difficulty).strip().upper()
            candidates = [t for t in candidates if t["difficulty"].upper() == diff_norm]

        if skill:
            skill_norm = normalize_skill_name(skill)
            candidates = [
                t for t in candidates
                if normalize_skill_name(t["skill"]) == skill_norm
            ]

        if category:
            cat_norm = str(category).strip().upper()
            candidates = [t for t in candidates if t["category"].upper() == cat_norm]

        # 2. Gather context signals for deterministic prioritization
        user_skills_set: Set[str] = set()
        if user_id:
            try:
                user_records = Skill.query.filter_by(user_id=int(user_id)).all()
                for rec in user_records:
                    if rec.skill_name:
                        user_skills_set.add(normalize_skill_name(rec.skill_name))
            except Exception:
                pass

        job_missing_skills: Set[str] = set()
        if job_source and job_id:
            try:
                job_record = LiveJobsService.get_job(job_source, job_id)
                if job_record and job_record.get("job"):
                    match_res = LiveJobsService.match_job_to_skills(
                        job_record["job"], list(user_skills_set)
                    )
                    for s in match_res.get("missing_skills", []):
                        job_missing_skills.add(normalize_skill_name(s))
            except Exception:
                pass

        # Skill ROI weights (Phase 11.1)
        roi_high_skills: Set[str] = set()
        roi_quick_wins: Set[str] = set()
        if career_id:
            try:
                roi_data = SkillRoiService.rank_career_skill_rois(
                    career_id=int(career_id), user_id=user_id
                )
                if isinstance(roi_data, dict) and "ranked_skills" in roi_data:
                    for item in roi_data["ranked_skills"]:
                        s_norm = normalize_skill_name(item.get("skill_name", ""))
                        if item.get("is_quickest_win"):
                            roi_quick_wins.add(s_norm)
                        elif item.get("roi_tier") in ("HIGH", "QUICKEST_WIN"):
                            roi_high_skills.add(s_norm)
            except Exception:
                pass

        # Portfolio demonstrated skills (Phase 11.2)
        portfolio_skills: Set[str] = set()
        if career_id:
            try:
                port_data = PortfolioProjectService.recommend_projects_for_career(
                    career_id=int(career_id), user_id=user_id, limit=3
                )
                if isinstance(port_data, dict) and "recommendations" in port_data:
                    for p in port_data["recommendations"]:
                        for s in p.get("demonstrated_skills", []):
                            portfolio_skills.add(normalize_skill_name(s))
            except Exception:
                pass

        # Academic deficit skills (Phase 11.3)
        academic_deficits: Set[str] = set()
        if career_id:
            try:
                acad_data = AcademicBenchmarkService.benchmark_academic_readiness(
                    career_id=int(career_id), user_id=user_id
                )
                if isinstance(acad_data, dict) and "skills" in acad_data:
                    for item in acad_data["skills"]:
                        if item.get("status") == "DEFICIT":
                            academic_deficits.add(normalize_skill_name(item.get("skill_name", "")))
            except Exception:
                pass

        # Industry high-demand skills (Phase 11.4)
        industry_high_demand: Set[str] = set()
        if career_id:
            try:
                ind_data = IndustryDemandService.evaluate_career_industry_demand(
                    career_id=int(career_id), user_id=user_id
                )
                if isinstance(ind_data, dict) and "skills" in ind_data:
                    for item in ind_data["skills"]:
                        if item.get("demand_level") in ("VERY_HIGH", "HIGH"):
                            industry_high_demand.add(normalize_skill_name(item.get("skill_name", "")))
            except Exception:
                pass

        # 3. Calculate priority score for each task
        def calculate_task_priority(task: Dict[str, Any]) -> float:
            score = 50.0
            task_skill_norm = normalize_skill_name(task["skill"])

            # Signal 1: Missing from candidate profile (+25)
            if user_skills_set and task_skill_norm not in user_skills_set:
                score += 25.0

            # Signal 2: Missing from targeted job vacancy (+35)
            if task_skill_norm in job_missing_skills:
                score += 35.0

            # Signal 3: Skill ROI Quickest Win (+20) or High Tier (+15)
            if task_skill_norm in roi_quick_wins:
                score += 20.0
            elif task_skill_norm in roi_high_skills:
                score += 15.0

            # Signal 4: Academic Deficit (+10)
            if task_skill_norm in academic_deficits:
                score += 10.0

            # Signal 5: Industry High Demand (+10)
            if task_skill_norm in industry_high_demand:
                score += 10.0

            # Signal 6: Portfolio Project Alignment (+10)
            if task_skill_norm in portfolio_skills:
                score += 10.0

            return score

        # Decorate, sort deterministically, and clamp
        scored_tasks = []
        for t in candidates:
            p_score = calculate_task_priority(t)
            t_copy = dict(t)
            t_copy["priority_score"] = round(p_score, 1)
            t_copy["is_job_gap"] = normalize_skill_name(t["skill"]) in job_missing_skills
            t_copy["is_roi_priority"] = (
                normalize_skill_name(t["skill"]) in roi_quick_wins
                or normalize_skill_name(t["skill"]) in roi_high_skills
            )
            scored_tasks.append(t_copy)

        # Deterministic sorting: higher priority first, then id alphabetically
        scored_tasks.sort(key=lambda x: (-x["priority_score"], x["id"]))

        # Limit
        max_limit = max(1, min(limit, 50))
        final_tasks = scored_tasks[:max_limit]

        return {
            "status": "success",
            "total": len(scored_tasks),
            "returned_count": len(final_tasks),
            "tasks": final_tasks,
            "filters_applied": {
                "career_id": career_id,
                "difficulty": difficulty,
                "skill": skill,
                "category": category,
                "job_source": job_source,
                "job_id": job_id,
                "limit": max_limit,
            },
            "disclaimer": cls.SAFETY_DISCLAIMER,
        }

    # =========================================================================
    # Deterministic Evaluation Engine
    # =========================================================================

    @classmethod
    def evaluate_task_attempt(
        cls,
        task_id: str,
        answer: str,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Deterministically evaluates a student's practical task response in memory.
        Calculates:
        - Concept Coverage (40%)
        - Requirement Coverage (25%)
        - Evaluation Criteria Coverage (20%)
        - Completeness (10%)
        - Structure (5%)
        - Practical Score & Band
        - Skill Evidence & Next Task Recommendation
        """
        # 1. Validate task existence
        task = cls.get_task_by_id(task_id)
        if not task:
            return {
                "status": "error",
                "error": "NOT_FOUND",
                "message": f"Practical task '{task_id}' not found",
            }

        # 2. Validate answer input
        if answer is None or not isinstance(answer, str) or not answer.strip():
            return {
                "status": "error",
                "error": "INVALID_INPUT",
                "message": "Answer is required and cannot be empty",
            }

        if len(answer) > cls.MAX_ANSWER_LENGTH:
            return {
                "status": "error",
                "error": "PAYLOAD_TOO_LARGE",
                "message": f"Answer exceeds maximum allowed length of {cls.MAX_ANSWER_LENGTH} characters",
            }

        clean_text = answer.strip()
        normalized_answer = cls._normalize_text(clean_text)

        # 3. Concept Coverage (Weight: 40%)
        expected_concepts = task.get("expected_concepts", [])
        matched_concepts: List[str] = []
        missing_concepts: List[str] = []

        for concept in expected_concepts:
            if cls._matches_concept(concept, normalized_answer):
                matched_concepts.append(concept)
            else:
                missing_concepts.append(concept)

        total_concepts = len(expected_concepts)
        if total_concepts > 0:
            concept_coverage = round((len(matched_concepts) / total_concepts) * 100.0, 1)
        else:
            concept_coverage = 100.0

        # 4. Requirement Coverage (Weight: 25%)
        requirements = task.get("requirements", [])
        matched_reqs: List[str] = []
        missing_reqs: List[str] = []

        for req in requirements:
            if cls._matches_requirement(req, normalized_answer):
                matched_reqs.append(req)
            else:
                missing_reqs.append(req)

        total_reqs = len(requirements)
        if total_reqs > 0:
            requirement_coverage = round((len(matched_reqs) / total_reqs) * 100.0, 1)
        else:
            requirement_coverage = 100.0

        # 5. Evaluation Criteria Coverage (Weight: 20%)
        criteria = task.get("evaluation_criteria", [])
        matched_criteria: List[str] = []
        missing_criteria: List[str] = []

        for crit in criteria:
            if cls._matches_criteria(crit, normalized_answer):
                matched_criteria.append(crit)
            else:
                missing_criteria.append(crit)

        total_crit = len(criteria)
        if total_crit > 0:
            criteria_coverage = round((len(matched_criteria) / total_crit) * 100.0, 1)
        else:
            criteria_coverage = 100.0

        # 6. Completeness (Weight: 10%)
        completeness = cls._score_completeness(clean_text)

        # 7. Structure (Weight: 5%)
        structure = cls._score_structure(clean_text)

        # 8. Practical Score Calculation
        # Formula: 0.40 * Concept + 0.25 * Req + 0.20 * Criteria + 0.10 * Completeness + 0.05 * Structure
        raw_score = (
            (0.40 * concept_coverage)
            + (0.25 * requirement_coverage)
            + (0.20 * criteria_coverage)
            + (0.10 * completeness)
            + (0.05 * structure)
        )
        practical_score = round(max(0.0, min(100.0, raw_score)), 1)

        # 9. Map Result Band
        if practical_score >= 85.0:
            band = cls.BAND_STRONG_MASTERY
            band_label = "Strong Practical Mastery"
            evidence_strength = cls.EVIDENCE_STRONG
        elif practical_score >= 70.0:
            band = cls.BAND_PRACTICE_READY
            band_label = "Practice Ready"
            evidence_strength = cls.EVIDENCE_MODERATE
        elif practical_score >= 55.0:
            band = cls.BAND_NEEDS_REINFORCEMENT
            band_label = "Needs Reinforcement"
            evidence_strength = cls.EVIDENCE_LIMITED
        else:
            band = cls.BAND_FOUNDATION_REQUIRED
            band_label = "Foundation Required"
            evidence_strength = cls.EVIDENCE_INSUFFICIENT

        # 10. Remaining Gaps Synthesis
        remaining_gaps = []
        for c in missing_concepts:
            remaining_gaps.append(f"Reinforce understanding of core concept '{c}'")
        for r in missing_reqs:
            remaining_gaps.append(f"Address requirement: '{r}'")

        # 11. Recommended Next Task
        next_task = cls._recommend_next_task(
            current_task=task,
            practical_score=practical_score,
            missing_concepts=missing_concepts,
        )

        # 12. Synthesize Skill Evidence
        skill_evidence = {
            "demonstrated_skill": task["skill"],
            "practical_score": practical_score,
            "evidence_strength": evidence_strength,
            "assessment_band": band,
            "band_label": band_label,
            "task_id": task["id"],
            "task_title": task["title"],
            "difficulty": task["difficulty"],
            "category": task["category"],
            "is_verified_signal": practical_score >= 70.0,
        }

        return {
            "status": "success",
            "task": {
                "id": task["id"],
                "title": task["title"],
                "career_id": task["career_id"],
                "career_title": task["career_title"],
                "skill": task["skill"],
                "category": task["category"],
                "difficulty": task["difficulty"],
            },
            "evaluation": {
                "concept_coverage": concept_coverage,
                "requirement_coverage": requirement_coverage,
                "criteria_coverage": criteria_coverage,
                "completeness": completeness,
                "structure": structure,
                "practical_score": practical_score,
                "band": band,
                "band_label": band_label,
                "matched_concepts": matched_concepts,
                "missing_concepts": missing_concepts,
                "matched_requirements_count": len(matched_reqs),
                "total_requirements_count": len(requirements),
            },
            "skill_evidence": skill_evidence,
            "remaining_gaps": remaining_gaps,
            "recommended_next_task": next_task,
            "disclaimer": cls.SAFETY_DISCLAIMER,
        }

    # =========================================================================
    # Internal Evaluation Helpers
    # =========================================================================

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Lowercases, strips punctuation, and collapses multiple whitespace."""
        lower = text.lower()
        cleaned = re.sub(r"[^\w\s-]", " ", lower)
        return " ".join(cleaned.split())

    @classmethod
    def _matches_concept(cls, concept: str, normalized_answer: str) -> bool:
        """Determines if an expected concept is addressed in the normalized text."""
        norm_concept = cls._normalize_text(concept)
        if norm_concept in normalized_answer:
            return True

        # Check token set overlap for multi-word concepts
        concept_tokens = norm_concept.split()
        if len(concept_tokens) > 1:
            matched_count = sum(1 for tok in concept_tokens if tok in normalized_answer)
            if matched_count / len(concept_tokens) >= 0.75:
                return True

        return False

    @classmethod
    def _matches_requirement(cls, requirement: str, normalized_answer: str) -> bool:
        """Extracts substantive requirement tokens and checks presence in answer."""
        stopwords = {
            "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with",
            "of", "by", "that", "this", "is", "are", "be", "ensure", "implement",
            "using", "all", "each", "every", "from", "into", "why", "how", "what"
        }
        raw_tokens = [t for t in re.sub(r"[^\w\s]", " ", requirement.lower()).split() if t not in stopwords and len(t) > 2]
        if not raw_tokens:
            return True

        matched = 0
        for t in raw_tokens:
            stem = t[:-1] if t.endswith("s") and len(t) > 4 else t
            if t in normalized_answer or stem in normalized_answer:
                matched += 1

        return (matched / len(raw_tokens)) >= 0.35

    @classmethod
    def _matches_criteria(cls, criterion: str, normalized_answer: str) -> bool:
        """Checks if evaluation criteria keywords are reflected in the response."""
        stopwords = {
            "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with",
            "of", "by", "that", "this", "is", "are", "be", "provides", "ensures",
            "addresses", "correctly", "explains", "demonstrates", "handles", "inside",
            "without", "triggering", "why", "from", "into"
        }
        raw_tokens = [t for t in re.sub(r"[^\w\s]", " ", criterion.lower()).split() if t not in stopwords and len(t) > 2]
        if not raw_tokens:
            return True

        matched = 0
        for t in raw_tokens:
            stem = t[:-1] if t.endswith("s") and len(t) > 4 else t
            if t in normalized_answer or stem in normalized_answer:
                matched += 1

        return (matched / len(raw_tokens)) >= 0.35

    @staticmethod
    def _score_completeness(text: str) -> float:
        """Evaluates response depth based on word count progression (0.0 to 100.0)."""
        words = text.split()
        count = len(words)

        if count < 10:
            return 15.0
        elif count < 25:
            return 40.0
        elif count < 50:
            return 65.0
        elif count < 90:
            return 85.0
        else:
            return 100.0

    @staticmethod
    def _score_structure(text: str) -> float:
        """Detects presence of code blocks, step lists, and technical sectioning (0.0 to 100.0)."""
        score = 40.0

        # Structural signal 1: List markers or numbered steps
        has_lists = bool(re.search(r"(?:^|\n)\s*(?:\d+[\.\)]|[-*•])\s+", text))
        if has_lists:
            score += 25.0

        # Structural signal 2: Code blocks, declarations, SQL or function patterns
        has_code = bool(
            re.search(r"(?:```|def\s+|class\s+|SELECT\s+|function\s+|const\s+|let\s+|\{|\})", text, re.I)
        )
        if has_code:
            score += 25.0

        # Structural signal 3: Headings or section demarcations
        has_headers = bool(re.search(r"(?:^|\n)\s*(?:#{1,4}\s+|Step\s+\d+|Approach:|Solution:|Explanation:)", text, re.I))
        if has_headers:
            score += 10.0

        return min(100.0, score)

    @classmethod
    def _recommend_next_task(
        cls,
        current_task: Dict[str, Any],
        practical_score: float,
        missing_concepts: List[str],
    ) -> Optional[Dict[str, Any]]:
        """
        Recommends a deterministic next task based on the student's performance.
        - High score: step up to higher difficulty or adjacent career skill.
        - Low score: reinforce current skill with foundation/intermediate task.
        """
        cid = current_task["career_id"]
        current_diff = current_task["difficulty"]
        current_id = current_task["id"]

        career_tasks = [t for t in cls.TASK_BANK if t["career_id"] == cid and t["id"] != current_id]

        if practical_score >= 70.0:
            # Look for next difficulty level
            target_diff = "ADVANCED" if current_diff == "INTERMEDIATE" else "INTERMEDIATE"
            matching = [t for t in career_tasks if t["difficulty"] == target_diff]
            if matching:
                chosen = matching[0]
                return {
                    "id": chosen["id"],
                    "title": chosen["title"],
                    "skill": chosen["skill"],
                    "difficulty": chosen["difficulty"],
                    "estimated_minutes": chosen["estimated_minutes"],
                    "recommendation_reason": (
                        f"Great progress on '{current_task['title']}'! "
                        f"Level up with {chosen['difficulty'].lower()} practical task '{chosen['title']}'."
                    ),
                }

        # Reinforce
        reinforce_tasks = [t for t in career_tasks if t["skill"] == current_task["skill"]]
        if not reinforce_tasks:
            reinforce_tasks = [t for t in career_tasks if t["difficulty"] in ("BEGINNER", "INTERMEDIATE")]

        if reinforce_tasks:
            chosen = reinforce_tasks[0]
            return {
                "id": chosen["id"],
                "title": chosen["title"],
                "skill": chosen["skill"],
                "difficulty": chosen["difficulty"],
                "estimated_minutes": chosen["estimated_minutes"],
                "recommendation_reason": (
                    f"To solidify concepts from '{current_task['title']}', "
                    f"we recommend practicing '{chosen['title']}'."
                ),
            }

        return None
