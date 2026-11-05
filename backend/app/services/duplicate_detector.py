import hashlib
import re
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.models.candidate import Candidate, Resume


class DuplicateDetector:
    @staticmethod
    def compute_sha256(file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    def normalize_email(email: Optional[str]) -> Optional[str]:
        if not email:
            return None
        return email.strip().lower()

    @staticmethod
    def normalize_phone(phone: Optional[str]) -> Optional[str]:
        if not phone:
            return None
        # Extract only digits
        digits = re.sub(r"\D", "", phone)
        # Take last 10 digits for Indian/standard phone numbers
        if len(digits) >= 10:
            return digits[-10:]
        return digits if digits else None

    @classmethod
    def check_duplicate(
        cls,
        db: Session,
        file_hash: str,
        email: Optional[str] = None,
        phone: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[Candidate]]:
        """
        Check if resume or candidate already exists using:
        1. Exact SHA-256 file hash matching.
        2. Normalized email matching.
        3. Normalized phone number matching.
        Returns: (is_duplicate: bool, duplicate_reason: str, existing_candidate: Optional[Candidate])
        """
        # 1. Exact file hash check
        existing_resume = db.query(Resume).filter(Resume.file_hash == file_hash).first()
        if existing_resume and existing_resume.candidate:
            return True, f"Identical file already uploaded for candidate {existing_resume.candidate.candidate_code} ({existing_resume.file_name})", existing_resume.candidate

        # 2. Email match
        norm_email = cls.normalize_email(email)
        if norm_email:
            existing_candidate = db.query(Candidate).filter(Candidate.email.ilike(norm_email)).first()
            if existing_candidate:
                return True, f"Candidate with email {email} already registered ({existing_candidate.candidate_code})", existing_candidate

        # 3. Phone match
        norm_phone = cls.normalize_phone(phone)
        if norm_phone and len(norm_phone) >= 10:
            candidates_with_phone = db.query(Candidate).filter(Candidate.phone.isnot(None)).all()
            for cand in candidates_with_phone:
                if cand.phone and cls.normalize_phone(cand.phone) == norm_phone:
                    return True, f"Candidate with phone number matching {phone} already registered ({cand.candidate_code})", cand

        return False, None, None

