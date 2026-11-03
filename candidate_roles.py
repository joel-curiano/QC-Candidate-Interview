"""Candidate role options and legacy-role normalization by discipline."""

NDT_DISCIPLINE = "NDT QC"


def candidate_roles_for_discipline(discipline):
    if discipline == NDT_DISCIPLINE:
        return ("Coordinator", "Supervisor")
    return ("Inspector", "Supervisor")


def default_candidate_role(discipline):
    return candidate_roles_for_discipline(discipline)[0]


def normalize_candidate_role(discipline, candidate_role):
    if not candidate_role or candidate_role in ("All", ""):
        return default_candidate_role(discipline)
    if candidate_role == "Technician":
        return default_candidate_role(discipline)
    return candidate_role


def is_valid_candidate_role(discipline, candidate_role):
    return candidate_role in candidate_roles_for_discipline(discipline)
