"""
Services package for AI Career Navigator.
"""

from services.skill_gap_service import (
    SkillGapService,
    assess_career_skill_gap,
)
from services.roadmap_service import (
    RoadmapService,
    generate_learning_roadmap,
)
from services.learning_resource_service import LearningResourceService
from services.career_recommendation_service import CareerRecommendationService
from services.career_transition_service import CareerTransitionService
from services.learning_progress_service import LearningProgressService
from services.resume_extraction_service import ResumeExtractionService
from services.career_comparison_service import CareerComparisonService
from services.student_analytics_service import StudentAnalyticsService
from services.skill_roi_service import SkillRoiService
from services.portfolio_project_service import PortfolioProjectService
from services.academic_benchmark_service import AcademicBenchmarkService
from services.industry_demand_service import IndustryDemandService
from services.career_trajectory_service import CareerTrajectoryService
from services.interview_simulation_service import InterviewSimulationService
from services.recommendation_evaluation_service import (
    RecommendationEvaluationService,
    EvaluationSkill,
)
from services.job_action_center_service import JobActionCenterService
from services.practical_task_service import PracticalTaskService

__all__ = [
    "SkillGapService",
    "assess_career_skill_gap",
    "RoadmapService",
    "generate_learning_roadmap",
    "LearningResourceService",
    "CareerRecommendationService",
    "CareerTransitionService",
    "LearningProgressService",
    "ResumeExtractionService",
    "CareerComparisonService",
    "StudentAnalyticsService",
    "SkillRoiService",
    "PortfolioProjectService",
    "AcademicBenchmarkService",
    "IndustryDemandService",
    "CareerTrajectoryService",
    "InterviewSimulationService",
    "RecommendationEvaluationService",
    "EvaluationSkill",
    "JobActionCenterService",
    "PracticalTaskService",
]
