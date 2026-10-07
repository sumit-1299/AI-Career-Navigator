"""
Interview Simulation Service for AI Career Navigator.
Module 11.6: AI Interview Simulation & Career Readiness Assessment.

Provides deterministic, structured interview simulation and career readiness
assessment across 10 standardized career tracks. Evaluates technical knowledge,
conceptual understanding, problem solving, communication structure, and career
competency coverage without external LLM dependencies.
"""

import re
import math
from typing import Dict, List, Any, Optional, Set, Tuple
from extensions import db
from models.career import Career
from models.career_skill import CareerSkill
from models.skill import Skill
from models.canonical_skill import CanonicalSkill
from models.skill_alias import SkillAlias

from services.skill_roi_service import SkillRoiService
from services.portfolio_project_service import PortfolioProjectService
from services.academic_benchmark_service import AcademicBenchmarkService
from services.industry_demand_service import IndustryDemandService
from services.career_trajectory_service import CareerTrajectoryService


# ==============================================================================
# DETERMINISTIC QUESTION BANK (10 Standardized Careers, ~75 Curated Questions)
# ==============================================================================

QUESTION_BANK: List[Dict[str, Any]] = [
    # --------------------------------------------------------------------------
    # Career 1: Software Developer (Python, Java, Data Structures, Git, SQL)
    # --------------------------------------------------------------------------
    {
        "question_id": "sd-tech-01",
        "career_id": 1,
        "career_title": "Software Developer",
        "competency": "Data Structures",
        "category": "TECHNICAL",
        "difficulty": "BEGINNER",
        "question_text": "What is the difference between an Array and a Linked List in memory allocation and lookup time complexity?",
        "expected_concepts": ["contiguous", "pointer", "o(1)", "o(n)", "cache locality", "dynamic sizing"],
        "context_hint": "Explain memory layout, index access time, and insertion/deletion tradeoffs."
    },
    {
        "question_id": "sd-tech-02",
        "career_id": 1,
        "career_title": "Software Developer",
        "competency": "Python",
        "category": "TECHNICAL",
        "difficulty": "INTERMEDIATE",
        "question_text": "How do Python generators differ from regular functions, and how does the yield keyword manage state?",
        "expected_concepts": ["yield", "iterator", "lazy evaluation", "memory efficiency", "state preservation", "generator"],
        "context_hint": "Focus on memory consumption with large datasets and iterator protocols."
    },
    {
        "question_id": "sd-conc-01",
        "career_id": 1,
        "career_title": "Software Developer",
        "competency": "Java",
        "category": "CONCEPTUAL",
        "difficulty": "INTERMEDIATE",
        "question_text": "Explain the four core principles of Object-Oriented Programming (OOP) and give a brief real-world example of Polymorphism.",
        "expected_concepts": ["encapsulation", "inheritance", "polymorphism", "abstraction", "method overriding", "interface"],
        "context_hint": "Define the 4 pillars and describe dynamic method dispatch or overriding."
    },
    {
        "question_id": "sd-tech-03",
        "career_id": 1,
        "career_title": "Software Developer",
        "competency": "Java",
        "category": "TECHNICAL",
        "difficulty": "INTERMEDIATE",
        "question_text": "How does Java memory management work between the Stack and the Heap, and how does Garbage Collection identify unreachable objects?",
        "expected_concepts": ["stack", "heap", "garbage collection", "reference", "mark and sweep", "memory"],
        "context_hint": "Distinguish primitive/reference frame storage on stack vs object instances on heap."
    },
    {
        "question_id": "sd-prob-01",
        "career_id": 1,
        "career_title": "Software Developer",
        "competency": "SQL",
        "category": "PROBLEM_SOLVING",
        "difficulty": "INTERMEDIATE",
        "question_text": "A query joining two large tables is executing very slowly. How would you diagnose the bottleneck and optimize the query?",
        "expected_concepts": ["explain analyze", "index", "execution plan", "full table scan", "join condition", "indexing"],
        "context_hint": "Describe diagnostic profiling commands and indexing solutions."
    },
    {
        "question_id": "sd-scen-01",
        "career_id": 1,
        "career_title": "Software Developer",
        "competency": "Git",
        "category": "SCENARIO",
        "difficulty": "BEGINNER",
        "question_text": "Two developers modify the same lines in a shared branch. How do you resolve the resulting merge conflict safely?",
        "expected_concepts": ["merge conflict", "git status", "git diff", "conflict markers", "commit", "test"],
        "context_hint": "Detail identifying markers, resolving differences, testing code, and committing."
    },
    {
        "question_id": "sd-arch-01",
        "career_id": 1,
        "career_title": "Software Developer",
        "competency": "Data Structures",
        "category": "SYSTEM_DESIGN",
        "difficulty": "ADVANCED",
        "question_text": "How would you design an in-memory Least Recently Used (LRU) Cache with O(1) get and put time complexity?",
        "expected_concepts": ["hash map", "doubly linked list", "o(1)", "eviction", "head", "tail"],
        "context_hint": "Describe combining a hash map for lookups with a doubly linked list for eviction order."
    },
    {
        "question_id": "sd-behav-01",
        "career_id": 1,
        "career_title": "Software Developer",
        "competency": "Python",
        "category": "BEHAVIORAL",
        "difficulty": "BEGINNER",
        "question_text": "Describe your approach when receiving critical code review feedback that requires refactoring your feature implementation.",
        "expected_concepts": ["constructive", "collaboration", "code quality", "refactoring", "clarification", "unit tests"],
        "context_hint": "Demonstrate professional communication, receptive mindset, and focus on codebase health."
    },

    # --------------------------------------------------------------------------
    # Career 2: Web Developer (HTML, CSS, JavaScript, React, Git)
    # --------------------------------------------------------------------------
    {
        "question_id": "web-tech-01",
        "career_id": 2,
        "career_title": "Web Developer",
        "competency": "JavaScript",
        "category": "TECHNICAL",
        "difficulty": "INTERMEDIATE",
        "question_text": "Explain how the JavaScript Event Loop handles the call stack, microtask queue, and macrotask queue for asynchronous execution.",
        "expected_concepts": ["call stack", "event loop", "microtask", "promise", "macrotask", "settimeout", "async"],
        "context_hint": "Explain queue priority, Promise resolutions vs timer execution order."
    },
    {
        "question_id": "web-tech-02",
        "career_id": 2,
        "career_title": "Web Developer",
        "competency": "React",
        "category": "TECHNICAL",
        "difficulty": "INTERMEDIATE",
        "question_text": "How does React's Virtual DOM differ from the real DOM, and how does the reconciliation algorithm optimize rendering?",
        "expected_concepts": ["virtual dom", "reconciliation", "diffing", "batching", "re-render", "keys"],
        "context_hint": "Discuss in-memory representation, batch updates, and key props."
    },
    {
        "question_id": "web-conc-01",
        "career_id": 2,
        "career_title": "Web Developer",
        "competency": "HTML",
        "category": "CONCEPTUAL",
        "difficulty": "BEGINNER",
        "question_text": "Why is semantic HTML important for web applications, and how does it impact accessibility (a11y) and SEO?",
        "expected_concepts": ["semantic", "accessibility", "screen reader", "seo", "aria", "structure"],
        "context_hint": "Contrast generic div tags with semantic elements like article, nav, main, header."
    },
    {
        "question_id": "web-conc-02",
        "career_id": 2,
        "career_title": "Web Developer",
        "competency": "CSS",
        "category": "CONCEPTUAL",
        "difficulty": "BEGINNER",
        "question_text": "Compare CSS Flexbox and CSS Grid. When would you choose one layout system over the other?",
        "expected_concepts": ["flexbox", "grid", "one-dimensional", "two-dimensional", "row", "column", "layout"],
        "context_hint": "Distinguish 1D component flows from 2D page layouts."
    },
    {
        "question_id": "web-prob-01",
        "career_id": 2,
        "career_title": "Web Developer",
        "competency": "React",
        "category": "PROBLEM_SOLVING",
        "difficulty": "ADVANCED",
        "question_text": "A React dashboard with frequent state updates suffers from laggy UI rendering. How do you identify bottlenecks and optimize component performance?",
        "expected_concepts": ["usememo", "usecallback", "react.memo", "profiler", "re-rendering", "state localization"],
        "context_hint": "Mention React DevTools profiler, memoization hooks, and state splitting."
    },
    {
        "question_id": "web-scen-01",
        "career_id": 2,
        "career_title": "Web Developer",
        "competency": "Git",
        "category": "SCENARIO",
        "difficulty": "BEGINNER",
        "question_text": "A critical frontend production bug is discovered on the live site. What is your git workflow to patch it without leaking unfinished staging features?",
        "expected_concepts": ["hotfix", "main branch", "tag", "cherry-pick", "pull request", "rebase"],
        "context_hint": "Describe branching off main, applying isolated hotfix, testing, and merging."
    },
    {
        "question_id": "web-behav-01",
        "career_id": 2,
        "career_title": "Web Developer",
        "competency": "JavaScript",
        "category": "BEHAVIORAL",
        "difficulty": "BEGINNER",
        "question_text": "How do you balance adhering strictly to pixel-perfect design specifications with technical constraints or tight deadlines?",
        "expected_concepts": ["communication", "designer", "tradeoff", "compromise", "priority", "accessibility"],
        "context_hint": "Focus on cross-functional alignment, clarifying user impact, and iterative delivery."
    },

    # --------------------------------------------------------------------------
    # Career 3: Data Analyst (Python, SQL, Excel, Statistics, Power BI)
    # --------------------------------------------------------------------------
    {
        "question_id": "da-tech-01",
        "career_id": 3,
        "career_title": "Data Analyst",
        "competency": "SQL",
        "category": "TECHNICAL",
        "difficulty": "INTERMEDIATE",
        "question_text": "Explain the difference between ROW_NUMBER(), RANK(), and DENSE_RANK() window functions in SQL.",
        "expected_concepts": ["window function", "partition by", "order by", "ties", "consecutive", "gap"],
        "context_hint": "Detail how duplicate or tied values are assigned rank numbers."
    },
    {
        "question_id": "da-tech-02",
        "career_id": 3,
        "career_title": "Data Analyst",
        "competency": "Statistics",
        "category": "TECHNICAL",
        "difficulty": "BEGINNER",
        "question_text": "What is the difference between Mean, Median, and Mode, and which measure of central tendency is best for skewed distributions?",
        "expected_concepts": ["mean", "median", "mode", "outlier", "skewed", "central tendency"],
        "context_hint": "Explain susceptibility to outliers and why median resists extreme values."
    },
    {
        "question_id": "da-conc-01",
        "career_id": 3,
        "career_title": "Data Analyst",
        "competency": "Power BI",
        "category": "CONCEPTUAL",
        "difficulty": "INTERMEDIATE",
        "question_text": "What is the difference between a Star Schema and a Snowflake Schema in data modeling for business intelligence dashboards?",
        "expected_concepts": ["star schema", "snowflake schema", "fact table", "dimension table", "normalization", "joins"],
        "context_hint": "Compare join complexity, query performance, and table normalization."
    },
    {
        "question_id": "da-prob-01",
        "career_id": 3,
        "career_title": "Data Analyst",
        "competency": "Python",
        "category": "PROBLEM_SOLVING",
        "difficulty": "INTERMEDIATE",
        "question_text": "You are given a raw dataset containing 20% missing values in key numeric columns. How do you assess, clean, and handle this missing data?",
        "expected_concepts": ["missing values", "imputation", "mean/median", "drop", "distribution", "bias"],
        "context_hint": "Discuss determining missingness mechanism (MCAR vs MNAR) and imputation strategies."
    },
    {
        "question_id": "da-scen-01",
        "career_id": 3,
        "career_title": "Data Analyst",
        "competency": "Excel",
        "category": "SCENARIO",
        "difficulty": "BEGINNER",
        "question_text": "When building financial models in Excel, why is XLOOKUP generally preferred over traditional VLOOKUP, and how do INDEX/MATCH compare?",
        "expected_concepts": ["xlookup", "vlookup", "index match", "left lookup", "exact match", "performance"],
        "context_hint": "Highlight column order independence, error defaults, and resilience to column inserts."
    },
    {
        "question_id": "da-behav-01",
        "career_id": 3,
        "career_title": "Data Analyst",
        "competency": "Statistics",
        "category": "BEHAVIORAL",
        "difficulty": "BEGINNER",
        "question_text": "How do you communicate complex statistical findings or anomalies to non-technical executive stakeholders?",
        "expected_concepts": ["visualization", "business impact", "storytelling", "actionable", "clarity", "context"],
        "context_hint": "Focus on narrative framing, minimizing jargon, and tying metrics to business decisions."
    },

    # --------------------------------------------------------------------------
    # Career 4: Data Scientist (Python, SQL, Statistics, Machine Learning, Pandas)
    # --------------------------------------------------------------------------
    {
        "question_id": "ds-tech-01",
        "career_id": 4,
        "career_title": "Data Scientist",
        "competency": "Machine Learning",
        "category": "TECHNICAL",
        "difficulty": "INTERMEDIATE",
        "question_text": "Explain the Bias-Variance Tradeoff in supervised machine learning. How do overfitting and underfitting relate to this tradeoff?",
        "expected_concepts": ["bias", "variance", "tradeoff", "overfitting", "underfitting", "generalization", "regularization"],
        "context_hint": "Contrast simple vs complex models and error decomposition."
    },
    {
        "question_id": "ds-tech-02",
        "career_id": 4,
        "career_title": "Data Scientist",
        "competency": "Statistics",
        "category": "TECHNICAL",
        "difficulty": "INTERMEDIATE",
        "question_text": "What is a p-value in hypothesis testing, and what does it mean to reject the null hypothesis at an alpha level of 0.05?",
        "expected_concepts": ["p-value", "null hypothesis", "significance level", "type 1 error", "probability", "statistical significance"],
        "context_hint": "Define false positive risk and correct probabilistic interpretation."
    },
    {
        "question_id": "ds-conc-01",
        "career_id": 4,
        "career_title": "Data Scientist",
        "competency": "Pandas",
        "category": "CONCEPTUAL",
        "difficulty": "INTERMEDIATE",
        "question_text": "How does vectorization in Pandas and NumPy achieve superior performance over iterative Python for-loops?",
        "expected_concepts": ["vectorization", "c-level", "simd", "numpy array", "overhead", "contiguous memory"],
        "context_hint": "Explain low-level C implementations, memory layout, and avoiding Python interpreter overhead."
    },
    {
        "question_id": "ds-prob-01",
        "career_id": 4,
        "career_title": "Data Scientist",
        "competency": "Machine Learning",
        "category": "PROBLEM_SOLVING",
        "difficulty": "ADVANCED",
        "question_text": "You are training a fraud detection classifier where only 0.2% of transactions are fraudulent. Why is accuracy a misleading metric, and how do you evaluate model performance?",
        "expected_concepts": ["class imbalance", "precision", "recall", "f1-score", "auc-roc", "confusion matrix", "pr-curve"],
        "context_hint": "Explain accuracy paradox and prioritize precision-recall curves for minority classes."
    },
    {
        "question_id": "ds-scen-01",
        "career_id": 4,
        "career_title": "Data Scientist",
        "competency": "SQL",
        "category": "SCENARIO",
        "difficulty": "INTERMEDIATE",
        "question_text": "How do you extract 30-day rolling customer retention cohorts from transactional databases using SQL?",
        "expected_concepts": ["cohort", "date_trunc", "first_purchase", "retention", "join", "group by"],
        "context_hint": "Outline user cohort tagging, timeline normalization, and repeat activity joins."
    },
    {
        "question_id": "ds-behav-01",
        "career_id": 4,
        "career_title": "Data Scientist",
        "competency": "Python",
        "category": "BEHAVIORAL",
        "difficulty": "BEGINNER",
        "question_text": "Tell me about a time a model experiment failed to yield expected results. How did you diagnose the root cause and pivot?",
        "expected_concepts": ["experimentation", "hypothesis", "feature engineering", "data leakage", "iteration", "learning"],
        "context_hint": "Demonstrate analytical rigor, debugging methodology, and constructive iteration."
    },

    # --------------------------------------------------------------------------
    # Career 5: AI/ML Engineer (Python, Machine Learning, Deep Learning, TensorFlow, Statistics)
    # --------------------------------------------------------------------------
    {
        "question_id": "aiml-tech-01",
        "career_id": 5,
        "career_title": "AI/ML Engineer",
        "competency": "Deep Learning",
        "category": "TECHNICAL",
        "difficulty": "INTERMEDIATE",
        "question_text": "Explain backpropagation and gradient descent in neural networks. How do vanishing and exploding gradients occur?",
        "expected_concepts": ["backpropagation", "gradient descent", "chain rule", "vanishing gradient", "activation function", "weights"],
        "context_hint": "Discuss partial derivatives, chain rule through deep layers, and saturating activation functions."
    },
    {
        "question_id": "aiml-tech-02",
        "career_id": 5,
        "career_title": "AI/ML Engineer",
        "competency": "TensorFlow",
        "category": "TECHNICAL",
        "difficulty": "INTERMEDIATE",
        "question_text": "How does TensorFlow's Computational Graph (tf.function) optimize execution speed compared to eager execution?",
        "expected_concepts": ["computational graph", "tf.function", "eager execution", "compilation", "xla", "gpu optimization"],
        "context_hint": "Discuss graph tracing, kernel fusion, and hardware device acceleration."
    },
    {
        "question_id": "aiml-conc-01",
        "career_id": 5,
        "career_title": "AI/ML Engineer",
        "competency": "Machine Learning",
        "category": "CONCEPTUAL",
        "difficulty": "ADVANCED",
        "question_text": "Explain the Multi-Head Self-Attention mechanism in Transformer architectures. Why does it outperform recurrent models like LSTMs?",
        "expected_concepts": ["attention", "transformer", "query key value", "parallelization", "long-range dependencies", "positional encoding"],
        "context_hint": "Highlight Q/K/V dot products, parallel token processing, and eliminating sequential bottlenecks."
    },
    {
        "question_id": "aiml-prob-01",
        "career_id": 5,
        "career_title": "AI/ML Engineer",
        "competency": "Python",
        "category": "PROBLEM_SOLVING",
        "difficulty": "ADVANCED",
        "question_text": "Your model experiences data drift in production, causing performance degradation over time. How do you detect and mitigate this?",
        "expected_concepts": ["data drift", "concept drift", "monitoring", "ks-test", "retraining", "pipeline"],
        "context_hint": "Detail distribution comparison tests, drift monitoring alarms, and automated retraining triggers."
    },
    {
        "question_id": "aiml-arch-01",
        "career_id": 5,
        "career_title": "AI/ML Engineer",
        "competency": "Deep Learning",
        "category": "SYSTEM_DESIGN",
        "difficulty": "ADVANCED",
        "question_text": "Design a high-throughput, low-latency model inference service capable of handling 5,000 queries per second.",
        "expected_concepts": ["batching", "onnx", "tensorrt", "quantization", "load balancing", "gpu caching", "caching"],
        "context_hint": "Discuss model optimization (quantization, TensorRT), dynamic batching, and horizontal scale."
    },
    {
        "question_id": "aiml-behav-01",
        "career_id": 5,
        "career_title": "AI/ML Engineer",
        "competency": "Statistics",
        "category": "BEHAVIORAL",
        "difficulty": "BEGINNER",
        "question_text": "How do you ensure ethical considerations and mitigate bias when selecting training datasets for AI systems?",
        "expected_concepts": ["bias", "fairness", "representation", "audit", "data curation", "transparency"],
        "context_hint": "Show awareness of demographic representation, algorithmic fairness metrics, and audit practices."
    },

    # --------------------------------------------------------------------------
    # Career 6: Cloud Engineer (Linux, Networking, AWS, Python, Docker)
    # --------------------------------------------------------------------------
    {
        "question_id": "cloud-tech-01",
        "career_id": 6,
        "career_title": "Cloud Engineer",
        "competency": "AWS",
        "category": "TECHNICAL",
        "difficulty": "INTERMEDIATE",
        "question_text": "What is the difference between AWS IAM Roles and IAM Users, and when should you use IAM instance profiles?",
        "expected_concepts": ["iam role", "iam user", "temporary credentials", "sts", "instance profile", "least privilege"],
        "context_hint": "Emphasize security advantages of short-lived credentials over hardcoded secret keys."
    },
    {
        "question_id": "cloud-tech-02",
        "career_id": 6,
        "career_title": "Cloud Engineer",
        "competency": "Docker",
        "category": "TECHNICAL",
        "difficulty": "INTERMEDIATE",
        "question_text": "How do Docker containers achieve isolation on a host system, and what role do Linux cgroups and namespaces play?",
        "expected_concepts": ["cgroups", "namespaces", "isolation", "process", "resource limits", "container"],
        "context_hint": "Explain kernel namespaces for visibility and cgroups for CPU/memory resource throttling."
    },
    {
        "question_id": "cloud-conc-01",
        "career_id": 6,
        "career_title": "Cloud Engineer",
        "competency": "Networking",
        "category": "CONCEPTUAL",
        "difficulty": "INTERMEDIATE",
        "question_text": "Explain the architecture of an AWS Virtual Private Cloud (VPC), including public subnets, private subnets, and NAT Gateways.",
        "expected_concepts": ["vpc", "public subnet", "private subnet", "nat gateway", "internet gateway", "route table", "cidr"],
        "context_hint": "Clarify routing paths for outbound-only internet access from private database subnets."
    },
    {
        "question_id": "cloud-conc-02",
        "career_id": 6,
        "career_title": "Cloud Engineer",
        "competency": "Linux",
        "category": "CONCEPTUAL",
        "difficulty": "BEGINNER",
        "question_text": "What is the difference between horizontal and vertical scaling in cloud architecture, and what are the respective tradeoffs?",
        "expected_concepts": ["horizontal scaling", "vertical scaling", "scale out", "scale up", "high availability", "distributed"],
        "context_hint": "Compare hardware capacity limits vs distributed system complexity."
    },
    {
        "question_id": "cloud-prob-01",
        "career_id": 6,
        "career_title": "Cloud Engineer",
        "competency": "Linux",
        "category": "PROBLEM_SOLVING",
        "difficulty": "INTERMEDIATE",
        "question_text": "A cloud server has high CPU usage and unresponsive services. What Linux diagnostic commands do you use to troubleshoot?",
        "expected_concepts": ["top", "htop", "ps aux", "iostat", "vmstat", "dmesg", "journalctl"],
        "context_hint": "List real-time process monitoring, memory, I/O wait, and log inspection commands."
    },
    {
        "question_id": "cloud-arch-01",
        "career_id": 6,
        "career_title": "Cloud Engineer",
        "competency": "AWS",
        "category": "SYSTEM_DESIGN",
        "difficulty": "ADVANCED",
        "question_text": "Design a resilient, multi-region disaster recovery architecture for a mission-critical web application on AWS.",
        "expected_concepts": ["multi-region", "route 53", "rpo", "rto", "replication", "s3 cross-region", "failover"],
        "context_hint": "Define RTO/RPO targets, DNS health checks, and database replication patterns."
    },
    {
        "question_id": "cloud-behav-01",
        "career_id": 6,
        "career_title": "Cloud Engineer",
        "competency": "Python",
        "category": "BEHAVIORAL",
        "difficulty": "BEGINNER",
        "question_text": "How do you manage cloud operational costs and prevent accidental resource sprawl across development teams?",
        "expected_concepts": ["cost monitoring", "budget alerts", "tagging", "auto-shutdown", "governance", "finops"],
        "context_hint": "Discuss tagging policies, budget alarms, scheduled environments, and FinOps awareness."
    },

    # --------------------------------------------------------------------------
    # Career 7: DevOps Engineer (Linux, Docker, Kubernetes, Git, CI/CD)
    # --------------------------------------------------------------------------
    {
        "question_id": "devops-tech-01",
        "career_id": 7,
        "career_title": "DevOps Engineer",
        "competency": "Kubernetes",
        "category": "TECHNICAL",
        "difficulty": "INTERMEDIATE",
        "question_text": "What is the difference between a Kubernetes Pod, Deployment, and Service? How does kube-proxy handle networking?",
        "expected_concepts": ["pod", "deployment", "service", "replica", "kube-proxy", "clusterip", "load balancing"],
        "context_hint": "Explain controller lifecycle management and stable networking endpoints."
    },
    {
        "question_id": "devops-tech-02",
        "career_id": 7,
        "career_title": "DevOps Engineer",
        "competency": "CI/CD",
        "category": "TECHNICAL",
        "difficulty": "INTERMEDIATE",
        "question_text": "Compare Blue/Green deployment with Canary deployment. How do they minimize downtime and rollback risk?",
        "expected_concepts": ["blue/green", "canary", "zero downtime", "rollback", "traffic shifting", "health check"],
        "context_hint": "Contrast full parallel environment switching with incremental percentage-based traffic routing."
    },
    {
        "question_id": "devops-conc-01",
        "career_id": 7,
        "career_title": "DevOps Engineer",
        "competency": "Docker",
        "category": "CONCEPTUAL",
        "difficulty": "BEGINNER",
        "question_text": "What is a multi-stage Docker build, and why is it essential for production container security and image size optimization?",
        "expected_concepts": ["multi-stage", "builder", "image size", "attack surface", "strip dependencies", "dockerfile"],
        "context_hint": "Highlight separation of build toolchains (compilers, dev deps) from runtime base images."
    },
    {
        "question_id": "devops-prob-01",
        "career_id": 7,
        "career_title": "DevOps Engineer",
        "competency": "Kubernetes",
        "category": "PROBLEM_SOLVING",
        "difficulty": "ADVANCED",
        "question_text": "A Kubernetes pod is stuck in CrashLoopBackOff status. Walk through your step-by-step diagnostic workflow.",
        "expected_concepts": ["kubectl describe", "kubectl logs", "events", "exit code", "liveness probe", "resources", "oomkilled"],
        "context_hint": "Describe inspecting pod events, prior container logs, OOM kills, and failing health probes."
    },
    {
        "question_id": "devops-scen-01",
        "career_id": 7,
        "career_title": "DevOps Engineer",
        "competency": "CI/CD",
        "category": "SCENARIO",
        "difficulty": "INTERMEDIATE",
        "question_text": "How do you implement GitOps with tools like ArgoCD or Flux to ensure cluster state matches declarative git repository configuration?",
        "expected_concepts": ["gitops", "declarative", "argocd", "reconciliation", "single source of truth", "drift detection"],
        "context_hint": "Explain continuous sync loops, pull-based cluster agents, and drift mitigation."
    },
    {
        "question_id": "devops-behav-01",
        "career_id": 7,
        "career_title": "DevOps Engineer",
        "competency": "Linux",
        "category": "BEHAVIORAL",
        "difficulty": "BEGINNER",
        "question_text": "Describe how you foster a blameless post-mortem culture after a major production service outage.",
        "expected_concepts": ["blameless", "post-mortem", "root cause", "action items", "systemic improvement", "learning"],
        "context_hint": "Emphasize focusing on systemic resilience, process defects, and prevention rather than individual blame."
    },

    # --------------------------------------------------------------------------
    # Career 8: Cybersecurity Analyst (Linux, Networking, Cybersecurity, Python, SIEM)
    # --------------------------------------------------------------------------
    {
        "question_id": "sec-tech-01",
        "career_id": 8,
        "career_title": "Cybersecurity Analyst",
        "competency": "SIEM",
        "category": "TECHNICAL",
        "difficulty": "INTERMEDIATE",
        "question_text": "How does a Security Information and Event Management (SIEM) system correlate disparate log sources to detect advanced persistent threats?",
        "expected_concepts": ["siem", "correlation", "log ingestion", "rule", "ioc", "alert", "anomaly"],
        "context_hint": "Explain parsing firewall, authentication, and endpoint logs to spot attacker attack chains."
    },
    {
        "question_id": "sec-tech-02",
        "career_id": 8,
        "career_title": "Cybersecurity Analyst",
        "competency": "Cybersecurity",
        "category": "TECHNICAL",
        "difficulty": "INTERMEDIATE",
        "question_text": "Explain the stages of the MITRE ATT&CK framework and how it aids defensive threat hunting.",
        "expected_concepts": ["mitre att&ck", "tactics", "techniques", "threat hunting", "initial access", "lateral movement"],
        "context_hint": "Describe standardized adversary behavioral classification from reconnaissance to exfiltration."
    },
    {
        "question_id": "sec-conc-01",
        "career_id": 8,
        "career_title": "Cybersecurity Analyst",
        "competency": "Networking",
        "category": "CONCEPTUAL",
        "difficulty": "BEGINNER",
        "question_text": "Explain the CIA Triad (Confidentiality, Integrity, Availability) and provide a security control that addresses each pillar.",
        "expected_concepts": ["confidentiality", "integrity", "availability", "encryption", "hashing", "redundancy", "cia"],
        "context_hint": "Pair each principle with controls like AES encryption, SHA hashing, and load-balanced clustering."
    },
    {
        "question_id": "sec-prob-01",
        "career_id": 8,
        "career_title": "Cybersecurity Analyst",
        "competency": "Cybersecurity",
        "category": "PROBLEM_SOLVING",
        "difficulty": "ADVANCED",
        "question_text": "An endpoint alerts for potential ransomware activity. What are your immediate containment, eradication, and forensic response steps?",
        "expected_concepts": ["containment", "isolate", "network isolation", "forensics", "memory dump", "incident response", "backup"],
        "context_hint": "Detail immediate network disconnection, memory/disk artifact capture, and safe recovery."
    },
    {
        "question_id": "sec-scen-01",
        "career_id": 8,
        "career_title": "Cybersecurity Analyst",
        "competency": "Linux",
        "category": "SCENARIO",
        "difficulty": "BEGINNER",
        "question_text": "How would you investigate unauthorized root logins on a Linux server using auditd and auth.log?",
        "expected_concepts": ["auth.log", "auditd", "last", "failed logins", "ssh", "grep", "timestamps"],
        "context_hint": "Discuss analyzing authentication logs, verifying accepted keys, and checking user login history."
    },
    {
        "question_id": "sec-behav-01",
        "career_id": 8,
        "career_title": "Cybersecurity Analyst",
        "competency": "Python",
        "category": "BEHAVIORAL",
        "difficulty": "BEGINNER",
        "question_text": "How do you handle internal resistance when enforcing strict security policies (like mandatory MFA or least privilege) that employees perceive as inconvenient?",
        "expected_concepts": ["education", "security awareness", "empathy", "friction reduction", "business risk", "executive support"],
        "context_hint": "Highlight education on attack risks, user-friendly security tool design, and respectful collaboration."
    },

    # --------------------------------------------------------------------------
    # Career 9: Network Engineer (Networking, Linux, Routing and Switching, CCNA, Network Security)
    # --------------------------------------------------------------------------
    {
        "question_id": "net-tech-01",
        "career_id": 9,
        "career_title": "Network Engineer",
        "competency": "Routing and Switching",
        "category": "TECHNICAL",
        "difficulty": "INTERMEDIATE",
        "question_text": "Compare OSPF (Open Shortest Path First) and BGP (Border Gateway Protocol). In what network topologies is each protocol applied?",
        "expected_concepts": ["ospf", "bgp", "igp", "egp", "link-state", "path vector", "autonomous system", "dijkstra"],
        "context_hint": "Contrast internal enterprise routing (IGP) with inter-domain Internet routing (EGP)."
    },
    {
        "question_id": "net-tech-02",
        "career_id": 9,
        "career_title": "Network Engineer",
        "competency": "Networking",
        "category": "TECHNICAL",
        "difficulty": "BEGINNER",
        "question_text": "Explain the 7 layers of the OSI model, focusing on the differences between Layer 2 (Data Link), Layer 3 (Network), and Layer 4 (Transport).",
        "expected_concepts": ["osi model", "layer 2", "layer 3", "layer 4", "mac address", "ip address", "tcp/udp", "packet", "frame"],
        "context_hint": "Discuss frames/switches at L2, packets/routers at L3, and ports/segments at L4."
    },
    {
        "question_id": "net-conc-01",
        "career_id": 9,
        "career_title": "Network Engineer",
        "competency": "CCNA",
        "category": "CONCEPTUAL",
        "difficulty": "BEGINNER",
        "question_text": "What is the purpose of VLANs (Virtual Local Area Networks) and trunking protocols like 802.1Q?",
        "expected_concepts": ["vlan", "trunking", "802.1q", "broadcast domain", "tagging", "segmentation", "switch"],
        "context_hint": "Explain broadcast domain containment, security segmentation, and VLAN tag encapsulation."
    },
    {
        "question_id": "net-prob-01",
        "career_id": 9,
        "career_title": "Network Engineer",
        "competency": "Network Security",
        "category": "PROBLEM_SOLVING",
        "difficulty": "INTERMEDIATE",
        "question_text": "A branch office experiences packet loss and high latency across an IPsec VPN tunnel. How do you troubleshoot MTU/MSS clamping and routing?",
        "expected_concepts": ["mtu", "mss", "ipsec", "fragmentation", "ping -f", "overhead", "vpn"],
        "context_hint": "Discuss packet fragmentation from encryption headers and tuning MTU/MSS sizes."
    },
    {
        "question_id": "net-scen-01",
        "career_id": 9,
        "career_title": "Network Engineer",
        "competency": "Linux",
        "category": "SCENARIO",
        "difficulty": "BEGINNER",
        "question_text": "What commands and tools on Linux do you use to verify network socket listeners, interface configurations, and packet routes?",
        "expected_concepts": ["ip addr", "ip route", "ss", "netstat", "tcpdump", "traceroute", "ping"],
        "context_hint": "Highlight modern iproute2 suite (ip, ss) and packet capture tools (tcpdump)."
    },
    {
        "question_id": "net-behav-01",
        "career_id": 9,
        "career_title": "Network Engineer",
        "competency": "Networking",
        "category": "BEHAVIORAL",
        "difficulty": "BEGINNER",
        "question_text": "Describe your strategy for planning maintenance windows for core backbone switch firmware upgrades with minimal downtime.",
        "expected_concepts": ["maintenance window", "redundancy", "failover test", "rollback plan", "stakeholder communication"],
        "context_hint": "Emphasize redundant routing verification, off-peak timing, and explicit rollback triggers."
    },

    # --------------------------------------------------------------------------
    # Career 10: Database Administrator (SQL, PostgreSQL, MySQL, Linux, Database Security)
    # --------------------------------------------------------------------------
    {
        "question_id": "dba-tech-01",
        "career_id": 10,
        "career_title": "Database Administrator",
        "competency": "SQL",
        "category": "TECHNICAL",
        "difficulty": "INTERMEDIATE",
        "question_text": "Explain ACID properties in relational database transactions. How do isolation levels prevent dirty reads, non-repeatable reads, and phantom reads?",
        "expected_concepts": ["atomicity", "consistency", "isolation", "durability", "read committed", "repeatable read", "serializable", "acid"],
        "context_hint": "Define each ACID component and describe transactional lock/MVCC concurrency trade-offs."
    },
    {
        "question_id": "dba-tech-02",
        "career_id": 10,
        "career_title": "Database Administrator",
        "competency": "PostgreSQL",
        "category": "TECHNICAL",
        "difficulty": "INTERMEDIATE",
        "question_text": "How does Multi-Version Concurrency Control (MVCC) work in PostgreSQL, and why is VACUUM necessary?",
        "expected_concepts": ["mvcc", "vacuum", "bloat", "dead tuples", "transaction id", "concurrency"],
        "context_hint": "Explain snapshot isolation, non-blocking reads, and dead tuple garbage collection."
    },
    {
        "question_id": "dba-conc-01",
        "career_id": 10,
        "career_title": "Database Administrator",
        "competency": "MySQL",
        "category": "CONCEPTUAL",
        "difficulty": "BEGINNER",
        "question_text": "Compare Clustered Indexes with Secondary (Non-Clustered) Indexes in MySQL InnoDB storage engine.",
        "expected_concepts": ["clustered index", "secondary index", "primary key", "b+ tree", "leaf nodes", "lookup"],
        "context_hint": "Explain that clustered index stores actual table row data at the leaf nodes, while secondary indexes store primary keys."
    },
    {
        "question_id": "dba-prob-01",
        "career_id": 10,
        "career_title": "Database Administrator",
        "competency": "Database Security",
        "category": "PROBLEM_SOLVING",
        "difficulty": "ADVANCED",
        "question_text": "How do you secure a production database server against SQL injection, data exfiltration, and unauthorized access?",
        "expected_concepts": ["parameterized queries", "least privilege", "encryption at rest", "tls/ssl", "network firewall", "audit logging"],
        "context_hint": "Cover prepared statements, dedicated application roles, network restriction, and data encryption."
    },
    {
        "question_id": "dba-scen-01",
        "career_id": 10,
        "career_title": "Database Administrator",
        "competency": "Linux",
        "category": "SCENARIO",
        "difficulty": "INTERMEDIATE",
        "question_text": "A database server is running out of disk space due to unbounded write-ahead logs (WAL). How do you safely resolve and prevent this?",
        "expected_concepts": ["wal", "archive_command", "replication slot", "disk space", "checkpoint", "retention policy"],
        "context_hint": "Investigate stalled replication slots, failed archive commands, and checkpoint tuning."
    },
    {
        "question_id": "dba-behav-01",
        "career_id": 10,
        "career_title": "Database Administrator",
        "competency": "PostgreSQL",
        "category": "BEHAVIORAL",
        "difficulty": "BEGINNER",
        "question_text": "When a developer requests direct production database superuser credentials to debug a live issue, how do you respond?",
        "expected_concepts": ["security compliance", "least privilege", "read-only replica", "sanitized data", "supportive collaboration"],
        "context_hint": "Safely decline superuser access while providing read-only logs, staging reproduction, or paired debugging sessions."
    },
]


# Map question ID for instant O(1) lookup
QUESTION_BY_ID: Dict[str, Dict[str, Any]] = {q["question_id"]: q for q in QUESTION_BANK}


# ==============================================================================
# READINESS BANDS & EVALUATION CONSTANTS
# ==============================================================================

READINESS_BANDS = {
    "INTERVIEW_READY": {
        "min_score": 85,
        "label": "Interview-Ready",
        "summary": "Candidate demonstrates comprehensive technical depth, clear conceptual frameworks, and solid communication structure. Competitive for junior and placement interviews."
    },
    "STRONG_PREPARATION": {
        "min_score": 70,
        "label": "Strong Preparation",
        "summary": "Candidate demonstrates solid foundational knowledge with minor gaps in specific edge cases or advanced technical nuances."
    },
    "NEEDS_PRACTICE": {
        "min_score": 55,
        "label": "Needs Practice",
        "summary": "Candidate understands high-level concepts but needs practical hands-on reinforcement and more structured technical articulation."
    },
    "FOUNDATION_REQUIRED": {
        "min_score": 0,
        "label": "Foundation Required",
        "summary": "Candidate requires substantial study in core career competencies and structured practice before technical interviews."
    }
}


def normalize_skill_name(name: str) -> str:
    """Normalize skill name for matching."""
    if not name:
        return ""
    return re.sub(r"[^a-z0-9]", "", name.lower().strip())


def normalize_text(text: str) -> str:
    """Normalize freeform text for concept parsing."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.lower().strip())


# ==============================================================================
# CORE INTERVIEW SIMULATION SERVICE
# ==============================================================================

class InterviewSimulationService:
    """
    Deterministic AI Interview Simulation and Career Readiness Assessment Engine.
    Evaluates simulated technical interview responses against expected competencies,
    scoring technical knowledge, conceptual understanding, problem solving,
    communication, and career competency coverage.
    """

    @classmethod
    def get_question_bank(
        cls,
        career_id: Optional[int] = None,
        difficulty: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Return questions filtered by career and/or difficulty."""
        res = QUESTION_BANK
        if career_id is not None:
            res = [q for q in res if q["career_id"] == career_id]
        if difficulty and difficulty.upper() != "ALL":
            res = [q for q in res if q["difficulty"].upper() == difficulty.upper()]
        return res

    @classmethod
    def generate_session(
        cls,
        career_id: int,
        difficulty: Optional[str] = "INTERMEDIATE",
        question_count: int = 5,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Deterministically selects a curated set of interview questions for the specified career.
        If user_id is provided, prioritizes questions addressing student skill gaps.
        """
        career = Career.query.get(career_id)
        if not career:
            return {"error": "CAREER_NOT_FOUND", "message": f"Career with id {career_id} not found"}

        # Validate question count
        clamped_count = max(1, min(10, int(question_count or 5)))

        # Candidate pool
        career_questions = [q for q in QUESTION_BANK if q["career_id"] == career_id]
        if not career_questions:
            return {
                "error": "NO_QUESTIONS_FOUND",
                "message": f"No questions mapped for career track '{career.title}'"
            }

        # Normalize difficulty filter
        diff_filter = (difficulty or "ALL").upper()
        if diff_filter != "ALL":
            filtered = [q for q in career_questions if q["difficulty"].upper() == diff_filter]
            if len(filtered) >= clamped_count:
                candidate_pool = filtered
            else:
                candidate_pool = career_questions
        else:
            candidate_pool = career_questions

        # Identify student skill gaps if authenticated
        gap_skills: Set[str] = set()
        is_personalized = False
        if user_id:
            try:
                user_skills = Skill.query.filter_by(user_id=user_id).all()
                user_skill_map = {
                    normalize_skill_name(s.skill_name): int(s.proficiency or 0)
                    for s in user_skills if s.skill_name
                }
                career_reqs = CareerSkill.query.filter_by(career_id=career_id).all()
                for cr in career_reqs:
                    norm_k = normalize_skill_name(cr.skill_name)
                    user_prof = user_skill_map.get(norm_k, 0)
                    if user_prof < cr.required_level:
                        gap_skills.add(norm_k)
                        gap_skills.add(cr.skill_name.lower())
                is_personalized = True
            except Exception:
                pass

        # Deterministic ranking / sorting
        # Prioritize: (1) covers gap competency, (2) difficulty match, (3) category diversity, (4) question_id
        def question_priority(q: Dict[str, Any]) -> Tuple[int, int, str]:
            norm_c = normalize_skill_name(q["competency"])
            is_gap = 1 if (norm_c in gap_skills or q["competency"].lower() in gap_skills) else 0
            diff_match = 1 if (diff_filter != "ALL" and q["difficulty"].upper() == diff_filter) else 0
            return (-is_gap, -diff_match, q["question_id"])

        sorted_pool = sorted(candidate_pool, key=question_priority)

        # Select distinct questions ensuring category balance if possible
        selected_questions: List[Dict[str, Any]] = []
        seen_ids: Set[str] = set()

        for q in sorted_pool:
            if len(selected_questions) >= clamped_count:
                break
            if q["question_id"] not in seen_ids:
                selected_questions.append(q)
                seen_ids.add(q["question_id"])

        # Format questions for client (omit expected_concepts from client payload for security)
        client_questions = []
        for idx, q in enumerate(selected_questions, 1):
            client_questions.append({
                "question_id": q["question_id"],
                "index": idx,
                "competency": q["competency"],
                "category": q["category"],
                "difficulty": q["difficulty"],
                "question_text": q["question_text"],
                "context_hint": q.get("context_hint", ""),
            })

        session_id = f"sim-{career_id}-{clamped_count}-{diff_filter.lower()}"

        return {
            "session_id": session_id,
            "career": {
                "id": career.id,
                "title": career.title,
                "domain": career.domain,
            },
            "difficulty": diff_filter,
            "question_count": len(client_questions),
            "is_personalized": is_personalized,
            "targeted_gap_competencies": sorted(list(gap_skills)),
            "questions": client_questions,
            "instructions": "Answer each question thoroughly using relevant technical terminology, conceptual reasoning, and practical examples.",
            "assessment_disclaimer": "This simulator provides an educational readiness estimate for practice and preparation. It is not an objective psychological assessment or employment guarantee."
        }

    @classmethod
    def evaluate_session(
        cls,
        career_id: int,
        answers: List[Dict[str, Any]],
        difficulty: Optional[str] = "INTERMEDIATE",
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Deterministically evaluates student answers against the career question bank.
        Calculates category scores, overall readiness, feedback, strengths, weaknesses,
        and cross-module integrations (11.1 ROI, 11.2 Portfolio, 11.3 Academic, 11.4 Market, 11.5 Trajectory).
        """
        career = Career.query.get(career_id)
        if not career:
            return {"error": "CAREER_NOT_FOUND", "message": f"Career with id {career_id} not found"}

        if not answers or not isinstance(answers, list):
            return {"error": "INVALID_ANSWERS", "message": "Answers list must be non-empty"}

        # Career required skills
        career_skills = CareerSkill.query.filter_by(career_id=career_id).all()
        required_skill_names = [cs.skill_name for cs in career_skills]
        norm_required_skills = {normalize_skill_name(s): s for s in required_skill_names}

        # Evaluate each question answer
        evaluated_results: List[Dict[str, Any]] = []
        competency_scores: Dict[str, List[float]] = {}
        category_scores_map: Dict[str, List[float]] = {
            "TECHNICAL": [],
            "CONCEPTUAL": [],
            "PROBLEM_SOLVING": [],
            "COMMUNICATION": [],
        }

        for item in answers:
            q_id = item.get("question_id")
            answer_text = item.get("answer", "") or ""

            question_obj = QUESTION_BY_ID.get(q_id)
            if not question_obj:
                # Skip or create generic evaluation if unknown
                continue

            # Evaluate single answer
            eval_res = cls._evaluate_single_answer(question_obj, answer_text)
            evaluated_results.append(eval_res)

            # Bucket scores
            score = eval_res["score"]
            comp_norm = normalize_skill_name(question_obj["competency"])
            if comp_norm not in competency_scores:
                competency_scores[comp_norm] = []
            competency_scores[comp_norm].append(score)

            cat = question_obj.get("category", "TECHNICAL").upper()
            if cat in ("TECHNICAL", "SYSTEM_DESIGN"):
                category_scores_map["TECHNICAL"].append(score)
            elif cat == "CONCEPTUAL":
                category_scores_map["CONCEPTUAL"].append(score)
            elif cat in ("PROBLEM_SOLVING", "SCENARIO"):
                category_scores_map["PROBLEM_SOLVING"].append(score)

            # Structure/communication component
            category_scores_map["COMMUNICATION"].append(eval_res["structure_score"])

        if not evaluated_results:
            return {"error": "NO_VALID_QUESTIONS", "message": "None of the submitted question IDs matched the question bank."}

        # Compute Category Scores
        # 1. Technical Knowledge
        tech_list = category_scores_map["TECHNICAL"]
        technical_score = round(sum(tech_list) / len(tech_list), 1) if tech_list else 70.0

        # 2. Conceptual Understanding
        conc_list = category_scores_map["CONCEPTUAL"]
        conceptual_score = round(sum(conc_list) / len(conc_list), 1) if conc_list else 70.0

        # 3. Problem Solving
        prob_list = category_scores_map["PROBLEM_SOLVING"]
        problem_solving_score = round(sum(prob_list) / len(prob_list), 1) if prob_list else 70.0

        # 4. Communication / Structure
        comm_list = category_scores_map["COMMUNICATION"]
        communication_score = round(sum(comm_list) / len(comm_list), 1) if comm_list else 65.0

        # 5. Career Competency Coverage
        # Proportion of career skills evaluated and scored above 60%
        evaluated_career_skills = set(competency_scores.keys()).intersection(set(norm_required_skills.keys()))
        strong_career_skills = {
            k for k in evaluated_career_skills
            if (sum(competency_scores[k]) / len(competency_scores[k])) >= 60.0
        }
        total_career_reqs = max(1, len(norm_required_skills))
        coverage_ratio = len(strong_career_skills) / total_career_reqs
        career_competency_score = round(min(100.0, max(20.0, coverage_ratio * 100.0)), 1)

        # Overall Readiness Formula (Documented weighted formulation):
        # Overall Readiness = 0.30 * Technical + 0.20 * Conceptual + 0.20 * Problem Solving + 0.15 * Communication + 0.15 * Career Competency
        overall_readiness = round(
            0.30 * technical_score +
            0.20 * conceptual_score +
            0.20 * problem_solving_score +
            0.15 * communication_score +
            0.15 * career_competency_score
        )
        overall_readiness = max(0, min(100, overall_readiness))

        # Map to Readiness Band
        readiness_band = "FOUNDATION_REQUIRED"
        for band_id, band_info in [
            ("INTERVIEW_READY", READINESS_BANDS["INTERVIEW_READY"]),
            ("STRONG_PREPARATION", READINESS_BANDS["STRONG_PREPARATION"]),
            ("NEEDS_PRACTICE", READINESS_BANDS["NEEDS_PRACTICE"]),
            ("FOUNDATION_REQUIRED", READINESS_BANDS["FOUNDATION_REQUIRED"]),
        ]:
            if overall_readiness >= band_info["min_score"]:
                readiness_band = band_id
                break

        band_meta = READINESS_BANDS[readiness_band]

        # Identify Strengths & Weaknesses
        strengths: List[Dict[str, Any]] = []
        weaknesses: List[Dict[str, Any]] = []
        for comp_norm, scores in competency_scores.items():
            avg_s = round(sum(scores) / len(scores), 1)
            display_name = norm_required_skills.get(comp_norm, comp_norm.title())
            if avg_s >= 70.0:
                strengths.append({
                    "competency": display_name,
                    "average_score": avg_s,
                    "status": "DEMONSTRATED_STRENGTH",
                    "feedback": f"Strong conceptual and practical command demonstrated in interview questions."
                })
            else:
                weaknesses.append({
                    "competency": display_name,
                    "average_score": avg_s,
                    "status": "IMPROVEMENT_NEEDED",
                    "feedback": f"Demonstrated gaps in key concepts. Further study and hands-on reinforcement recommended."
                })

        strengths.sort(key=lambda x: -x["average_score"])
        weaknesses.sort(key=lambda x: x["average_score"])

        # Priority Skills (Weaknesses first, then missing career requirements)
        priority_skills = [w["competency"] for w in weaknesses]
        for req_norm, req_title in norm_required_skills.items():
            if req_norm not in competency_scores and req_title not in priority_skills:
                priority_skills.append(req_title)

        # Cross-Module Integrations (Additive intelligence layers)
        integrations = cls._build_cross_module_integrations(
            career_id=career_id,
            weak_competencies=[w["competency"] for w in weaknesses],
            user_id=user_id
        )

        # Explainable Summary Rationale
        explanation = cls._generate_explainable_summary(
            career_title=career.title,
            readiness_score=overall_readiness,
            readiness_band=readiness_band,
            strengths=strengths,
            weaknesses=weaknesses,
            integrations=integrations
        )

        return {
            "status": "success",
            "career": {
                "id": career.id,
                "title": career.title,
                "domain": career.domain,
            },
            "overall_readiness": overall_readiness,
            "readiness_band": readiness_band,
            "readiness_label": band_meta["label"],
            "readiness_summary": band_meta["summary"],
            "category_scores": {
                "technical": technical_score,
                "conceptual": conceptual_score,
                "problem_solving": problem_solving_score,
                "communication": communication_score,
                "career_competency": career_competency_score,
            },
            "questions_evaluated_count": len(evaluated_results),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "priority_skills": priority_skills,
            "question_results": evaluated_results,
            "integrations": integrations,
            "explanation": explanation,
            "assessment_disclaimer": "This simulator provides an educational readiness estimate for practice and preparation. It is not an objective psychological assessment or employment guarantee.",
            "provenance": "DEMO / SAMPLE / PROTOTYPE MARKET BENCHMARK — NOT LIVE LABOR MARKET DATA"
        }

    # ==========================================================================
    # PRIVATE HELPER METHODS: ANSWER EVALUATION & SCORING
    # ==========================================================================

    @classmethod
    def _evaluate_single_answer(
        cls,
        question_obj: Dict[str, Any],
        answer_text: str
    ) -> Dict[str, Any]:
        """
        Evaluates a single answer against expected concepts, completeness, and structure.
        """
        norm_answer = normalize_text(answer_text)
        expected_concepts = question_obj.get("expected_concepts", [])

        if not norm_answer or len(norm_answer.strip()) == 0:
            return {
                "question_id": question_obj["question_id"],
                "competency": question_obj["competency"],
                "category": question_obj["category"],
                "difficulty": question_obj["difficulty"],
                "question_text": question_obj["question_text"],
                "user_answer": "",
                "score": 0,
                "concept_coverage": 0.0,
                "completeness_score": 0.0,
                "structure_score": 0.0,
                "matched_concepts": [],
                "missing_concepts": expected_concepts,
                "feedback": "No answer was provided. Please articulate your technical knowledge to demonstrate readiness."
            }

        # 1. Concept Matching
        matched_concepts = []
        missing_concepts = []
        for concept in expected_concepts:
            norm_c = concept.lower().strip()
            # Check direct phrase or multi-word boundary
            if norm_c in norm_answer:
                matched_concepts.append(concept)
            else:
                # Check for slash options e.g. "mean/median"
                if "/" in norm_c:
                    parts = norm_c.split("/")
                    if any(p.strip() in norm_answer for p in parts):
                        matched_concepts.append(concept)
                        continue
                missing_concepts.append(concept)

        total_concepts = max(1, len(expected_concepts))
        concept_coverage = round((len(matched_concepts) / total_concepts) * 100.0, 1)

        # 2. Completeness Scoring (word count and depth)
        words = norm_answer.split()
        word_count = len(words)
        if word_count < 10:
            completeness_score = min(40.0, word_count * 4.0)
        elif word_count < 25:
            completeness_score = 40.0 + (word_count - 10) * 2.0  # 40 -> 70
        elif word_count < 60:
            completeness_score = 70.0 + (word_count - 25) * 0.7  # 70 -> 94.5
        else:
            completeness_score = 95.0 + min(5.0, (word_count - 60) * 0.2)
        completeness_score = round(min(100.0, completeness_score), 1)

        # 3. Structure & Communication Scoring
        # Positive indicators: punctuation, reasoning connectives, paragraphs
        connectives = [
            "because", "for example", "such as", "therefore", "in contrast",
            "whereas", "first", "second", "additionally", "in order to", "specifically"
        ]
        has_connective = any(c in norm_answer for c in connectives)
        sentence_count = len(re.split(r"[.!?]+", answer_text.strip()))

        base_structure = 50.0
        if sentence_count >= 2:
            base_structure += 20.0
        if has_connective:
            base_structure += 20.0
        if len(answer_text) > 0 and answer_text[0].isupper():
            base_structure += 10.0

        structure_score = round(min(100.0, max(20.0, base_structure)), 1)

        # 4. Answer Quality Score:
        # 0.60 * Concept Coverage + 0.20 * Completeness + 0.20 * Structure
        quality_score = round(
            0.60 * concept_coverage +
            0.20 * completeness_score +
            0.20 * structure_score
        )
        quality_score = max(0, min(100, quality_score))

        # 5. Explainable Feedback Generation
        feedback_parts = []
        if len(matched_concepts) > 0:
            feedback_parts.append(
                f"Demonstrated good awareness of: {', '.join(matched_concepts[:3])}."
            )
        if len(missing_concepts) > 0:
            feedback_parts.append(
                f"To strengthen this response, elaborate on: {', '.join(missing_concepts[:3])}."
            )
        if completeness_score < 60:
            feedback_parts.append("Consider providing a more comprehensive explanation with concrete examples.")

        feedback = " ".join(feedback_parts) if feedback_parts else "Adequate foundational response."

        return {
            "question_id": question_obj["question_id"],
            "competency": question_obj["competency"],
            "category": question_obj["category"],
            "difficulty": question_obj["difficulty"],
            "question_text": question_obj["question_text"],
            "user_answer": answer_text,
            "score": quality_score,
            "concept_coverage": concept_coverage,
            "completeness_score": completeness_score,
            "structure_score": structure_score,
            "matched_concepts": matched_concepts,
            "missing_concepts": missing_concepts,
            "feedback": feedback
        }

    # ==========================================================================
    # CROSS-MODULE INTEGRATIONS (11.1 - 11.5)
    # ==========================================================================

    @classmethod
    def _build_cross_module_integrations(
        cls,
        career_id: int,
        weak_competencies: List[str],
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Integrates interview weakness insights with Phase 11.1 ROI, 11.2 Portfolio,
        11.3 Academic Benchmarks, 11.4 Industry Demand, and 11.5 Trajectory.
        """
        integrations: Dict[str, Any] = {
            "skill_roi": None,
            "portfolio_project": None,
            "academic_alignment": None,
            "industry_demand": None,
            "trajectory_relevance": None,
        }

        # 1. Phase 11.1 Skill ROI Integration
        try:
            roi_res = SkillRoiService.calculate_career_skill_roi(
                career_id=career_id,
                user_id=user_id,
                hours_per_week=10
            )
            if roi_res and "ranked_skills" in roi_res:
                # Find the weak interview competency that has the highest ROI
                weak_norms = {normalize_skill_name(w) for w in weak_competencies}
                matched_roi = None
                for r_skill in roi_res["ranked_skills"]:
                    if normalize_skill_name(r_skill.get("skill_name", "")) in weak_norms:
                        matched_roi = r_skill
                        break
                # Fallback to quickest win
                best_roi = matched_roi or roi_res.get("quickest_win") or (roi_res["ranked_skills"][0] if roi_res["ranked_skills"] else None)
                if best_roi:
                    integrations["skill_roi"] = {
                        "prioritized_skill": best_roi.get("skill_name"),
                        "roi_score": best_roi.get("roi_score"),
                        "readiness_gain": best_roi.get("readiness_gain"),
                        "estimated_weeks": best_roi.get("estimated_weeks"),
                        "rationale": f"Improving {best_roi.get('skill_name')} yields high marginal readiness (+{best_roi.get('readiness_gain')}%) with high efficiency ({best_roi.get('roi_score')} pts/wk)."
                    }
        except Exception:
            pass

        # 2. Phase 11.2 Portfolio Capstone Integration
        try:
            p_res = PortfolioProjectService.recommend_projects_for_career(career_id=career_id, limit=2)
            proj_list = p_res.get("recommendations") or p_res.get("recommended_projects")
            if proj_list:
                rec_proj = proj_list[0]
                integrations["portfolio_project"] = {
                    "project_id": rec_proj.get("project_id"),
                    "title": rec_proj.get("title"),
                    "difficulty": rec_proj.get("difficulty"),
                    "estimated_hours": rec_proj.get("estimated_hours"),
                    "skills_addressed": rec_proj.get("missing_skills_addressed", []) + rec_proj.get("weak_skills_addressed", []),
                    "rationale": f"Building '{rec_proj.get('title')}' creates concrete proof-of-work deliverables to validate interview competencies."
                }
        except Exception:
            pass

        # 3. Phase 11.3 Academic Recommendation Benchmarking Integration
        try:
            acad_res = AcademicBenchmarkService.benchmark_career_curriculum(career_id=career_id, user_id=user_id)
            if acad_res and "coverage_summary" in acad_res:
                integrations["academic_alignment"] = {
                    "academic_program": acad_res.get("curriculum_baseline", {}).get("program_name"),
                    "curriculum_coverage_score": acad_res.get("coverage_summary", {}).get("coverage_score"),
                    "covered_competencies": [s.get("skill_name") for s in acad_res.get("curriculum_covered_skills", [])],
                    "curriculum_gap_competencies": [s.get("skill_name") for s in acad_res.get("curriculum_gap_skills", [])],
                    "disclaimer": acad_res.get("provenance_disclaimer"),
                }
        except Exception:
            pass

        # 4. Phase 11.4 Industry Demand Benchmarking Integration
        try:
            dem_res = IndustryDemandService.evaluate_career_industry_demand(career_id=career_id, user_id=user_id)
            if dem_res and "market_outlook" in dem_res:
                integrations["industry_demand"] = {
                    "demand_level": dem_res.get("market_outlook", {}).get("demand_level"),
                    "demand_score": dem_res.get("market_outlook", {}).get("demand_score"),
                    "growing_competencies": [s.get("skill_name") for s in dem_res.get("ranked_skills", [])[:3]],
                    "provenance_disclaimer": dem_res.get("provenance_disclaimer"),
                }
        except Exception:
            pass

        # 5. Phase 11.5 Career Trajectory Integration
        try:
            traj_res = CareerTrajectoryService.find_trajectory(target_career_id=career_id, max_hops=3, limit=1)
            if traj_res and "recommended_trajectory" in traj_res:
                rec_t = traj_res["recommended_trajectory"]
                integrations["trajectory_relevance"] = {
                    "is_multihop_better": traj_res.get("comparison", {}).get("is_multihop_better", False),
                    "trajectory_path": rec_t.get("path"),
                    "trajectory_roles": rec_t.get("careers"),
                    "progressive_skill_reuse": rec_t.get("progressive_skill_reuse"),
                    "total_learning_hours": rec_t.get("estimated_learning_hours"),
                }
        except Exception:
            pass

        return integrations

    @classmethod
    def _generate_explainable_summary(
        cls,
        career_title: str,
        readiness_score: int,
        readiness_band: str,
        strengths: List[Dict[str, Any]],
        weaknesses: List[Dict[str, Any]],
        integrations: Dict[str, Any]
    ) -> str:
        """
        Generates a transparent, professional natural-language summary of interview readiness.
        """
        band_info = READINESS_BANDS.get(readiness_band, READINESS_BANDS["FOUNDATION_REQUIRED"])

        parts = [
            f"Interview assessment for {career_title} indicates an estimated readiness score of {readiness_score}/100 ({band_info['label']})."
        ]

        if strengths:
            s_names = [s["competency"] for s in strengths[:3]]
            parts.append(f"Demonstrated solid competency in {', '.join(s_names)}.")

        if weaknesses:
            w_names = [w["competency"] for w in weaknesses[:3]]
            parts.append(f"Targeted preparation is recommended for {', '.join(w_names)}.")

        roi_data = integrations.get("skill_roi")
        if roi_data and roi_data.get("prioritized_skill"):
            parts.append(
                f"Prioritizing {roi_data['prioritized_skill']} yields highest learning efficiency (+{roi_data.get('readiness_gain')}% readiness gain)."
            )

        proj_data = integrations.get("portfolio_project")
        if proj_data and proj_data.get("title"):
            parts.append(
                f"Completing capstone project '{proj_data['title']}' will provide verified proof-of-work evidence for key gaps."
            )

        return " ".join(parts)
