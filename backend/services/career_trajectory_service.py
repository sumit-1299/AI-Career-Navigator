"""
Multi-Hop Career Trajectory Intelligence Service for AI Career Navigator.
Phase 11 Module 11.5: Multi-Hop Career Trajectory Intelligence.

Models the standardized career ecosystem as a weighted directed graph where:
- Nodes: Careers (10 standardized IT careers)
- Edges: Directed transitions with compatibility and traversal costs.

Supports explainable multi-step career pathway planning answering:
- What careers can a student move into next?
- Which intermediate career best prepares for a long-term target?
- What competencies are targeted at each stage?
- How difficult is each transition?
- How do direct vs multi-hop paths compare?
- Multiple trajectory objectives: BEST_FIT, SHORTEST, LOWEST_EFFORT, MARKET_AWARE.

Integrations:
- Phase 11.1: Skill ROI Engine
- Phase 11.2: Actionable Portfolio & Capstone Projects
- Phase 11.3: Academic Recommendation Benchmarking
- Phase 11.4: Real-Time Industry Trends & Dynamic Skill Demand Weighting

DATA PROVENANCE & TRANSPARENCY:
Sample benchmark data is explicitly labeled:
"DEMO / SAMPLE / PROTOTYPE MARKET BENCHMARK — NOT LIVE LABOR MARKET DATA".
No external graph DB is used; transitions are computed dynamically from relational models.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from collections import deque
from models.career import Career
from models.career_skill import CareerSkill
from models.canonical_skill import CanonicalSkill
from models.skill import Skill
from models.student_profile import StudentProfile
from services.career_transition_service import CareerTransitionService
from services.industry_demand_service import (
    IndustryDemandService,
    INDUSTRY_DEMAND_PROVENANCE,
)
from services.skill_roi_service import SkillRoiService
from services.portfolio_project_service import PortfolioProjectService
from services.academic_benchmark_service import AcademicBenchmarkService
from utils.normalization import normalize_skill_name, strip_parenthetical_qualifiers


SUPPORTED_OBJECTIVES = ["BEST_FIT", "SHORTEST", "LOWEST_EFFORT", "MARKET_AWARE"]


class CareerTrajectoryService:
    """
    Multi-hop career trajectory planning and graph intelligence service.
    """

    @classmethod
    def get_supported_objectives(cls) -> List[str]:
        return SUPPORTED_OBJECTIVES.copy()

    @classmethod
    def _get_all_career_data(cls) -> Tuple[Dict[int, Career], Dict[int, Dict[str, Dict[str, Any]]]]:
        """
        Loads all careers and their skills into in-memory dictionaries
        to avoid repeated database queries during graph traversal.
        """
        careers = Career.query.all()
        career_map: Dict[int, Career] = {c.id: c for c in careers}

        skills_map: Dict[int, Dict[str, Dict[str, Any]]] = {}
        for c in careers:
            skills_map[c.id] = {}
            for cs in c.skills:
                norm_name = normalize_skill_name(cs.skill_name)
                skills_map[c.id][norm_name] = {
                    "skill_name": cs.skill_name,
                    "canonical_skill_id": cs.canonical_skill_id,
                    "required_level": int(cs.required_level or 3),
                    "importance": int(cs.importance or 3),
                }

        return career_map, skills_map

    @classmethod
    def calculate_transition_edge(
        cls,
        source_career_id: int,
        target_career_id: int,
        career_map: Optional[Dict[int, Career]] = None,
        skills_map: Optional[Dict[int, Dict[str, Dict[str, Any]]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Calculates the directed transition edge properties from Career A to Career B.
        Formula:
            Compatibility = 0.40 * Skill Overlap
                          + 0.25 * Transferability
                          + 0.20 * Gap Feasibility
                          + 0.15 * Market Opportunity
            Cost = 1.0 - Compatibility (bounded in [0.0, 1.0])
        """
        if source_career_id == target_career_id:
            return None

        if career_map is None or skills_map is None:
            career_map, skills_map = cls._get_all_career_data()

        source_career = career_map.get(source_career_id)
        target_career = career_map.get(target_career_id)

        if not source_career or not target_career:
            return None

        src_skills = skills_map.get(source_career_id, {})
        tgt_skills = skills_map.get(target_career_id, {})

        if not tgt_skills:
            return None

        total_tgt_count = len(tgt_skills)
        overlap_skills = []
        missing_skills = []
        achieved_points = 0.0
        total_target_points = sum(s["required_level"] for s in tgt_skills.values()) or 1.0
        learning_hours = 0

        for s_norm, t_info in tgt_skills.items():
            t_req = t_info["required_level"]
            t_imp = t_info["importance"]

            if s_norm in src_skills:
                s_info = src_skills[s_norm]
                s_req = s_info["required_level"]
                transfer_level = min(s_req, t_req)
                achieved_points += transfer_level
                level_gap = max(0, t_req - s_req)

                if level_gap > 0:
                    learning_hours += level_gap * 15  # 15 hours per proficiency upgrade level

                overlap_skills.append({
                    "skill_name": t_info["skill_name"],
                    "source_level": s_req,
                    "target_level": t_req,
                    "level_gap": level_gap,
                    "is_transferable": CareerTransitionService.is_transferable(t_info["skill_name"]),
                })
            else:
                missing_skills.append({
                    "skill_name": t_info["skill_name"],
                    "target_level": t_req,
                    "target_importance": t_imp,
                    "is_transferable": CareerTransitionService.is_transferable(t_info["skill_name"]),
                })
                learning_hours += t_req * 20  # 20 hours per new skill level required

        # 1. Skill Overlap [0.0 - 1.0]
        skill_overlap = round(len(overlap_skills) / float(total_tgt_count), 3)

        # 2. Transferability [0.0 - 1.0]
        # Ratio of transferable/satisfied points over total target requirement points
        transferability = round(achieved_points / float(total_target_points), 3)

        # 3. Gap Feasibility [0.0 - 1.0]
        gap_feasibility = round(max(0.0, 1.0 - (len(missing_skills) / float(total_tgt_count))), 3)

        # 4. Market Opportunity [0.0 - 1.0] from Phase 11.4
        market_data = IndustryDemandService.get_skill_market_data(target_career.title)
        # Average demand score of target career required skills
        tgt_demand_scores = [
            IndustryDemandService.get_skill_market_data(s["skill_name"])["demand_score"]
            for s in tgt_skills.values()
        ]
        market_opportunity = round(sum(tgt_demand_scores) / float(len(tgt_demand_scores)), 3) if tgt_demand_scores else 0.50

        # Transition Compatibility Formula
        compatibility = (
            0.40 * skill_overlap +
            0.25 * transferability +
            0.20 * gap_feasibility +
            0.15 * market_opportunity
        )
        compatibility = round(max(0.0, min(1.0, compatibility)), 3)

        # Transition Cost = 1.0 - Compatibility (bounded in [0.0, 1.0])
        transition_cost = round(max(0.0, min(1.0, 1.0 - compatibility)), 3)

        return {
            "from_career_id": source_career_id,
            "from_career_title": source_career.title,
            "to_career_id": target_career_id,
            "to_career_title": target_career.title,
            "skill_overlap": skill_overlap,
            "transferability": transferability,
            "gap_feasibility": gap_feasibility,
            "market_opportunity": market_opportunity,
            "transition_compatibility": compatibility,
            "transition_cost": transition_cost,
            "estimated_learning_hours": learning_hours,
            "overlapping_skills": overlap_skills,
            "missing_skills": missing_skills,
        }

    @classmethod
    def build_career_graph(
        cls,
        career_map: Optional[Dict[int, Career]] = None,
        skills_map: Optional[Dict[int, Dict[str, Dict[str, Any]]]] = None
    ) -> Dict[int, Dict[int, Dict[str, Any]]]:
        """
        Builds the complete in-memory directed graph of career transitions.
        Graph representation:
            graph[u][v] = edge_properties
        """
        if career_map is None or skills_map is None:
            career_map, skills_map = cls._get_all_career_data()

        graph: Dict[int, Dict[int, Dict[str, Any]]] = {}
        c_ids = list(career_map.keys())

        for u in c_ids:
            graph[u] = {}
            for v in c_ids:
                if u != v:
                    edge = cls.calculate_transition_edge(u, v, career_map, skills_map)
                    if edge:
                        graph[u][v] = edge

        return graph

    @classmethod
    def _find_all_simple_paths(
        cls,
        graph: Dict[int, Dict[int, Dict[str, Any]]],
        source_id: int,
        target_id: int,
        max_hops: int = 3
    ) -> List[List[int]]:
        """
        Finds all simple directed paths from source_id to target_id with at most max_hops.
        Strict cycle prevention: no career can be visited more than once in a path.
        """
        max_hops = max(1, min(4, int(max_hops)))
        results: List[List[int]] = []

        def dfs(current_id: int, current_path: List[int], visited: Set[int]):
            if current_id == target_id:
                if len(current_path) > 1:
                    results.append(current_path.copy())
                return

            if len(current_path) - 1 >= max_hops:
                return

            for neighbor_id in graph.get(current_id, {}):
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    current_path.append(neighbor_id)
                    dfs(neighbor_id, current_path, visited)
                    current_path.pop()
                    visited.remove(neighbor_id)

        dfs(source_id, [source_id], {source_id})
        return results

    @classmethod
    def calculate_progressive_skill_reuse(
        cls,
        path: List[int],
        skills_map: Dict[int, Dict[str, Dict[str, Any]]]
    ) -> float:
        """
        Measures the fraction of target skills missing from the source career
        that are developed by intermediate careers in the trajectory.
        Formula:
            Reusable Target Skills / Total Target Skills Missing from Source
        Bounded in [0.0, 1.0]. Direct path has reuse = 0.0.
        """
        if len(path) <= 2:
            return 0.0

        source_id = path[0]
        target_id = path[-1]

        src_skills = set(skills_map.get(source_id, {}).keys())
        tgt_skills = set(skills_map.get(target_id, {}).keys())

        target_missing_from_source = tgt_skills - src_skills
        if not target_missing_from_source:
            return 1.0

        # Collect skills developed in all intermediate stages
        intermediate_skills: Set[str] = set()
        for c_id in path[1:-1]:
            intermediate_skills.update(skills_map.get(c_id, {}).keys())

        developed_for_target = target_missing_from_source.intersection(intermediate_skills)
        reuse_score = len(developed_for_target) / float(len(target_missing_from_source))
        return round(max(0.0, min(1.0, reuse_score)), 3)

    @classmethod
    def evaluate_trajectory(
        cls,
        path: List[int],
        graph: Dict[int, Dict[int, Dict[str, Any]]],
        career_map: Dict[int, Career],
        skills_map: Dict[int, Dict[str, Dict[str, Any]]],
        user_skills_map: Optional[Dict[str, int]] = None,
        project_cache: Optional[Dict[int, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates a complete candidate trajectory path [C_0, C_1, ..., C_k].
        Computes progressive skill acquisition, cumulative hours, ROI,
        and trajectory score.
        """
        hop_count = len(path) - 1
        edges = []
        stages = []
        total_transition_cost = 0.0
        total_compatibility = 0.0
        market_opportunities = []

        # Progressive state tracking:
        # Accumulated competencies start with source career (or user profile)
        accumulated_skills: Dict[str, int] = {}
        if user_skills_map:
            accumulated_skills.update(user_skills_map)
        for s_norm, s_info in skills_map.get(path[0], {}).items():
            accumulated_skills[s_norm] = max(
                accumulated_skills.get(s_norm, 0),
                s_info["required_level"]
            )

        cumulative_learning_hours = 0
        final_target_id = path[-1]
        final_target_skills = skills_map.get(final_target_id, {})

        if project_cache is None:
            project_cache = {}

        for i in range(hop_count):
            u = path[i]
            v = path[i + 1]
            edge = graph.get(u, {}).get(v)
            if not edge:
                edge = cls.calculate_transition_edge(u, v, career_map, skills_map) or {}

            edges.append(edge)
            compat = edge.get("transition_compatibility", 0.5)
            cost = edge.get("transition_cost", 0.5)
            total_compatibility += compat
            total_transition_cost += cost
            market_opportunities.append(edge.get("market_opportunity", 0.5))

            # Progressive learning hours for this stage against accumulated competencies
            v_skills = skills_map.get(v, {})
            stage_hours = 0
            skills_targeted_at_stage = []

            for s_norm, v_info in v_skills.items():
                v_req = v_info["required_level"]
                curr_level = accumulated_skills.get(s_norm, 0)
                gap = max(0, v_req - curr_level)

                if gap > 0:
                    skills_targeted_at_stage.append({
                        "skill_name": v_info["skill_name"],
                        "target_level": v_req,
                        "current_level": curr_level,
                        "level_gap": gap,
                        "is_target_competency": s_norm in final_target_skills,
                    })
                    if curr_level == 0:
                        stage_hours += v_req * 20
                    else:
                        stage_hours += gap * 15

                # Update accumulated competencies after this stage
                accumulated_skills[s_norm] = max(curr_level, v_req)

            cumulative_learning_hours += stage_hours

            # Remaining target gaps after this stage
            remaining_target_gaps = [
                t_info["skill_name"] for t_norm, t_info in final_target_skills.items()
                if accumulated_skills.get(t_norm, 0) < t_info["required_level"]
            ]

            # Recommended capstone project for this transition (cached)
            if v in project_cache:
                stage_project = project_cache[v]
            else:
                stage_project = None
                try:
                    p_recs = PortfolioProjectService.recommend_projects_for_career(career_id=v, limit=1)
                    proj_list = p_recs.get("recommendations") or p_recs.get("recommended_projects")
                    if proj_list:
                        p = proj_list[0]
                        stage_project = {
                            "project_id": p.get("project_id"),
                            "title": p.get("title"),
                            "difficulty": p.get("difficulty"),
                            "estimated_hours": p.get("estimated_hours"),
                        }
                except Exception:
                    pass
                project_cache[v] = stage_project

            stages.append({
                "stage_number": i + 1,
                "from_career_id": u,
                "from_career_title": career_map[u].title,
                "to_career_id": v,
                "to_career_title": career_map[v].title,
                "transition_compatibility": compat,
                "transition_cost": cost,
                "stage_learning_hours": stage_hours,
                "skills_targeted": skills_targeted_at_stage,
                "remaining_target_gaps": remaining_target_gaps,
                "recommended_project": stage_project,
            })

        avg_compatibility = round(total_compatibility / float(hop_count), 3) if hop_count else 1.0
        total_transition_cost = round(total_transition_cost, 3)
        avg_market_opportunity = round(sum(market_opportunities) / float(len(market_opportunities)), 3) if market_opportunities else 0.50

        # Effort feasibility [0.0 - 1.0]
        effort_feasibility = round(max(0.0, min(1.0, 1.0 - (cumulative_learning_hours / 500.0))), 3)

        # Progressive skill reuse [0.0 - 1.0]
        progressive_reuse = cls.calculate_progressive_skill_reuse(path, skills_map)

        # Trajectory Score Formula
        # 0.40 * Compatibility + 0.25 * Effort Feasibility + 0.20 * Progressive Reuse + 0.15 * Market Opportunity
        # For direct transition (hop_count == 1), reuse weight is distributed to compatibility
        if hop_count == 1:
            traj_score = (
                0.55 * avg_compatibility +
                0.30 * effort_feasibility +
                0.15 * avg_market_opportunity
            )
        else:
            traj_score = (
                0.40 * avg_compatibility +
                0.25 * effort_feasibility +
                0.20 * progressive_reuse +
                0.15 * avg_market_opportunity
            )
        traj_score = round(max(0.0, min(1.0, traj_score)), 3)

        # Market-aware specific score
        market_aware_score = round(
            0.50 * avg_market_opportunity +
            0.30 * avg_compatibility +
            0.20 * (progressive_reuse if hop_count > 1 else effort_feasibility),
            3
        )

        return {
            "path": path,
            "careers": [career_map[cid].title for cid in path],
            "career_ids": path,
            "hop_count": hop_count,
            "total_transition_cost": total_transition_cost,
            "average_compatibility": avg_compatibility,
            "estimated_learning_hours": cumulative_learning_hours,
            "progressive_skill_reuse": progressive_reuse,
            "market_opportunity_score": avg_market_opportunity,
            "trajectory_score": traj_score,
            "market_aware_score": market_aware_score,
            "stages": stages,
        }

    @classmethod
    def _rank_trajectories(
        cls,
        evaluated_paths: List[Dict[str, Any]],
        objective: str
    ) -> List[Dict[str, Any]]:
        """
        Ranks evaluated trajectories according to the specified objective.
        Supported objectives:
        - BEST_FIT: Highest overall trajectory_score
        - SHORTEST: Fewest career transitions (hop_count ASC, trajectory_score DESC)
        - LOWEST_EFFORT: Lowest estimated learning hours (hours ASC, trajectory_score DESC)
        - MARKET_AWARE: Highest market-aware composite score
        """
        obj = objective.strip().upper() if objective else "BEST_FIT"
        if obj not in SUPPORTED_OBJECTIVES:
            obj = "BEST_FIT"

        if obj == "SHORTEST":
            return sorted(
                evaluated_paths,
                key=lambda p: (p["hop_count"], -p["trajectory_score"], p["estimated_learning_hours"])
            )
        elif obj == "LOWEST_EFFORT":
            return sorted(
                evaluated_paths,
                key=lambda p: (p["estimated_learning_hours"], -p["trajectory_score"], p["hop_count"])
            )
        elif obj == "MARKET_AWARE":
            return sorted(
                evaluated_paths,
                key=lambda p: (-p["market_aware_score"], -p["trajectory_score"], p["hop_count"])
            )
        else:  # BEST_FIT
            return sorted(
                evaluated_paths,
                key=lambda p: (-p["trajectory_score"], -p["average_compatibility"], p["hop_count"])
            )

    @classmethod
    def _generate_trajectory_explanation(
        cls,
        recommended: Dict[str, Any],
        direct: Dict[str, Any],
        objective: str
    ) -> str:
        """
        Generates clear, deterministic, explainable rationale for the trajectory recommendation.
        """
        hop_count = recommended["hop_count"]
        careers = recommended["careers"]
        src_title = careers[0]
        tgt_title = careers[-1]

        if hop_count == 1:
            return (
                f"A direct transition from {src_title} to {tgt_title} is recommended because "
                f"it provides a high compatibility score ({round(recommended['average_compatibility'] * 100, 1)}%) "
                f"with approximately {recommended['estimated_learning_hours']} hours of targeted learning, "
                f"making an intermediate career step unnecessary."
            )

        intermediate_names = ", ".join(careers[1:-1])
        diff_hours = direct["estimated_learning_hours"] - recommended["estimated_learning_hours"]
        reuse_pct = round(recommended["progressive_skill_reuse"] * 100, 1)

        reasons = []
        reasons.append(
            f"Transitioning from {src_title} to {tgt_title} via intermediate role(s) ({intermediate_names}) "
            f"provides a structured {hop_count}-stage progression."
        )

        if reuse_pct > 0:
            reasons.append(
                f"The intermediate role develops {reuse_pct}% of the competencies required by {tgt_title} "
                f"that are absent from {src_title}."
            )

        if diff_hours > 0:
            reasons.append(
                f"This progressive path saves approximately {diff_hours} hours of steep upfront preparation "
                f"compared to attempting a direct transition ({recommended['estimated_learning_hours']}h vs {direct['estimated_learning_hours']}h)."
            )
        else:
            reasons.append(
                f"While requiring {recommended['estimated_learning_hours']} total hours across stages, "
                f"each individual transition maintains higher feasibility (avg compatibility: {round(recommended['average_compatibility'] * 100, 1)}%)."
            )

        if objective == "MARKET_AWARE":
            reasons.append(
                f"Ranked under Market-Aware objective with strong industry growth and demand velocity "
                f"(market opportunity score: {recommended['market_opportunity_score']})."
            )

        return " ".join(reasons)

    @classmethod
    def find_trajectory(
        cls,
        target_career_id: int,
        from_career_id: Optional[int] = None,
        objective: str = "BEST_FIT",
        max_hops: int = 3,
        user_id: Optional[int] = None,
        limit: int = 3
    ) -> Dict[str, Any]:
        """
        Main entry point for multi-hop career trajectory intelligence.
        Calculates direct vs multi-hop candidate paths, applies objectives,
        and provides rich explainable comparisons.
        """
        # Validate target career
        target_career = Career.query.get(target_career_id)
        if not target_career:
            return {"error": "TARGET_CAREER_NOT_FOUND", "message": f"Target career with id {target_career_id} not found"}

        career_map, skills_map = cls._get_all_career_data()

        # Resolve student context if user_id provided
        is_personalized = False
        user_skills_map: Dict[str, int] = {}
        if user_id:
            try:
                user_skills = Skill.query.filter_by(user_id=user_id).all()
                if user_skills:
                    is_personalized = True
                    for us in user_skills:
                        if us.skill_name:
                            norm_name = normalize_skill_name(us.skill_name)
                            user_skills_map[norm_name] = max(
                                user_skills_map.get(norm_name, 0),
                                int(us.proficiency or 0)
                            )
            except Exception:
                pass

        # Determine source career ID
        if from_career_id is None:
            # If authenticated, attempt to infer closest matching career, otherwise default to career 1
            if from_career_id is None:
                # Default to Full Stack Developer (id 1) or another baseline if target is 1
                from_career_id = 1 if target_career_id != 1 else 8

        source_career = career_map.get(from_career_id)
        if not source_career:
            return {"error": "SOURCE_CAREER_NOT_FOUND", "message": f"Source career with id {from_career_id} not found"}

        # Edge case: Source == Target
        if source_career_id := from_career_id:
            if source_career_id == target_career_id:
                return {
                    "source_career": {
                        "id": source_career.id,
                        "title": source_career.title,
                        "domain": source_career.domain,
                    },
                    "target_career": {
                        "id": target_career.id,
                        "title": target_career.title,
                        "domain": target_career.domain,
                    },
                    "objective": objective,
                    "is_personalized": is_personalized,
                    "is_identical_career": True,
                    "provenance": INDUSTRY_DEMAND_PROVENANCE,
                    "direct_transition": {
                        "compatibility": 1.0,
                        "transition_cost": 0.0,
                        "estimated_learning_hours": 0,
                    },
                    "recommended_trajectory": {
                        "careers": [source_career.title],
                        "career_ids": [source_career.id],
                        "hop_count": 0,
                        "trajectory_score": 1.0,
                        "estimated_learning_hours": 0,
                        "stages": [],
                    },
                    "alternative_trajectories": [],
                    "comparison": {
                        "is_multihop_better": False,
                        "estimated_hours_saved": 0,
                        "summary": "Source and target careers are identical. No transition required.",
                    },
                    "explanation": f"You are already exploring {target_career.title}. No career transitions are necessary.",
                }

        # Build graph
        graph = cls.build_career_graph(career_map, skills_map)

        # Direct transition edge evaluation
        direct_edge = graph.get(from_career_id, {}).get(target_career_id)
        if not direct_edge:
            direct_edge = cls.calculate_transition_edge(from_career_id, target_career_id, career_map, skills_map) or {}

        project_cache: Dict[int, Any] = {}
        direct_evaluated = cls.evaluate_trajectory(
            path=[from_career_id, target_career_id],
            graph=graph,
            career_map=career_map,
            skills_map=skills_map,
            user_skills_map=user_skills_map if is_personalized else None,
            project_cache=project_cache
        )

        # Multi-hop path search (max_hops clamped 1-4)
        clamped_max_hops = max(1, min(4, int(max_hops or 3)))
        all_paths = cls._find_all_simple_paths(graph, from_career_id, target_career_id, clamped_max_hops)

        evaluated_trajectories = [
            cls.evaluate_trajectory(
                path=p,
                graph=graph,
                career_map=career_map,
                skills_map=skills_map,
                user_skills_map=user_skills_map if is_personalized else None,
                project_cache=project_cache
            )
            for p in all_paths
        ]

        if not evaluated_trajectories:
            evaluated_trajectories = [direct_evaluated]

        # Rank trajectories
        ranked_trajectories = cls._rank_trajectories(evaluated_trajectories, objective)

        recommended = ranked_trajectories[0]
        alternatives = ranked_trajectories[1:limit + 1]

        # Direct vs Multi-Hop Comparison
        is_multihop = recommended["hop_count"] > 1
        hours_saved = max(0, direct_evaluated["estimated_learning_hours"] - recommended["estimated_learning_hours"])

        comparison_summary = (
            f"Multi-hop trajectory via {', '.join(recommended['careers'][1:-1])} provides higher structured feasibility "
            f"and saves ~{hours_saved} hours of direct skill friction."
            if is_multihop and hours_saved > 0 else
            "Direct transition provides the most direct and efficient route."
            if not is_multihop else
            f"Multi-hop trajectory provides lower per-hop friction through {', '.join(recommended['careers'][1:-1])}."
        )

        explanation = cls._generate_trajectory_explanation(recommended, direct_evaluated, objective)

        return {
            "source_career": {
                "id": source_career.id,
                "title": source_career.title,
                "domain": source_career.domain,
            },
            "target_career": {
                "id": target_career.id,
                "title": target_career.title,
                "domain": target_career.domain,
            },
            "objective": objective.upper() if objective in SUPPORTED_OBJECTIVES else "BEST_FIT",
            "supported_objectives": SUPPORTED_OBJECTIVES,
            "max_hops_requested": clamped_max_hops,
            "is_personalized": is_personalized,
            "is_identical_career": False,
            "provenance": INDUSTRY_DEMAND_PROVENANCE,
            "direct_transition": {
                "compatibility": direct_evaluated["average_compatibility"],
                "transition_cost": direct_evaluated["total_transition_cost"],
                "estimated_learning_hours": direct_evaluated["estimated_learning_hours"],
                "missing_skills_count": len(direct_edge.get("missing_skills", [])),
            },
            "recommended_trajectory": recommended,
            "alternative_trajectories": alternatives,
            "total_candidate_trajectories_found": len(ranked_trajectories),
            "comparison": {
                "is_multihop_better": is_multihop and (hours_saved > 0 or recommended["trajectory_score"] > direct_evaluated["trajectory_score"]),
                "estimated_hours_saved": hours_saved,
                "summary": comparison_summary,
            },
            "explanation": explanation,
        }
