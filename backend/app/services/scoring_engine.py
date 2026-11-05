import re
from typing import Dict, Any, List, Tuple
from app.models.candidate import Candidate
from app.models.requisition import JobScorecard


class DeterministicScoringEngine:
    @staticmethod
    def extract_evidence_quote(text: str, search_terms: List[str]) -> str:
        """
        Finds the exact sentence or line in the CV raw text that mentions
        any of the search terms.
        If no exact mention exists, returns 'Evidence not found'.
        Strict rule: Never generate fake quotations!
        """
        if not text:
            return "Evidence not found"

        sentences = re.split(r"(?<=[.!?\n])\s+", text)
        matched_sentences = []

        for term in search_terms:
            pattern = re.compile(rf"\b{re.escape(term.strip())}\b", re.IGNORECASE)
            for s in sentences:
                clean_s = s.strip()
                if pattern.search(clean_s) and clean_s not in matched_sentences:
                    matched_sentences.append(clean_s)
                    if len(matched_sentences) >= 2:
                        break
            if len(matched_sentences) >= 2:
                break

        if matched_sentences:
            return " \" " + " ... ".join(matched_sentences[:2]) + " \" "
        return "Evidence not found"

    @classmethod
    def calculate_candidate_score(
        cls,
        candidate: Candidate,
        scorecard: JobScorecard,
        override_weights: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Deterministically calculate candidate score against job scorecard.
        Strict Fairness Guarantee:
        Candidate name, gender, age, photo, marital status, religion, caste, etc.
        are strictly EXCLUDED from evaluation.
        Only job-related criteria are computed.
        """
        raw_text = candidate.raw_text or ""
        candidate_skills = [s.strip().lower() for s in (candidate.skills or [])]

        # Weights configuration
        weights = override_weights or scorecard.weights or {
            "required_skills": 40.0,
            "experience_match": 25.0,
            "relevant_experience": 15.0,
            "good_to_have_skills": 10.0,
            "notice_period": 10.0
        }

        req_skills_weight = float(weights.get("required_skills", 40.0))
        exp_match_weight = float(weights.get("experience_match", 25.0))
        rel_exp_weight = float(weights.get("relevant_experience", 15.0))
        good_skills_weight = float(weights.get("good_to_have_skills", 10.0))
        notice_weight = float(weights.get("notice_period", 10.0))

        must_have = scorecard.must_have_skills or []
        good_to_have = scorecard.good_to_have_skills or []
        min_exp = float(scorecard.min_experience or 0.0)
        max_exp = float(scorecard.max_experience or 10.0)
        max_notice = int(scorecard.max_notice_period or 60)

        evidence_items = []

        # -------------------------------------------------------------
        # 1. Required Skills Evaluation (Max: req_skills_weight pts)
        # -------------------------------------------------------------
        matching_req_skills = []
        missing_req_skills = []

        for skill in must_have:
            skill_lower = skill.strip().lower()
            # Check candidate skills list or exact mention in CV text
            in_skills = any(skill_lower in cs or cs in skill_lower for cs in candidate_skills)
            in_text = bool(re.search(rf"\b{re.escape(skill.strip())}\b", raw_text, re.IGNORECASE))
            if in_skills or in_text:
                matching_req_skills.append(skill)
            else:
                missing_req_skills.append(skill)

        if must_have:
            req_ratio = len(matching_req_skills) / len(must_have)
            req_score = round(req_ratio * req_skills_weight, 2)
        else:
            req_score = req_skills_weight

        req_evidence = cls.extract_evidence_quote(raw_text, matching_req_skills) if matching_req_skills else "Evidence not found"
        missing_req_text = f"Missing required skills: {', '.join(missing_req_skills)}" if missing_req_skills else None

        evidence_items.append({
            "criterion_name": "Required Must-Have Skills",
            "max_score": req_skills_weight,
            "awarded_score": req_score,
            "evidence_quote": req_evidence,
            "explanation": f"Candidate possesses {len(matching_req_skills)} of {len(must_have)} must-have skills ({', '.join(matching_req_skills) if matching_req_skills else 'None'}).",
            "missing_info": missing_req_text
        })

        # -------------------------------------------------------------
        # 2. Experience Match (Max: exp_match_weight pts)
        # -------------------------------------------------------------
        total_exp = float(candidate.total_experience_years or 0.0)
        if total_exp >= min_exp:
            exp_score = exp_match_weight
            exp_explanation = f"Candidate has {total_exp} years total experience, satisfying the requirement of {min_exp} to {max_exp} years."
            exp_missing = None
        else:
            ratio = total_exp / max(min_exp, 1.0)
            exp_score = round(ratio * exp_match_weight, 2)
            shortfall = round(min_exp - total_exp, 1)
            exp_explanation = f"Candidate has {total_exp} years total experience, falling short by {shortfall} years of the minimum {min_exp} years."
            exp_missing = f"Shortfall of {shortfall} years experience"

        exp_evidence = cls.extract_evidence_quote(raw_text, ["experience", "years", "total", "career"])
        evidence_items.append({
            "criterion_name": "Total Experience Match",
            "max_score": exp_match_weight,
            "awarded_score": exp_score,
            "evidence_quote": exp_evidence,
            "explanation": exp_explanation,
            "missing_info": exp_missing
        })

        # -------------------------------------------------------------
        # 3. Relevant Experience (Max: rel_exp_weight pts)
        # -------------------------------------------------------------
        rel_exp = float(candidate.relevant_experience_years or max(0.0, total_exp - 1.0))
        if rel_exp >= min_exp:
            rel_score = rel_exp_weight
            rel_explanation = f"Candidate has {rel_exp} years of directly relevant domain experience (exceeds or meets {min_exp} years min)."
            rel_missing = None
        else:
            rel_ratio = rel_exp / max(min_exp, 1.0)
            rel_score = round(rel_ratio * rel_exp_weight, 2)
            rel_explanation = f"Candidate has {rel_exp} years relevant experience vs {min_exp} years requested."
            rel_missing = f"Relevant experience {rel_exp} yrs is lower than required {min_exp} yrs"

        rel_evidence = cls.extract_evidence_quote(raw_text, [candidate.current_role or "developer", "engineer", "lead", "analyst"])
        evidence_items.append({
            "criterion_name": "Relevant Domain Experience",
            "max_score": rel_exp_weight,
            "awarded_score": rel_score,
            "evidence_quote": rel_evidence,
            "explanation": rel_explanation,
            "missing_info": rel_missing
        })

        # -------------------------------------------------------------
        # 4. Good-to-Have Skills (Max: good_skills_weight pts)
        # -------------------------------------------------------------
        matching_good_skills = []
        missing_good_skills = []
        for skill in good_to_have:
            skill_lower = skill.strip().lower()
            in_skills = any(skill_lower in cs or cs in skill_lower for cs in candidate_skills)
            in_text = bool(re.search(rf"\b{re.escape(skill.strip())}\b", raw_text, re.IGNORECASE))
            if in_skills or in_text:
                matching_good_skills.append(skill)
            else:
                missing_good_skills.append(skill)

        if good_to_have:
            good_ratio = len(matching_good_skills) / len(good_to_have)
            good_score = round(good_ratio * good_skills_weight, 2)
        else:
            good_score = good_skills_weight

        good_evidence = cls.extract_evidence_quote(raw_text, matching_good_skills) if matching_good_skills else "Evidence not found"
        evidence_items.append({
            "criterion_name": "Good-to-Have Skills",
            "max_score": good_skills_weight,
            "awarded_score": good_score,
            "evidence_quote": good_evidence,
            "explanation": f"Matched {len(matching_good_skills)} of {len(good_to_have)} secondary skills ({', '.join(matching_good_skills) if matching_good_skills else 'None'}).",
            "missing_info": f"Missing: {', '.join(missing_good_skills)}" if missing_good_skills else None
        })

        # -------------------------------------------------------------
        # 5. Notice Period Match (Max: notice_weight pts)
        # -------------------------------------------------------------
        notice_days = int(candidate.notice_period_days or 30)
        if notice_days <= max_notice:
            notice_score = notice_weight
            notice_explanation = f"Notice period is {notice_days} days, well within the {max_notice} days threshold."
            notice_missing = None
        else:
            # Graded deduction
            excess = notice_days - max_notice
            deduction = min(notice_weight, (excess / 30.0) * (notice_weight * 0.5))
            notice_score = round(max(0.0, notice_weight - deduction), 2)
            notice_explanation = f"Notice period of {notice_days} days exceeds client requirement of {max_notice} days."
            notice_missing = f"Exceeds notice limit by {excess} days"

        notice_evidence = cls.extract_evidence_quote(raw_text, ["notice", "days", "immediate", "serving"])
        evidence_items.append({
            "criterion_name": "Notice Period Availability",
            "max_score": notice_weight,
            "awarded_score": notice_score,
            "evidence_quote": notice_evidence,
            "explanation": notice_explanation,
            "missing_info": notice_missing
        })

        # Total Deterministic Score
        total_score = round(req_score + exp_score + rel_score + good_score + notice_score, 1)

        # Match Grade
        if total_score >= 80.0:
            match_grade = "High Match"
        elif total_score >= 50.0:
            match_grade = "Moderate Match"
        else:
            match_grade = "Low Match"

        reasoning = (
            f"Candidate achieved a total deterministic match score of {total_score}/100. "
            f"Required Skills: {req_score}/{req_skills_weight} pts; "
            f"Experience: {exp_score}/{exp_match_weight} pts; "
            f"Relevant Exp: {rel_score}/{rel_exp_weight} pts; "
            f"Good-to-have: {good_score}/{good_skills_weight} pts; "
            f"Notice Period: {notice_score}/{notice_weight} pts. "
            f"Strict algorithmic evaluation based only on verified qualifications."
        )

        return {
            "total_score": total_score,
            "max_possible_score": 100.0,
            "required_skills_score": req_score,
            "experience_score": exp_score,
            "relevant_experience_score": rel_score,
            "good_to_have_score": good_score,
            "notice_period_score": notice_score,
            "matching_skills": matching_req_skills + matching_good_skills,
            "missing_skills": missing_req_skills,
            "match_grade": match_grade,
            "ai_reasoning": reasoning,
            "evidence_items": evidence_items
        }

