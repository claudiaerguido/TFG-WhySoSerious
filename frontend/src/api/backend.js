const BASE_URL = "http://localhost:8000";

// ── Admin Actions ──────────────────────────────────────────────
export async function triggerAnalysis() {
    const res = await fetch(`${BASE_URL}/admin/trigger-analysis`, { method: "POST" });
    if (!res.ok) throw new Error("Error al lanzar análisis");
    return res.json();
}

// ── Auth / Sesión ────────────────────────────────────────────────
export const loginUrl = `${BASE_URL}/login`;
export const logoutUrl = `${BASE_URL}/logout`;

export async function fetchMe() {
    try {
        const res = await fetch(`${BASE_URL}/api/me`, { credentials: "include" });
        if (!res.ok) return null;
        return res.json(); // { authenticated, user_email, display_name, role }
    } catch {
        return null;
    }
}

// ── Workspace Endpoints ─────────────────────────────────────────
export async function fetchMyWorkspaces() {
    const res = await fetch(`${BASE_URL}/api/my/workspaces`, { credentials: "include" });
    if (res.status === 401) return { workspaces: [], role: null };
    if (!res.ok) throw new Error("Error al obtener workspaces");
    return res.json(); // { workspaces: [...], role }
}

export async function fetchWorkspaceRisk(workspaceId, days = 7) {
    const res = await fetch(
        `${BASE_URL}/api/workspace/risk?workspace_id=${workspaceId}&days=${days}`,
        { credentials: "include" }
    );
    if (res.status === 403) throw Object.assign(new Error("Forbidden"), { status: 403 });
    if (!res.ok) throw new Error("Error al obtener riesgo del workspace");
    return res.json();
}

export async function fetchWorkspaceTrend(workspaceId, days = 30) {
    const res = await fetch(
        `${BASE_URL}/api/workspace/trend?workspace_id=${workspaceId}&days=${days}`,
        { credentials: "include" }
    );
    if (res.status === 403) throw Object.assign(new Error("Forbidden"), { status: 403 });
    if (!res.ok) throw new Error("Error al obtener tendencia del workspace");
    return res.json();
}

export async function fetchWorkspaceMembers(workspaceId) {
    const res = await fetch(
        `${BASE_URL}/api/workspace/members?workspace_id=${workspaceId}`,
        { credentials: "include" }
    );
    if (res.status === 403) throw Object.assign(new Error("Forbidden"), { status: 403 });
    if (!res.ok) throw new Error("Error al obtener miembros del workspace");
    return res.json(); // { members: [{alias, included}], workspace_id }
}

export async function fetchWorkspaceMemberRisks(workspaceId, days = 7) {
    const res = await fetch(
        `${BASE_URL}/api/workspace/member-risks?workspace_id=${workspaceId}&days=${days}`,
        { credentials: "include" }
    );
    if (res.status === 403) throw Object.assign(new Error("Forbidden"), { status: 403 });
    if (!res.ok) throw new Error("Error al obtener riesgo por miembro");
    return res.json(); // { members: [{alias, risk_score_percentage, risk_level, message_count}] }
}
