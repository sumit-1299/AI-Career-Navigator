"""
Actionable Portfolio & Capstone Project Recommendation Engine for AI Career Navigator.
Phase 11 Module 11.2: Actionable Portfolio & Capstone Project Recommendation Engine.

Provides:
- Deterministic project catalog mapped to canonical skills and the 10 standardized IT career tracks.
- Skill coverage evaluation matching project competencies against career requirements and student skill gaps.
- Integration with Phase 11.1 Skill ROI engine (boosting projects that close high-ROI / Quickest Win gaps).
- Multi-factor deterministic ranking based on gap closure, career coverage, difficulty fit, and portfolio value.
- Explainable natural-language justification for why each project is recommended.
- Actionable portfolio deliverables checklist (code, architecture diagram, tests, CI/CD, documentation).
- Strict safety guarantee: ZERO database modifications or schema migrations.
"""

from typing import Any, Dict, List, Optional, Set
from models.career import Career
from models.career_skill import CareerSkill
from models.skill import Skill
from services.skill_gap_service import SkillGapService, SkillGapStatus
from services.skill_roi_service import SkillRoiService
from utils.normalization import normalize_skill_name, strip_parenthetical_qualifiers


# ==============================================================================
# DETERMINISTIC PORTFOLIO & CAPSTONE PROJECT CATALOG
# ==============================================================================
# Mapped strictly to canonical skills and the 10 standardized IT careers:
# 1. Software Developer
# 2. Web Developer
# 3. Data Analyst
# 4. Data Scientist
# 5. AI/ML Engineer
# 6. Cloud Engineer
# 7. DevOps Engineer
# 8. Cybersecurity Analyst
# 9. Network Engineer
# 10. Database Administrator
# ==============================================================================

PORTFOLIO_PROJECTS_CATALOG: List[Dict[str, Any]] = [
    # --------------------------------------------------------------------------
    # 1. SOFTWARE DEVELOPER PROJECTS
    # --------------------------------------------------------------------------
    {
        "project_id": "distributed-task-orchestrator",
        "title": "Microservices Distributed Task Queue & Worker Engine",
        "description": "High-throughput asynchronous task processing engine with worker nodes, priority scheduling, and persistent job state tracking.",
        "target_career_ids": [1],
        "domain": "Software Development",
        "difficulty": "Advanced",
        "estimated_hours": 45,
        "portfolio_value": 95,
        "demonstrated_skills": ["Python", "Java", "Data Structures", "SQL", "Git"],
        "deliverables": [
            "GitHub repository with modular multi-threaded worker architecture",
            "C4 system architecture diagram and sequence flow in README",
            "PostgreSQL schema with transactional job state transitions",
            "Automated unit & concurrency stress test suite (>85% coverage)",
            "OpenAPI REST endpoints for task submission and status polling"
        ],
        "extension_ideas": [
            "Add distributed locks using Redis or ZooKeeper",
            "Implement exponential backoff retry and Dead Letter Queue (DLQ)"
        ]
    },
    {
        "project_id": "in-memory-kv-store",
        "title": "Concurrent In-Memory Key-Value Store with Write-Ahead Logging",
        "description": "Fast key-value cache implementing custom hash tables, LRU eviction policy, thread-safe synchronization, and crash recovery via append-only logs.",
        "target_career_ids": [1],
        "domain": "Software Development",
        "difficulty": "Intermediate",
        "estimated_hours": 30,
        "portfolio_value": 90,
        "demonstrated_skills": ["Java", "Data Structures", "Git"],
        "deliverables": [
            "Clean Java repository with custom memory structures (no external cache libraries)",
            "Detailed benchmark performance report comparing against standard collections",
            "Binary protocol parser or socket server implementation",
            "Comprehensive test coverage validating data consistency across threads"
        ],
        "extension_ideas": [
            "Implement snapshotting alongside write-ahead logging (WAL)",
            "Support time-to-live (TTL) key expiration"
        ]
    },
    {
        "project_id": "rest-api-gateway",
        "title": "Lightweight API Gateway with Rate Limiting & Auth Validation",
        "description": "Reverse-proxy API gateway featuring token verification, route routing, sliding-window rate limiting, and centralized latency metrics.",
        "target_career_ids": [1],
        "domain": "Software Development",
        "difficulty": "Beginner",
        "estimated_hours": 20,
        "portfolio_value": 82,
        "demonstrated_skills": ["Python", "SQL", "Git", "Data Structures"],
        "deliverables": [
            "Modular Python application with clean request routing middleware",
            "Swagger / OpenAPI documentation with automated schema validation",
            "Relational database integration for consumer API key and quota management",
            "README containing setup instructions and sample curl requests"
        ],
        "extension_ideas": [
            "Implement token bucket rate limiting algorithm",
            "Add response payload caching for idempotent endpoints"
        ]
    },

    # --------------------------------------------------------------------------
    # 2. WEB DEVELOPER PROJECTS
    # --------------------------------------------------------------------------
    {
        "project_id": "collaborative-kanban-platform",
        "title": "Collaborative Real-Time Kanban Board & Workspace Platform",
        "description": "Feature-rich project workspace with drag-and-drop card columns, optimistic UI updates, Markdown task descriptions, and team activity feeds.",
        "target_career_ids": [2],
        "domain": "Web Development",
        "difficulty": "Advanced",
        "estimated_hours": 40,
        "portfolio_value": 94,
        "demonstrated_skills": ["React", "JavaScript", "HTML", "CSS", "Git"],
        "deliverables": [
            "Responsive React 18 single-page application with reusable component architecture",
            "Smooth HTML5 drag-and-drop board interaction with accessible keyboard controls",
            "State management handling optimistic mutations and rollback on network errors",
            "Interactive live deployment link (Vercel / Netlify) with demo test account"
        ],
        "extension_ideas": [
            "Add WebSocket synchronization for multi-user live cursors",
            "Support dark/light theme persistence and board export to JSON/CSV"
        ]
    },
    {
        "project_id": "ecommerce-product-catalog",
        "title": "Headless E-Commerce Storefront with Faceted Filtering & Cart",
        "description": "High-performance online shopping storefront featuring instant multi-attribute filtering, persistent cart state, and smooth checkout stepper.",
        "target_career_ids": [2],
        "domain": "Web Development",
        "difficulty": "Intermediate",
        "estimated_hours": 28,
        "portfolio_value": 88,
        "demonstrated_skills": ["React", "JavaScript", "HTML", "CSS", "Git"],
        "deliverables": [
            "React frontend with custom hooks for cart management and localStorage persistence",
            "Dynamic URL query-string synchronization for active search and category filters",
            "Accessible semantic HTML markup and mobile-first CSS styling",
            "Lighthouse audit report achieving >90 in Performance and Accessibility"
        ],
        "extension_ideas": [
            "Integrate mock Stripe checkout payment flow",
            "Implement image skeleton loaders and responsive image srcsets"
        ]
    },
    {
        "project_id": "interactive-analytics-dashboard",
        "title": "Responsive SaaS Analytics Portal with Component System",
        "description": "Executive metrics portal rendering SVG/Canvas data charts, configurable KPI widgets, and adaptive multi-tier navigation menus.",
        "target_career_ids": [2],
        "domain": "Web Development",
        "difficulty": "Beginner",
        "estimated_hours": 18,
        "portfolio_value": 80,
        "demonstrated_skills": ["HTML", "CSS", "JavaScript", "Git"],
        "deliverables": [
            "Semantic, standards-compliant HTML5 structure with custom CSS Grid layout",
            "Clean, dependency-light JavaScript DOM manipulation and event delegation",
            "Responsive design tested across desktop, tablet, and mobile breakpoints",
            "GitHub repository with GitHub Pages deployment and detailed README"
        ],
        "extension_ideas": [
            "Add animated KPI counters and SVG sparklines",
            "Export charts as downloadable PNG / PDF reports"
        ]
    },

    # --------------------------------------------------------------------------
    # 3. DATA ANALYST PROJECTS
    # --------------------------------------------------------------------------
    {
        "project_id": "executive-saas-churn-bi",
        "title": "Executive SaaS Revenue Analytics & Cohort Retention BI Suite",
        "description": "Comprehensive business intelligence project calculating Monthly Recurring Revenue (MRR), cohort retention curves, and customer lifetime value (LTV).",
        "target_career_ids": [3],
        "domain": "Data Analytics",
        "difficulty": "Advanced",
        "estimated_hours": 35,
        "portfolio_value": 92,
        "demonstrated_skills": ["Python", "SQL", "Power BI", "Statistics", "Excel"],
        "deliverables": [
            "Multi-tab Power BI dashboard (.pbix) with drill-down DAX measures",
            "Complex SQL query scripts with window functions, CTEs, and cohort groupings",
            "Python data transformation notebook validating data cleansing steps",
            "Executive PDF slide deck summarizing actionable churn mitigation findings"
        ],
        "extension_ideas": [
            "Implement automated scheduled refresh via Power BI Gateway",
            "Build dynamic what-if parameter sliders for subscription pricing scenarios"
        ]
    },
    {
        "project_id": "retail-omnichannel-analytics",
        "title": "Omnichannel Retail Sales & Inventory Optimization Model",
        "description": "Multi-region supply chain and sales analysis discovering inventory turnover bottlenecks, stockout risks, and seasonal promotion effectiveness.",
        "target_career_ids": [3],
        "domain": "Data Analytics",
        "difficulty": "Intermediate",
        "estimated_hours": 24,
        "portfolio_value": 86,
        "demonstrated_skills": ["SQL", "Excel", "Power BI", "Statistics"],
        "deliverables": [
            "Interactive Excel model utilizing Power Query, advanced formulas, and Pivot Tables",
            "Normalized relational schema with SQL analytical queries for inventory velocity",
            "Power BI executive view highlighting stockout risk heatmaps by warehouse",
            "Clear documentation detailing metric definitions and data assumptions"
        ],
        "extension_ideas": [
            "Calculate safety stock levels and economic order quantity (EOQ)",
            "Incorporate external economic indicators or weather impact data"
        ]
    },
    {
        "project_id": "customer-survey-eda",
        "title": "Customer Feedback & Product Satisfaction Statistical Study",
        "description": "Statistical exploration of customer satisfaction surveys evaluating Net Promoter Score (NPS), demographic correlations, and feature sentiment.",
        "target_career_ids": [3],
        "domain": "Data Analytics",
        "difficulty": "Beginner",
        "estimated_hours": 16,
        "portfolio_value": 78,
        "demonstrated_skills": ["Excel", "Statistics", "SQL"],
        "deliverables": [
            "Structured Excel workbook with descriptive statistics and correlation matrices",
            "Cleaned dataset with documented handling of missing values and outliers",
            "Visual summary charts communicating survey trends to non-technical stakeholders",
            "Concise executive memo recommending top 3 product improvement priorities"
        ],
        "extension_ideas": [
            "Conduct two-sample hypothesis testing comparing user cohorts",
            "Create interactive slicers and dynamic summary cards"
        ]
    },

    # --------------------------------------------------------------------------
    # 4. DATA SCIENTIST PROJECTS
    # --------------------------------------------------------------------------
    {
        "project_id": "predictive-lead-conversion-ml",
        "title": "Predictive Customer Churn & Propensity Scoring Platform",
        "description": "End-to-end supervised machine learning pipeline predicting customer churn with rigorous feature engineering, cross-validation, and SHAP explainability.",
        "target_career_ids": [4],
        "domain": "Data Science",
        "difficulty": "Advanced",
        "estimated_hours": 42,
        "portfolio_value": 95,
        "demonstrated_skills": ["Python", "SQL", "Pandas", "Statistics", "Machine Learning", "Git"],
        "deliverables": [
            "Reproducible Jupyter notebook walking through EDA, feature scaling, and model tuning",
            "Comparative evaluation across Random Forest, XGBoost, and Logistic Regression",
            "SHAP / LIME explainability plots breaking down individual prediction drivers",
            "Packaged Python inference script saving serialized pipeline artifacts (.joblib)"
        ],
        "extension_ideas": [
            "Implement probability calibration (Isotonic / Platt scaling)",
            "Construct a cost-benefit matrix optimizing classification decision threshold"
        ]
    },
    {
        "project_id": "algorithmic-risk-scoring",
        "title": "Financial Credit Default Probability & Risk Scoring Engine",
        "description": "Statistical risk modeling applying feature discretization, Weight of Evidence (WoE) transformation, and Information Value (IV) selection for default prediction.",
        "target_career_ids": [4],
        "domain": "Data Science",
        "difficulty": "Intermediate",
        "estimated_hours": 28,
        "portfolio_value": 89,
        "demonstrated_skills": ["Python", "Statistics", "Pandas", "Machine Learning"],
        "deliverables": [
            "Clean Python codebase computing scorecard metrics, ROC-AUC, and Gini coefficient",
            "Documented handling of severe class imbalance via SMOTE and class-weighting",
            "Statistical validation report checking for multicollinearity using VIF",
            "README outlining model regulatory governance and fair lending compliance"
        ],
        "extension_ideas": [
            "Build population stability index (PSI) monitoring script for distribution drift",
            "Deploy interactive Streamlit application for underwriting loan officers"
        ]
    },
    {
        "project_id": "housing-price-regression",
        "title": "Real Estate Valuation Engine with Regularized Regression",
        "description": "Regression analysis predicting property valuations using geospatial coordinates, feature interactions, and Lasso/Ridge regularization.",
        "target_career_ids": [4],
        "domain": "Data Science",
        "difficulty": "Beginner",
        "estimated_hours": 18,
        "portfolio_value": 80,
        "demonstrated_skills": ["Python", "Pandas", "Statistics", "SQL"],
        "deliverables": [
            "End-to-end data preparation notebook handling skewed target distributions (log transform)",
            "Comparative model residual diagnostic plots checking homoscedasticity",
            "Cross-validated RMSE and R² evaluation metrics across baseline models",
            "GitHub repository with clear data dictionary and virtualenv instructions"
        ],
        "extension_ideas": [
            "Extract census demographic features via public APIs",
            "Incorporate K-Means spatial cluster indicators into regression features"
        ]
    },

    # --------------------------------------------------------------------------
    # 5. AI/ML ENGINEER PROJECTS
    # --------------------------------------------------------------------------
    {
        "project_id": "vision-defect-inspection-api",
        "title": "Production Deep Learning Vision API with Transfer Learning",
        "description": "Convolutional neural network for industrial defect classification built with TensorFlow/Keras, quantized for low-latency REST inference.",
        "target_career_ids": [5],
        "domain": "Artificial Intelligence",
        "difficulty": "Advanced",
        "estimated_hours": 48,
        "portfolio_value": 96,
        "demonstrated_skills": ["Python", "Deep Learning", "TensorFlow", "Machine Learning", "Statistics"],
        "deliverables": [
            "Training pipeline applying data augmentation, learning rate scheduling, and early stopping",
            "Fine-tuned transfer learning architecture (ResNet / EfficientNet) with benchmark metrics",
            "FastAPI / Flask serving container serving batch and single-image predictions",
            "Comprehensive confusion matrix and Precision-Recall curve documentation"
        ],
        "extension_ideas": [
            "Export optimized model to TFLite / ONNX runtime for edge devices",
            "Implement Grad-CAM heatmap visualization to explain vision model focus"
        ]
    },
    {
        "project_id": "nlp-semantic-document-search",
        "title": "Semantic Document Search & Vector Embedding Retrieval Engine",
        "description": "Retrieval-augmented search pipeline using dense vector embeddings, cosine similarity index, and re-ranking for enterprise technical documentation.",
        "target_career_ids": [5],
        "domain": "Artificial Intelligence",
        "difficulty": "Intermediate",
        "estimated_hours": 32,
        "portfolio_value": 91,
        "demonstrated_skills": ["Python", "TensorFlow", "Machine Learning", "Statistics"],
        "deliverables": [
            "Document chunking and embedding generation pipeline using Transformer encoders",
            "Vector indexing engine with similarity thresholds and hybrid keyword filtering",
            "Interactive query evaluation CLI demonstrating top-k passage relevance",
            "Evaluation notebook measuring Mean Reciprocal Rank (MRR) and NDCG@5"
        ],
        "extension_ideas": [
            "Integrate FAISS or ChromaDB vector store for sub-millisecond retrieval",
            "Build cross-encoder re-ranking stage to boost precision"
        ]
    },
    {
        "project_id": "tabular-multiclass-classifier",
        "title": "Production Tabular Classifier with Model Monitoring",
        "description": "Multi-class predictive classifier with automated hyperparameter tuning (Optuna/GridSearch) and structured data preprocessing pipelines.",
        "target_career_ids": [5],
        "domain": "Artificial Intelligence",
        "difficulty": "Beginner",
        "estimated_hours": 20,
        "portfolio_value": 82,
        "demonstrated_skills": ["Python", "Machine Learning", "Statistics"],
        "deliverables": [
            "Scikit-learn / TensorFlow pipeline avoiding data leakage across train/validation splits",
            "Automated hyperparameter optimization script with convergence tracking",
            "Detailed evaluation report covering Macro F1, Balanced Accuracy, and Log-Loss",
            "Structured repository with requirements.txt, configuration YAML, and unit tests"
        ],
        "extension_ideas": [
            "Log model training experiments using MLflow or Weights & Biases",
            "Simulate data drift and trigger automated alerting"
        ]
    },

    # --------------------------------------------------------------------------
    # 6. CLOUD ENGINEER PROJECTS
    # --------------------------------------------------------------------------
    {
        "project_id": "aws-multi-tier-ha-arch",
        "title": "Resilient Multi-AZ Cloud Architecture with Auto Scaling on AWS",
        "description": "Enterprise-grade cloud infrastructure on AWS spanning multiple Availability Zones with Application Load Balancer, Auto Scaling, and secure VPC subnets.",
        "target_career_ids": [6],
        "domain": "Cloud Computing",
        "difficulty": "Advanced",
        "estimated_hours": 40,
        "portfolio_value": 94,
        "demonstrated_skills": ["AWS", "Linux", "Networking", "Python", "Docker"],
        "deliverables": [
            "Complete CloudFormation or Terraform Infrastructure as Code (IaC) configuration",
            "VPC network architecture diagram depicting public/private subnets, NAT, and route tables",
            "Automated health check and failover demonstration simulating instance termination",
            "Security group hardening documentation adhering to least-privilege principles"
        ],
        "extension_ideas": [
            "Incorporate AWS WAF rules protecting against common OWASP vulnerabilities",
            "Configure centralized CloudWatch log subscription and anomaly alarms"
        ]
    },
    {
        "project_id": "containerized-microservices-ecs",
        "title": "Containerized Web Microservices Platform on AWS ECS Fargate",
        "description": "Serverless container workload deployed on AWS ECS with private ECR container registries, Secrets Manager credentials, and HTTPS termination.",
        "target_career_ids": [6],
        "domain": "Cloud Computing",
        "difficulty": "Intermediate",
        "estimated_hours": 28,
        "portfolio_value": 89,
        "demonstrated_skills": ["AWS", "Docker", "Linux", "Networking"],
        "deliverables": [
            "Multi-stage Dockerfile producing minimal, secure production container images",
            "ECS Task Definition and Service configuration files with resource limits",
            "Step-by-step deployment runbook detailing SSL certificate and DNS setup",
            "Cost breakdown estimate demonstrating serverless container cost efficiency"
        ],
        "extension_ideas": [
            "Implement blue/green deployment strategy using AWS CodeDeploy",
            "Enable AWS X-Ray distributed tracing across container endpoints"
        ]
    },
    {
        "project_id": "cloud-cost-health-monitor",
        "title": "Automated Cloud Resource Cost & Security Audit Utility",
        "description": "Serverless Lambda function written in Python that audits unattached EBS volumes, idle elastic IPs, and insecure security group CIDR blocks.",
        "target_career_ids": [6],
        "domain": "Cloud Computing",
        "difficulty": "Beginner",
        "estimated_hours": 16,
        "portfolio_value": 81,
        "demonstrated_skills": ["Python", "AWS", "Linux"],
        "deliverables": [
            "Boto3 Python script scanning AWS account resources for optimization candidates",
            "Automated weekly markdown/HTML report sent via Amazon SNS / SES email",
            "IAM role definition adhering to strict read-only audit policy permissions",
            "README instructions for local testing with Moto / LocalStack mock services"
        ],
        "extension_ideas": [
            "Add automated remediation mode to terminate untagged test instances",
            "Output cost savings metrics formatted for Slack / Discord webhooks"
        ]
    },

    # --------------------------------------------------------------------------
    # 7. DEVOPS ENGINEER PROJECTS
    # --------------------------------------------------------------------------
    {
        "project_id": "gitops-kubernetes-cicd",
        "title": "End-to-End GitOps Deployment Pipeline with Kubernetes & ArgoCD",
        "description": "Production continuous integration and continuous deployment pipeline automating linting, container building, vulnerability scanning, and GitOps delivery.",
        "target_career_ids": [7],
        "domain": "DevOps",
        "difficulty": "Advanced",
        "estimated_hours": 45,
        "portfolio_value": 96,
        "demonstrated_skills": ["Kubernetes", "Docker", "CI/CD", "Linux", "Git"],
        "deliverables": [
            "Kubernetes manifests (Deployments, Services, Ingress, ConfigMaps, Secrets)",
            "Automated GitHub Actions CI workflow executing unit tests and Trivy container scan",
            "Declarative GitOps repository setup with ArgoCD synchronization manifests",
            "Demonstration video or GIF showing automated canary / rolling zero-downtime release"
        ],
        "extension_ideas": [
            "Implement Prometheus and Grafana monitoring stack with alert manager",
            "Configure Horizontal Pod Autoscaler (HPA) responding to traffic spikes"
        ]
    },
    {
        "project_id": "dockerized-multi-stage-ci",
        "title": "Hardened Multi-Stage Docker Pipeline with Security Gateways",
        "description": "Enterprise containerization pipeline enforcing non-root users, minimal Alpine/distroless bases, and automated static security analysis.",
        "target_career_ids": [7],
        "domain": "DevOps",
        "difficulty": "Intermediate",
        "estimated_hours": 26,
        "portfolio_value": 88,
        "demonstrated_skills": ["Docker", "CI/CD", "Linux", "Git"],
        "deliverables": [
            "Highly optimized Dockerfile demonstrating layer caching and size reduction (<100MB)",
            "CI pipeline blocking deployment on high/critical CVE container vulnerabilities",
            "Docker Compose stack orchestrating web service, database, and health probes",
            "Security audit checklist document explaining hardening rationale"
        ],
        "extension_ideas": [
            "Sign container images cryptographically with Cosign / Sigstore",
            "Implement automated dependency bump pipeline using Dependabot / Renovate"
        ]
    },
    {
        "project_id": "linux-server-automation-ansible",
        "title": "Automated Linux Server Provisioning & Hardening Playbooks",
        "description": "Idempotent configuration management playbooks provisioning Nginx web servers, firewall rules, automated OS patching, and SSH key management.",
        "target_career_ids": [7],
        "domain": "DevOps",
        "difficulty": "Beginner",
        "estimated_hours": 18,
        "portfolio_value": 82,
        "demonstrated_skills": ["Linux", "Git", "CI/CD"],
        "deliverables": [
            "Modular Ansible playbooks / Bash automation scripts structured by server roles",
            "CIS benchmark hardening verification report testing SSH, UFW, and fail2ban",
            "GitHub Actions workflow validating playbook syntax with ansible-lint",
            "Comprehensive setup instructions using local Vagrant / Multipass VMs"
        ],
        "extension_ideas": [
            "Add automated SSL certificate renewal via Let's Encrypt Certbot",
            "Export node metrics into centralized Grafana dashboard"
        ]
    },

    # --------------------------------------------------------------------------
    # 8. CYBERSECURITY ANALYST PROJECTS
    # --------------------------------------------------------------------------
    {
        "project_id": "soc-siem-detection-lab",
        "title": "Enterprise SIEM Security Operations Lab & Threat Detection Suite",
        "description": "Security Operations Center (SOC) home lab configuring Elasticsearch/Wazuh SIEM, ingesting multi-system event logs, and generating Sigma detection rules.",
        "target_career_ids": [8],
        "domain": "Cybersecurity",
        "difficulty": "Advanced",
        "estimated_hours": 44,
        "portfolio_value": 95,
        "demonstrated_skills": ["SIEM", "Linux", "Networking", "Cybersecurity", "Python"],
        "deliverables": [
            "Fully configured SIEM detection lab with documented attack simulation telemetry",
            "Custom Sigma / Yara detection rules mapped to MITRE ATT&CK framework techniques",
            "Incident Response triage playbook for brute-force and privilege escalation alerts",
            "Executive incident summary memo detailing timeline, scope, and remediation"
        ],
        "extension_ideas": [
            "Automate threat response webhook executing IP blocking via iptables",
            "Integrate open-source threat intelligence feeds (AlienVault OTX / MISP)"
        ]
    },
    {
        "project_id": "network-vuln-scanner",
        "title": "Automated Network Vulnerability Scanner & Port Auditor",
        "description": "Python security utility performing multi-threaded TCP SYN port scanning, service banner grabbing, and known CVE mapping against NIST NVD database.",
        "target_career_ids": [8],
        "domain": "Cybersecurity",
        "difficulty": "Intermediate",
        "estimated_hours": 28,
        "portfolio_value": 89,
        "demonstrated_skills": ["Python", "Networking", "Linux", "Cybersecurity"],
        "deliverables": [
            "Multi-threaded socket network scanner handling CIDR subnet ranges gracefully",
            "Automated vulnerability report generator producing structured JSON and PDF findings",
            "Responsible disclosure & authorized testing methodology documentation",
            "Test suite validating scanner accuracy against controlled local mock targets"
        ],
        "extension_ideas": [
            "Incorporate SSL/TLS cipher suite security audit checks",
            "Build asynchronous scan worker using Python asyncio"
        ]
    },
    {
        "project_id": "hardened-linux-bastion",
        "title": "Hardened Linux Bastion Host & Network Perimeter Defense",
        "description": "Zero-trust jump server configured with multi-factor SSH authentication, iptables network filtering, strict sudo auditing, and intrusion alerting.",
        "target_career_ids": [8],
        "domain": "Cybersecurity",
        "difficulty": "Beginner",
        "estimated_hours": 18,
        "portfolio_value": 81,
        "demonstrated_skills": ["Linux", "Networking", "Cybersecurity"],
        "deliverables": [
            "Hardened Linux configuration scripts enforcing CIS Level 1 benchmark requirements",
            "Fail2ban and auditd configuration logging all session commands to tamper-proof storage",
            "Network traffic capture (.pcap) analysis analyzing normal vs malicious connection attempts",
            "Step-by-step administrator guide for onboarding privileged operators"
        ],
        "extension_ideas": [
            "Integrate Google Authenticator PAM module for TOTP MFA at SSH login",
            "Send real-time root privilege escalation alerts via Telegram / Slack"
        ]
    },

    # --------------------------------------------------------------------------
    # 9. NETWORK ENGINEER PROJECTS
    # --------------------------------------------------------------------------
    {
        "project_id": "enterprise-multi-vlan-topology",
        "title": "Enterprise Multi-VLAN Segmented Network Topology with OSPF",
        "description": "High-availability enterprise campus network featuring multi-VLAN segmentation, inter-VLAN routing, OSPF dynamic routing, and redundant HSRP default gateways.",
        "target_career_ids": [9],
        "domain": "Networking",
        "difficulty": "Advanced",
        "estimated_hours": 38,
        "portfolio_value": 94,
        "demonstrated_skills": ["Networking", "Routing and Switching", "CCNA", "Network Security", "Linux"],
        "deliverables": [
            "Cisco Packet Tracer / GNS3 topology file with full startup-config archives",
            "Comprehensive IP addressing plan and VLSM subnet allocation documentation",
            "Verification show command outputs validating OSPF neighbor states and HSRP failover",
            "Access Control List (ACL) security matrix restricting inter-departmental traffic"
        ],
        "extension_ideas": [
            "Implement 802.1Q trunking with EtherChannel link aggregation",
            "Configure DHCP snooping and Dynamic ARP Inspection (DAI) against spoofing"
        ]
    },
    {
        "project_id": "site-to-site-ipsec-vpn",
        "title": "Secure Site-to-Site IPsec VPN Gateway with GRE Tunneling",
        "description": "Encrypted branch-office interconnect establishing route-based IPsec VPN tunnels, Phase 1/Phase 2 IKE security associations, and network address translation (NAT).",
        "target_career_ids": [9],
        "domain": "Networking",
        "difficulty": "Intermediate",
        "estimated_hours": 26,
        "portfolio_value": 88,
        "demonstrated_skills": ["Networking", "Routing and Switching", "CCNA", "Network Security"],
        "deliverables": [
            "Documented Cisco IOS configuration files for headquarter and branch routers",
            "Wireshark packet capture analysis proving payload encryption (ESP headers)",
            "Failover testing log documenting primary vs backup tunnel convergence times",
            "Network security hardening audit verifying crypto key lifetime policies"
        ],
        "extension_ideas": [
            "Add BGP routing over DMVPN for scalable multi-site connectivity",
            "Implement QoS traffic shaping prioritizing VoIP over bulk data"
        ]
    },
    {
        "project_id": "python-network-automation-cli",
        "title": "Automated Network Device Configuration & Backup Tool in Python",
        "description": "Network automation utility leveraging Netmiko / Scrapli to automate bulk configuration deployment, interface health checks, and running-config backups.",
        "target_career_ids": [9],
        "domain": "Networking",
        "difficulty": "Beginner",
        "estimated_hours": 18,
        "portfolio_value": 83,
        "demonstrated_skills": ["Python", "Networking", "Linux", "CCNA"],
        "deliverables": [
            "Clean Python automation CLI with YAML device inventory and Jinja2 templates",
            "Automated configuration backup archiving configs with timestamped Git commits",
            "Error handling handling unreachable hosts and authentication timeouts gracefully",
            "Documentation explaining how automation eliminates human configuration drift"
        ],
        "extension_ideas": [
            "Validate configuration changes before commit using NAPALM compliance checks",
            "Build interface traffic utilization monitor outputting CSV reports"
        ]
    },

    # --------------------------------------------------------------------------
    # 10. DATABASE ADMINISTRATOR PROJECTS
    # --------------------------------------------------------------------------
    {
        "project_id": "postgres-ha-streaming-cluster",
        "title": "High-Availability PostgreSQL Cluster with Streaming Replication",
        "description": "Production database infrastructure featuring primary-standby streaming replication, connection pooling via PgBouncer, and automated failover.",
        "target_career_ids": [10],
        "domain": "Database Management",
        "difficulty": "Advanced",
        "estimated_hours": 42,
        "portfolio_value": 95,
        "demonstrated_skills": ["SQL", "PostgreSQL", "Linux", "Database Security"],
        "deliverables": [
            "Step-by-step cluster setup guide configuring postgresql.conf and pg_hba.conf",
            "Benchmarking report evaluating read-replica query scaling under concurrent load",
            "Disaster recovery simulation documenting zero-data-loss failover promotion",
            "PgBouncer connection pooling configuration optimizing memory and latency"
        ],
        "extension_ideas": [
            "Configure Patroni with etcd for automated consensus-based leader election",
            "Set up SSL client certificate authentication for database connections"
        ]
    },
    {
        "project_id": "db-query-tuning-optimization",
        "title": "Enterprise Database Query Optimization & Indexing Benchmark",
        "description": "Performance tuning project analyzing slow query logs, optimizing complex joins using EXPLAIN ANALYZE, and designing composite/partial indexing strategies.",
        "target_career_ids": [10],
        "domain": "Database Management",
        "difficulty": "Intermediate",
        "estimated_hours": 26,
        "portfolio_value": 89,
        "demonstrated_skills": ["SQL", "PostgreSQL", "MySQL", "Database Security"],
        "deliverables": [
            "Comprehensive query optimization report showcasing before/after EXPLAIN cost metrics",
            "Demonstrated reduction in execution time across 5 realistic high-volume queries (>70% lift)",
            "Index design documentation covering B-Tree, GIN, and BRIN indexing trade-offs",
            "Database security audit script auditing role privileges and schemas"
        ],
        "extension_ideas": [
            "Implement declarative table partitioning across large historical time-series datasets",
            "Set up pg_stat_statements monitoring dashboard highlighting query degradation"
        ]
    },
    {
        "project_id": "automated-db-backup-pitr",
        "title": "Automated Database Backup, Encryption & Point-in-Time Recovery Suite",
        "description": "Automated backup architecture implementing physical WAL archiving, encrypted backups to remote storage, and validated Point-in-Time Recovery (PITR).",
        "target_career_ids": [10],
        "domain": "Database Management",
        "difficulty": "Beginner",
        "estimated_hours": 18,
        "portfolio_value": 82,
        "demonstrated_skills": ["SQL", "PostgreSQL", "Linux", "Database Security"],
        "deliverables": [
            "Cron-based automated backup scripts with GPG encryption and rotation policies",
            "Validated Point-in-Time Recovery (PITR) drill restoring database to exact target timestamp",
            "Audit verification log checking backup checksum integrity and retention windows",
            "Disaster Recovery Runbook (RTO and RPO metrics) formatted for IT leadership"
        ],
        "extension_ideas": [
            "Integrate automated backup notification alerts via email/webhooks on failure",
            "Implement pgBackRest for differential and incremental compressed backups"
        ]
    }
]


class PortfolioProjectService:
    """Service providing career- and skill-gap-driven capstone and portfolio project recommendations."""

    @classmethod
    def get_all_projects(cls) -> List[Dict[str, Any]]:
        """Returns the complete immutable catalog of defined portfolio projects."""
        return PORTFOLIO_PROJECTS_CATALOG

    @classmethod
    def match_project_skills(
        cls,
        project_skills: List[str],
        career_skills: List[CareerSkill],
        missing_skills_norm: Set[str],
        weak_skills_norm: Set[str]
    ) -> Dict[str, Any]:
        """
        Determines the intersection between project competencies, career requirements,
        and student skill deficits.
        Uses normalized skill names to ensure multi-source alias and case-insensitive alignment.
        """
        proj_norm_set = set()
        for s in project_skills:
            norm_s = normalize_skill_name(s)
            if norm_s:
                proj_norm_set.add(norm_s)
            stripped = normalize_skill_name(strip_parenthetical_qualifiers(s))
            if stripped:
                proj_norm_set.add(stripped)

        try:
            from models.skill_alias import SkillAlias
            for s in list(proj_norm_set):
                alias_record = SkillAlias.query.filter_by(normalized_alias=s).first()
                if alias_record and alias_record.canonical_skill:
                    cname = normalize_skill_name(alias_record.canonical_skill.canonical_name)
                    if cname:
                        proj_norm_set.add(cname)
        except Exception:
            pass

        covered_career_skills = []
        missing_addressed = []
        weak_addressed = []

        total_importance_covered = 0

        for cs in career_skills:
            cs_norm = normalize_skill_name(cs.skill_name)
            if cs_norm in proj_norm_set:
                covered_career_skills.append(cs.skill_name)
                total_importance_covered += (cs.importance or 1)

                if cs_norm in missing_skills_norm:
                    missing_addressed.append(cs.skill_name)
                elif cs_norm in weak_skills_norm:
                    weak_addressed.append(cs.skill_name)

        return {
            "covered_career_skills": covered_career_skills,
            "missing_addressed": missing_addressed,
            "weak_addressed": weak_addressed,
            "total_importance_covered": total_importance_covered,
            "coverage_count": len(covered_career_skills)
        }

    @classmethod
    def calculate_project_score(
        cls,
        project: Dict[str, Any],
        career: Career,
        match_info: Dict[str, Any],
        total_career_skills_count: int,
        student_readiness: float,
        quickest_win_norm: Optional[str] = None,
        top_roi_norms: Optional[Set[str]] = None,
        is_personalized: bool = False
    ) -> float:
        """
        Computes a deterministic recommendation score (0.0 to 100.0) for a project.

        Formula Components:
        1. Career Relevance (15%): Direct career match (100) vs domain match (75).
        2. Career Skill Coverage (25%): Fraction of required career skills demonstrated.
        3. Gap Closure (30%): Proportion of student's missing and weak skills addressed.
        4. ROI Alignment (15%): Bonus for addressing Module 11.1 Quickest Win / Top ROI skills.
        5. Difficulty Fit (10%): Match between project difficulty and student readiness stage.
        6. Portfolio Appeal (5%): Inherent portfolio value score.
        """
        # 1. Career Relevance Score (0-100)
        target_ids = project.get("target_career_ids", [])
        if career.id in target_ids:
            s_career = 100.0
        elif (project.get("domain") or "").lower() == (career.domain or "").lower():
            s_career = 75.0
        elif match_info["coverage_count"] > 0:
            s_career = 50.0
        else:
            s_career = 20.0

        # 2. Career Skill Coverage Score (0-100)
        total_req = max(1, total_career_skills_count)
        s_coverage = min(100.0, (match_info["coverage_count"] / float(total_req)) * 100.0)

        # 3. Gap Closure Score (0-100)
        missing_count = len(match_info["missing_addressed"])
        weak_count = len(match_info["weak_addressed"])

        if is_personalized:
            # Score heavily based on solving actual deficits
            gap_points = (missing_count * 2.0) + (weak_count * 1.0)
            # Normalize against typical deficit target of 3 skills
            s_gap = min(100.0, (gap_points / 3.0) * 100.0)
            if missing_count == 0 and weak_count == 0:
                s_gap = 10.0 if total_req > 0 else 50.0
        else:
            # Unauthenticated: default to coverage
            s_gap = s_coverage

        # 4. ROI Alignment Score (0-100)
        proj_skills_norm = {normalize_skill_name(s) for s in project.get("demonstrated_skills", [])}
        s_roi = 50.0  # Baseline neutral

        if quickest_win_norm and quickest_win_norm in proj_skills_norm:
            s_roi = 100.0  # Solves the fastest readiness gain opportunity
        elif top_roi_norms and (top_roi_norms & proj_skills_norm):
            s_roi = 80.0
        elif is_personalized and (missing_count > 0 or weak_count > 0):
            s_roi = 65.0

        # 5. Difficulty Fit Score (0-100)
        diff = (project.get("difficulty") or "Intermediate").lower()
        if student_readiness < 40.0:  # Novice / Developing
            diff_scores = {"beginner": 100.0, "intermediate": 80.0, "advanced": 55.0}
        elif student_readiness < 70.0:  # Proficient
            diff_scores = {"beginner": 80.0, "intermediate": 100.0, "advanced": 85.0}
        else:  # Advanced
            diff_scores = {"beginner": 60.0, "intermediate": 85.0, "advanced": 100.0}

        s_difficulty = diff_scores.get(diff, 80.0)

        # 6. Portfolio Appeal (0-100)
        s_portfolio = float(project.get("portfolio_value", 85))

        # Weighted composite score
        if is_personalized:
            composite = (
                (0.30 * s_gap) +
                (0.25 * s_coverage) +
                (0.15 * s_career) +
                (0.15 * s_roi) +
                (0.10 * s_difficulty) +
                (0.05 * s_portfolio)
            )
        else:
            composite = (
                (0.40 * s_coverage) +
                (0.30 * s_career) +
                (0.15 * s_difficulty) +
                (0.15 * s_portfolio)
            )

        return round(max(0.0, min(100.0, composite)), 1)

    @classmethod
    def generate_recommendation_reason(
        cls,
        project_title: str,
        career_title: str,
        covered_skills: List[str],
        missing_addressed: List[str],
        weak_addressed: List[str],
        is_quickest_win: bool,
        difficulty: str
    ) -> str:
        """Generates an explainable, deterministic justification for recommending this project."""
        reasons = []

        if is_quickest_win and missing_addressed:
            reasons.append(
                f"Addresses your quickest-win competency '{missing_addressed[0]}' along with "
                f"{len(covered_skills)} core skills required for {career_title}."
            )
        elif missing_addressed and weak_addressed:
            reasons.append(
                f"Directly bridges missing skills ({', '.join(missing_addressed)}) and reinforces "
                f"weak areas ({', '.join(weak_addressed)}) required by {career_title}."
            )
        elif missing_addressed:
            reasons.append(
                f"Provides hands-on proof-of-work for key missing requirements: {', '.join(missing_addressed)}."
            )
        elif weak_addressed:
            reasons.append(
                f"Reinforces practical implementation in developing competencies: {', '.join(weak_addressed)}."
            )
        else:
            reasons.append(
                f"Demonstrates comprehensive mastery of {len(covered_skills)} required competencies: "
                f"{', '.join(covered_skills[:3])}."
            )

        reasons.append(
            f"The {difficulty.lower()} scope provides verified portfolio deliverables employers look for."
        )

        return " ".join(reasons)

    @classmethod
    def recommend_projects_for_career(
        cls,
        career_id: int,
        user_id: Optional[int] = None,
        difficulty_filter: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Recommends and ranks actionable portfolio/capstone projects for a specific career track.
        Personalizes by student's current gaps and Module 11.1 Skill ROI priorities when user_id is provided.
        """
        career = Career.query.get(career_id)
        if not career:
            return {
                "error": "CAREER_NOT_FOUND",
                "message": f"Career with ID {career_id} not found"
            }

        # 1. Fetch career skills
        career_skills: List[CareerSkill] = (
            career.skills if hasattr(career, "skills") and career.skills else
            CareerSkill.query.filter_by(career_id=career.id).all()
        )

        # 2. Retrieve student skill gap and Module 11.1 ROI priorities if user_id present
        is_personalized = False
        student_skills: List[Skill] = []
        missing_skills_norm: Set[str] = set()
        weak_skills_norm: Set[str] = set()
        student_readiness = 0.0
        quickest_win_norm = None
        top_roi_norms: Set[str] = set()

        if user_id:
            is_personalized = True
            student_skills = Skill.query.filter_by(user_id=user_id).all()

            gap_analysis = SkillGapService.evaluate_career_gap(career, student_skills)
            student_readiness = gap_analysis["summary"]["readiness_percentage"]

            for g in gap_analysis["prioritized_skill_gaps"]:
                norm_name = normalize_skill_name(g["skill_name"])
                if g["status"] == SkillGapStatus.MISSING:
                    missing_skills_norm.add(norm_name)
                elif g["status"] == SkillGapStatus.WEAK:
                    weak_skills_norm.add(norm_name)

            # Module 11.1 Integration: Retrieve Quickest Win and Top ROI skills
            try:
                roi_analysis = SkillRoiService.rank_career_skill_rois(career.id, user_id=user_id)
                if roi_analysis.get("quickest_win"):
                    quickest_win_norm = normalize_skill_name(roi_analysis["quickest_win"]["skill_name"])
                for s in roi_analysis.get("ranked_skills", [])[:3]:
                    top_roi_norms.add(normalize_skill_name(s["skill_name"]))
            except Exception:
                pass

        # 3. Score and rank catalog projects
        all_projects = cls.get_all_projects()
        scored_projects = []

        diff_filter_norm = difficulty_filter.strip().lower() if difficulty_filter else None

        for p in all_projects:
            # Apply optional difficulty filter
            if diff_filter_norm and (p.get("difficulty") or "").lower() != diff_filter_norm:
                continue

            match_info = cls.match_project_skills(
                project_skills=p.get("demonstrated_skills", []),
                career_skills=career_skills,
                missing_skills_norm=missing_skills_norm,
                weak_skills_norm=weak_skills_norm
            )

            # Only consider projects that demonstrate at least one relevant skill for the career,
            # or specifically target this career/domain
            is_target_career = career.id in p.get("target_career_ids", [])
            is_target_domain = (p.get("domain") or "").lower() == (career.domain or "").lower()

            if not is_target_career and not is_target_domain and match_info["coverage_count"] == 0:
                continue

            score = cls.calculate_project_score(
                project=p,
                career=career,
                match_info=match_info,
                total_career_skills_count=len(career_skills),
                student_readiness=student_readiness,
                quickest_win_norm=quickest_win_norm,
                top_roi_norms=top_roi_norms,
                is_personalized=is_personalized
            )

            is_qw_addressed = bool(
                quickest_win_norm and
                quickest_win_norm in {normalize_skill_name(s) for s in p.get("demonstrated_skills", [])}
            )

            reason = cls.generate_recommendation_reason(
                project_title=p["title"],
                career_title=career.title,
                covered_skills=match_info["covered_career_skills"],
                missing_addressed=match_info["missing_addressed"],
                weak_addressed=match_info["weak_addressed"],
                is_quickest_win=is_qw_addressed,
                difficulty=p.get("difficulty", "Intermediate")
            )

            scored_projects.append({
                "project_id": p["project_id"],
                "title": p["title"],
                "description": p["description"],
                "domain": p.get("domain", career.domain),
                "difficulty": p.get("difficulty", "Intermediate"),
                "estimated_hours": p.get("estimated_hours", 30),
                "portfolio_value": p.get("portfolio_value", 85),
                "recommendation_score": score,
                "demonstrated_skills": p.get("demonstrated_skills", []),
                "covered_career_skills": match_info["covered_career_skills"],
                "missing_skills_addressed": match_info["missing_addressed"],
                "weak_skills_addressed": match_info["weak_addressed"],
                "addresses_quickest_win": is_qw_addressed,
                "deliverables": p.get("deliverables", []),
                "extension_ideas": p.get("extension_ideas", []),
                "recommendation_reason": reason
            })

        # Deterministic sorting
        scored_projects.sort(
            key=lambda x: (
                -x["recommendation_score"],
                -len(x["missing_skills_addressed"]),
                -x["portfolio_value"],
                x["title"]
            )
        )

        quickest_gap_closer = None
        for sp in scored_projects:
            if sp["addresses_quickest_win"] or len(sp["missing_skills_addressed"]) > 0:
                quickest_gap_closer = sp
                break

        if not quickest_gap_closer and scored_projects:
            quickest_gap_closer = scored_projects[0]

        final_list = scored_projects[:limit] if (limit and limit > 0) else scored_projects

        return {
            "career_id": career.id,
            "career_title": career.title,
            "domain": career.domain,
            "is_personalized": is_personalized,
            "student_readiness": student_readiness,
            "total_projects_count": len(final_list),
            "quickest_gap_closer": quickest_gap_closer,
            "recommendations": final_list
        }
