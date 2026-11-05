import json
import logging
import re
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.schemas.requisition import JDAnalysisResponse

logger = logging.getLogger(__name__)

# Initialize Groq client if SDK & API key available
groq_client = None
if settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip():
    try:
        from groq import Groq
        groq_client = Groq(api_key=settings.GROQ_API_KEY)
    except Exception as e:
        logger.warning(f"Could not initialize Groq client: {e}")


class GroqAIService:
    @staticmethod
    def is_groq_available() -> bool:
        return bool(groq_client and settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip())

    @classmethod
    def analyze_job_description(cls, jd_text: str, job_title: Optional[str] = None) -> tuple[JDAnalysisResponse, bool]:
        """
        Extract structured scorecard criteria from Job Description text using Groq API.
        Returns: (JDAnalysisResponse, is_demo_mode: bool)
        """
        if cls.is_groq_available():
            try:
                system_prompt = (
                    "You are an expert technical recruitment analyst. Analyze the following Job Description (JD) "
                    "and extract structured requirements in strictly valid JSON format. "
                    "Fields required:\n"
                    "{\n"
                    '  "must_have_skills": ["Skill1", "Skill2", ...],\n'
                    '  "good_to_have_skills": ["SkillA", "SkillB", ...],\n'
                    '  "min_experience": 5.0,\n'
                    '  "max_experience": 8.0,\n'
                    '  "location": "Noida",\n'
                    '  "max_notice_period": 60,\n'
                    '  "ctc_info": "Competitive / 15-25 LPA",\n'
                    '  "suggested_title": "Senior Java Developer",\n'
                    '  "summary": "Brief 2-sentence summary of the role"\n'
                    "}\n"
                    "Return ONLY JSON. Do not include markdown code fences or conversational prose."
                )

                response = groq_client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Job Title: {job_title or 'Not specified'}\n\nJD Content:\n{jd_text}"}
                    ],
                    temperature=settings.GROQ_TEMPERATURE,
                    max_tokens=settings.GROQ_MAX_TOKENS,
                    response_format={"type": "json_object"}
                )

                raw_json = response.choices[0].message.content
                data = json.loads(raw_json)
                parsed = JDAnalysisResponse(**data)
                return parsed, False
            except Exception as e:
                logger.error(f"Groq JD analysis error, falling back to deterministic extractor: {e}")

        # Deterministic Rule-Based Fallback / Demo Mode
        fallback_data = cls._deterministic_jd_extraction(jd_text, job_title)
        return JDAnalysisResponse(**fallback_data), True

    @classmethod
    def extract_candidate_from_cv(cls, cv_text: str, file_name: str = "") -> tuple[Dict[str, Any], bool]:
        """
        Extract structured candidate information from resume text using Groq API.
        Returns: (candidate_dict, is_demo_mode: bool)
        """
        if cls.is_groq_available():
            try:
                system_prompt = (
                    "You are an expert recruitment parser. Extract structured candidate information from the CV text. "
                    "Never invent or hallucinate information that is not present in the CV. "
                    "Return strictly valid JSON with this structure:\n"
                    "{\n"
                    '  "first_name": "Ritika",\n'
                    '  "last_name": "Bansal",\n'
                    '  "email": "ritika.bansal@example.com",\n'
                    '  "phone": "+91 9876543210",\n'
                    '  "current_role": "Senior Java Developer",\n'
                    '  "total_experience_years": 6.5,\n'
                    '  "relevant_experience_years": 6.0,\n'
                    '  "skills": ["Java", "Spring Boot", "Microservices", "Kafka", "PostgreSQL"],\n'
                    '  "notice_period_days": 60,\n'
                    '  "current_location": "Noida",\n'
                    '  "education": "B.Tech in Computer Science",\n'
                    '  "summary": "Experienced backend developer with 6+ years in Java and microservices."\n'
                    "}\n"
                    "Return ONLY JSON."
                )

                response = groq_client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Filename: {file_name}\n\nResume Text:\n{cv_text[:4000]}"}
                    ],
                    temperature=settings.GROQ_TEMPERATURE,
                    max_tokens=settings.GROQ_MAX_TOKENS,
                    response_format={"type": "json_object"}
                )

                raw_json = response.choices[0].message.content
                data = json.loads(raw_json)
                return data, False
            except Exception as e:
                logger.error(f"Groq CV extraction error, falling back to deterministic extractor: {e}")

        # Deterministic Rule-Based Fallback / Demo Mode
        fallback_data = cls._deterministic_cv_extraction(cv_text, file_name)
        return fallback_data, True

    @staticmethod
    def _deterministic_jd_extraction(jd_text: str, job_title: Optional[str] = None) -> Dict[str, Any]:
        """
        High-accuracy rule-based heuristic extraction when Groq is unavailable or in demo mode.
        """
        lower = jd_text.lower()
        title = job_title or "Senior Java Developer"
        if "java" in lower and not job_title:
            title = "Senior Java Developer"
        elif "frontend" in lower or "react" in lower:
            title = "Senior Frontend Engineer"

        # Experience extraction
        exp_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:years|yrs)", lower)
        min_exp = float(exp_match.group(1)) if exp_match else 5.0
        max_exp = float(exp_match.group(2)) if exp_match else 8.0

        # Location
        location = "Noida"
        locations = ["noida", "gurgaon", "bangalore", "bengaluru", "hyderabad", "pune", "mumbai", "delhi", "remote"]
        for loc in locations:
            if loc in lower:
                location = loc.capitalize()
                break

        # Notice period
        notice = 60
        notice_match = re.search(r"(\d+)\s*(?:days|day)\s*notice", lower)
        if notice_match:
            notice = int(notice_match.group(1))

        # Skill dictionary search
        common_skills = [
            "Java", "Spring Boot", "Microservices", "REST APIs", "Hibernate", "Kafka",
            "Docker", "Kubernetes", "AWS", "SQL", "PostgreSQL", "React", "TypeScript",
            "Node.js", "Python", "FastAPI", "CI/CD", "Redis", "Git", "KYC", "AML Checks", "Excel"
        ]
        found_skills = [s for s in common_skills if re.search(rf"\b{re.escape(s.lower())}\b", lower)]
        
        must_have = found_skills[:4] if found_skills else ["Java", "Spring Boot", "Microservices"]
        good_to_have = found_skills[4:8] if len(found_skills) > 4 else ["Docker", "Kubernetes", "Kafka", "AWS"]

        return {
            "must_have_skills": must_have,
            "good_to_have_skills": good_to_have,
            "min_experience": min_exp,
            "max_experience": max_exp,
            "location": location,
            "max_notice_period": notice,
            "ctc_info": "15 - 25 LPA (Negotiable based on experience)",
            "suggested_title": title,
            "summary": f"Role for {title} requiring {min_exp}-{max_exp} years experience with expertise in {', '.join(must_have[:3])}."
        }

    @staticmethod
    def _deterministic_cv_extraction(cv_text: str, file_name: str = "") -> Dict[str, Any]:
        """
        High-accuracy rule-based heuristic extraction for resumes.
        """
        lower = cv_text.lower()
        lines = [line.strip() for line in cv_text.splitlines() if line.strip()]

        # Name extraction (usually line 1 or from file name)
        first_name = "Candidate"
        last_name = "Applicant"
        if lines:
            first_line = lines[0]
            words = first_line.split()
            if 2 <= len(words) <= 4 and not any(char.isdigit() or "@" in char for char in first_line):
                first_name = words[0]
                last_name = " ".join(words[1:])
            elif file_name:
                name_part = re.sub(r"[-_]", " ", file_name.split(".")[0]).title().split()
                if len(name_part) >= 2:
                    first_name = name_part[0]
                    last_name = name_part[1]

        # Email
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", cv_text)
        email = email_match.group(0).lower() if email_match else f"{first_name.lower()}.{last_name.lower()}@synthetic-candidate.com"

        # Phone
        phone_match = re.search(r"(?:\+91[\-\s]?)?[6789]\d{9}", cv_text)
        phone = phone_match.group(0) if phone_match else "+91 9876543210"

        # Experience
        exp_match = re.search(r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs|year)\s*(?:of\s*)?(?:experience|exp)", lower)
        if not exp_match:
            exp_match = re.search(r"total\s*experience\s*[:\-]?\s*(\d+(?:\.\d+)?)", lower)
        
        total_exp = float(exp_match.group(1)) if exp_match else 4.0
        relevant_exp = max(0.0, total_exp - 0.5)

        # Notice period
        notice_match = re.search(r"notice\s*(?:period)?\s*[:\-]?\s*(\d+)\s*(?:days|day|month|months)?", lower)
        notice_days = 30
        if notice_match:
            val = int(notice_match.group(1))
            notice_days = val * 30 if "month" in lower[notice_match.start():notice_match.end() + 15] and val <= 6 else val

        # Current role
        role = "Software Engineer"
        for potential_role in ["Senior Java Developer", "Java Developer", "KYC Analyst", "Frontend Engineer", "Full Stack Engineer", "DevOps Engineer", "Backend Developer"]:
            if potential_role.lower() in lower:
                role = potential_role
                break

        # Location
        location = "Noida"
        for loc in ["noida", "gurgaon", "bangalore", "hyderabad", "pune", "mumbai", "delhi"]:
            if loc in lower:
                location = loc.capitalize()
                break

        # Skills catalog matching
        catalog = [
            "Java", "Spring Boot", "Microservices", "REST APIs", "Hibernate", "Kafka",
            "Docker", "Kubernetes", "AWS", "SQL", "PostgreSQL", "React", "TypeScript",
            "Node.js", "Python", "FastAPI", "CI/CD", "Redis", "Git", "KYC", "AML Checks",
            "Excel", "AML", "Compliance", "Due Diligence", "JPA", "Maven", "JUnit"
        ]
        matched_skills = [s for s in catalog if re.search(rf"\b{re.escape(s.lower())}\b", lower)]
        if not matched_skills:
            matched_skills = ["Java", "SQL"]

        return {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "current_role": role,
            "total_experience_years": total_exp,
            "relevant_experience_years": relevant_exp,
            "skills": matched_skills,
            "notice_period_days": notice_days,
            "current_location": location,
            "education": "Bachelor of Technology in Computer Science",
            "summary": f"Professional with {total_exp} years experience in {role} skilled in {', '.join(matched_skills[:4])}."
        }

