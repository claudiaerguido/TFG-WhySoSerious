"""
db_supabase.py — Proxy de compatibilidad (Arquitectura Simplificada).
Re-exporta funciones desde los nuevos módulos consolidados.
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_client import get_supabase_client
from logic.risk_model import (
    TARGET_LABELS, DB_COLS, NEGATIVE_LABELS, RISK_THRESHOLDS,
    _risk_level, _safe_corr, _normalize_weights, compute_pearson_msg_risk as _pearson_msg_risk
)
from db_repository import (
    fetch_team_members as _fetch_team_members,
    fetch_project_members as _fetch_project_members,
    fetch_metrics_for_users as _fetch_team_metrics,
    save_risk_metrics
)
from services.permissions_service import (
    ensure_org_user, get_user_role, get_teams_and_projects_for_user
)
from services.risk_service import (
    get_employee_global_risk, get_employee_project_risk,
    get_team_global_risk, get_project_global_risk,
    get_team_risk_trend, get_member_projects_breakdown,
    get_project_risk_trend, get_project_members_list as get_project_members,
    get_all_workspaces_with_members as get_all_teams_and_projects_with_members
)
from services.legacy_service import (
    get_workspace_risk_metrics, get_workspace_member_risks
)

# Helpers de compatibilidad para emails
from db_repository import fetch_team_members, fetch_project_members

def _fetch_team_emails(supabase, team_id: int):
    return [m["user_email"] for m in fetch_team_members(supabase, team_id)]

def _fetch_project_emails(supabase, project_id: int):
    return [m["user_email"] for m in fetch_project_members(supabase, project_id)]

def _fetch_workspace_emails(supabase, workspace_id: int):
    from services.legacy_service import _fetch_workspace_emails as _fwe
    return _fwe(supabase, workspace_id)