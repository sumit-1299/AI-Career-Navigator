"""
Learning Progress Tracking Service for AI Career Navigator.

Manages persistent tracking of student progress across curated learning resources.
Updates student skill proficiency upon verified resource completion.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from extensions import db
from models.canonical_skill import CanonicalSkill
from models.learning_resource import LearningResource
from models.skill import Skill
from models.user_learning_progress import UserLearningProgress
from utils.normalization import normalize_skill_name


class LearningProgressService:
    """Service managing student learning resource progress and skill advancement."""

    @staticmethod
    def _calculate_skill_proficiency_boost(
        difficulty_level: str,
        current_proficiency: Optional[int]
    ) -> int:
        """
        Calculates resulting skill proficiency (1-10 scale) after completing a resource.
        - Beginner: base 5 (or +1 if already >= 5, clamped at 10)
        - Intermediate: base 7 (or +1 if already >= 7, clamped at 10)
        - Advanced: base 9 (or +1 if already >= 9, clamped at 10)
        """
        diff = (difficulty_level or "Beginner").lower()
        if "adv" in diff:
            target = 9
        elif "inter" in diff:
            target = 7
        else:
            target = 5

        if current_proficiency is None or current_proficiency <= 0:
            return target
        elif current_proficiency < target:
            return target
        else:
            return min(10, current_proficiency + 1)

    @classmethod
    def start_resource(
        cls,
        user_id: int,
        learning_resource_id: int
    ) -> Dict[str, Any]:
        """
        Begins tracking a learning resource for a student.
        Idempotent: returns existing record if already started.
        """
        resource = LearningResource.query.get(learning_resource_id)
        if not resource:
            raise ValueError(f"Learning resource {learning_resource_id} not found")

        progress = UserLearningProgress.query.filter_by(
            user_id=user_id,
            learning_resource_id=learning_resource_id
        ).first()

        if progress:
            if progress.status == "Not Started":
                progress.status = "In Progress"
                progress.started_at = datetime.utcnow()
                db.session.commit()
            return progress.to_dict()

        progress = UserLearningProgress(
            user_id=user_id,
            learning_resource_id=learning_resource_id,
            canonical_skill_id=resource.canonical_skill_id,
            status="In Progress",
            progress_percentage=5.0,  # Starting baseline
            started_at=datetime.utcnow()
        )
        db.session.add(progress)
        db.session.commit()
        return progress.to_dict()

    @classmethod
    def update_progress(
        cls,
        user_id: int,
        learning_resource_id: int,
        progress_percentage: float,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Updates the progress percentage and optional notes for a resource.
        If percentage reaches 100%, triggers completion.
        """
        progress = UserLearningProgress.query.filter_by(
            user_id=user_id,
            learning_resource_id=learning_resource_id
        ).first()

        if not progress:
            # Auto-start if not previously started
            cls.start_resource(user_id, learning_resource_id)
            progress = UserLearningProgress.query.filter_by(
                user_id=user_id,
                learning_resource_id=learning_resource_id
            ).first()

        clamped_pct = max(0.0, min(100.0, float(progress_percentage)))
        progress.progress_percentage = clamped_pct
        progress.last_updated = datetime.utcnow()

        if notes is not None:
            progress.notes = notes

        if clamped_pct >= 100.0:
            return cls.complete_resource(user_id, learning_resource_id)

        if clamped_pct > 0.0 and progress.status != "Completed":
            progress.status = "In Progress"

        db.session.commit()
        return progress.to_dict()

    @classmethod
    def complete_resource(
        cls,
        user_id: int,
        learning_resource_id: int
    ) -> Dict[str, Any]:
        """
        Marks a learning resource as Completed and updates the student's skill proficiency.
        """
        resource = LearningResource.query.get(learning_resource_id)
        if not resource:
            raise ValueError(f"Learning resource {learning_resource_id} not found")

        progress = UserLearningProgress.query.filter_by(
            user_id=user_id,
            learning_resource_id=learning_resource_id
        ).first()

        already_completed = (progress is not None and progress.status == "Completed")

        if not progress:
            progress = UserLearningProgress(
                user_id=user_id,
                learning_resource_id=learning_resource_id,
                canonical_skill_id=resource.canonical_skill_id,
                started_at=datetime.utcnow()
            )
            db.session.add(progress)

        progress.status = "Completed"
        progress.progress_percentage = 100.0
        if not progress.completed_at:
            progress.completed_at = datetime.utcnow()
        progress.last_updated = datetime.utcnow()

        # Update student's Skill proficiency in database
        canonical_skill = resource.canonical_skill
        skill_update_info = None

        if canonical_skill:
            # Check existing skill by canonical_skill_id or normalized name
            norm_name = normalize_skill_name(canonical_skill.canonical_name)
            student_skill = Skill.query.filter_by(
                user_id=user_id,
                canonical_skill_id=canonical_skill.id
            ).first()

            if not student_skill:
                # Fallback check by skill_name
                skills = Skill.query.filter_by(user_id=user_id).all()
                for s in skills:
                    if normalize_skill_name(s.skill_name) == norm_name:
                        student_skill = s
                        break

            if already_completed:
                skill_update_info = {
                    "action": "already_boosted",
                    "skill_name": student_skill.skill_name if student_skill else canonical_skill.canonical_name,
                    "previous_proficiency": student_skill.proficiency if student_skill else 0,
                    "new_proficiency": student_skill.proficiency if student_skill else 0,
                    "duplicate_boost_prevented": True
                }
            else:
                prev_prof = student_skill.proficiency if student_skill else 0
                new_prof = cls._calculate_skill_proficiency_boost(
                    resource.difficulty_level,
                    prev_prof
                )

                if student_skill:
                    student_skill.proficiency = new_prof
                    if not student_skill.canonical_skill_id:
                        student_skill.canonical_skill_id = canonical_skill.id
                    skill_update_info = {
                        "action": "updated",
                        "skill_name": student_skill.skill_name,
                        "previous_proficiency": prev_prof,
                        "new_proficiency": new_prof,
                        "duplicate_boost_prevented": False
                    }
                else:
                    new_skill = Skill(
                        user_id=user_id,
                        skill_name=canonical_skill.canonical_name,
                        proficiency=new_prof,
                        canonical_skill_id=canonical_skill.id
                    )
                    db.session.add(new_skill)
                    skill_update_info = {
                        "action": "created",
                        "skill_name": canonical_skill.canonical_name,
                        "previous_proficiency": 0,
                        "new_proficiency": new_prof,
                        "duplicate_boost_prevented": False
                    }

        db.session.commit()

        result = progress.to_dict()
        result["skill_advancement"] = skill_update_info
        return result

    @classmethod
    def get_user_progress(
        cls,
        user_id: int,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves learning progress records for a student."""
        query = UserLearningProgress.query.filter_by(user_id=user_id)
        if status:
            query = query.filter(UserLearningProgress.status.ilike(status))

        records = query.order_by(UserLearningProgress.last_updated.desc()).all()
        return [r.to_dict() for r in records]

    @classmethod
    def get_progress_for_skill(
        cls,
        user_id: int,
        canonical_skill_id: int
    ) -> List[Dict[str, Any]]:
        """Retrieves progress for resources associated with a specific canonical skill."""
        records = UserLearningProgress.query.filter_by(
            user_id=user_id,
            canonical_skill_id=canonical_skill_id
        ).order_by(UserLearningProgress.last_updated.desc()).all()

        return [r.to_dict() for r in records]
