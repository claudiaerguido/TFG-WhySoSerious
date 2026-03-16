from typing import Dict, List, Any
from db_client import get_supabase_client
from logic.risk_model import compute_pearson_msg_risk, _risk_level, DB_COLS, TARGET_LABELS
from db_repository import fetch_metrics_for_users

def _fetch_workspace_emails(supabase, workspace_id: int) -> List[str]:
    """Legacy helper para obtener emails de un workspace."""
    try:
        res = supabase.table("workspace_members").select("user_email").eq("workspace_id", workspace_id).execute()
        return [r["user_email"] for r in (res.data or [])]
    except Exception as e:
        print(f"⚠️ _fetch_workspace_emails error: {e}")
        return []

def get_workspace_risk_metrics(workspace_id: int, days: int = 30) -> Dict[str, Any]:
    """
    (Legacy) Calcula el riesgo para un workspace de tipo equipo/proyecto antiguo.
    """
    supabase = get_supabase_client()
    emails = _fetch_workspace_emails(supabase, workspace_id)
    if not emails:
        return {"risk_level": "BAJO", "risk_score_percentage": 0, "sample_size": 0}

    df = fetch_metrics_for_users(supabase, emails, days, workspace_id=workspace_id)
    if df.empty:
        return {"risk_level": "BAJO", "risk_score_percentage": 0, "sample_size": 0}

    # Cálculo simplificado para legacy (Pearson)
    try:
        avg_scores = df[[DB_COLS[l] for l in TARGET_LABELS]].mean().to_dict()
        # Convertir nombres de columna de BD a etiquetas de modelo
        scores_for_risk = {l: avg_scores.get(DB_COLS[l], 0) for l in TARGET_LABELS}
        
        risk_percentage = compute_pearson_msg_risk(scores_for_risk)
        return {
            "risk_level": _risk_level(risk_percentage),
            "risk_score_percentage": int(risk_percentage),
            "sample_size": len(emails)
        }
    except Exception as e:
        print(f"⚠️ get_workspace_risk_metrics error: {e}")
        return {"risk_level": "ERROR", "risk_score_percentage": 0, "sample_size": 0}

def get_workspace_member_risks(workspace_id: int, days: int = 30) -> List[Dict[str, Any]]:
    """(Legacy) Desglose de riesgos por miembro en un workspace antiguo."""
    supabase = get_supabase_client()
    emails = _fetch_workspace_emails(supabase, workspace_id)
    if not emails: return []

    df = fetch_metrics_for_users(supabase, emails, days, workspace_id=workspace_id)
    
    results = []
    for email in emails:
        user_df = df[df["user_email"] == email]
        if user_df.empty:
            results.append({"user_email": email, "risk_score_percentage": 0, "risk_level": "BAJO"})
            continue
            
        avg_scores = user_df[[DB_COLS[l] for l in TARGET_LABELS]].mean().to_dict()
        scores_for_risk = {l: avg_scores.get(DB_COLS[l], 0) for l in TARGET_LABELS}
        risk_p = compute_pearson_msg_risk(scores_for_risk)
        
        results.append({
            "user_email": email,
            "risk_score_percentage": int(risk_p),
            "risk_level": _risk_level(risk_p)
        })
    return results
