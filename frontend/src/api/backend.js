const BASE_URL = "http://localhost:8000";

export async function fetchTeamRisk(teamId, days) {
    const res = await fetch(`${BASE_URL}/api/team/risk?team_id=${teamId}&days=${days}`);
    if (!res.ok) throw new Error("Error al obtener riesgo del equipo");
    return res.json();
}

export async function fetchTeams() {
    const res = await fetch(`${BASE_URL}/api/teams`);
    if (!res.ok) throw new Error("Error al obtener equipos");
    return res.json();
}

export async function fetchTeamTrend(teamId, days) {
    const res = await fetch(`${BASE_URL}/api/team/risk/trend?team_id=${teamId}&days=${days}`);
    if (!res.ok) throw new Error("Error al obtener tendencia");
    return res.json();
}

export async function triggerAnalysis() {
    const res = await fetch(`${BASE_URL}/admin/trigger-analysis`, { method: "POST" });
    if (!res.ok) throw new Error("Error al lanzar análisis");
    return res.json();
}

export async function checkLoginStatus() {
    try {
        const res = await fetch(`${BASE_URL}/api/me`, { credentials: "include" });
        return res.ok;
    } catch {
        return false;
    }
}

export async function fetchUserInfo() {
    try {
        const res = await fetch(`${BASE_URL}/api/me/info`, { credentials: "include" });
        if (!res.ok) return null;
        return res.json();
    } catch {
        return null;
    }
}

export async function fetchAuthUrl() {
    try {
        const res = await fetch(`${BASE_URL}/api/auth-url`, { credentials: "include" });
        if (!res.ok) return null;
        return res.json();
    } catch {
        return null;
    }
}

export const loginUrl = `${BASE_URL}/login`;
export const logoutUrl = `${BASE_URL}/logout`;

// ── Auth / sesión ────────────────────────────────────────────────
export async function fetchMe() {
    try {
        const res = await fetch(`${BASE_URL}/api/me`, { credentials: "include" });
        if (!res.ok) return null;
        return res.json(); // { authenticated, user_email, display_name, role }
    } catch {
        return null;
    }
}

// ── Workspace endpoints ─────────────────────────────────────────
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
