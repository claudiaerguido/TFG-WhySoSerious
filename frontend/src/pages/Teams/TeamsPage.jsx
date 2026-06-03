import { useQuery } from "@tanstack/react-query";
import { useLocation, useNavigate } from "react-router-dom";
import {
    Box, Typography, Skeleton, Chip, Divider, Paper
} from "@mui/material";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import GroupsIcon from "@mui/icons-material/Groups";
import AssignmentOutlinedIcon from "@mui/icons-material/AssignmentOutlined";
import { fetchMyTeamsAndProjects, fetchTeamRisk, fetchProjectRisk } from "../../api/api";
import "./TeamsPage.css";

const CHIP_COLORS = {
    Verde: { bg: '#dcfce7', text: '#16a34a' },
    Amarillo: { bg: '#fef9c3', text: '#b45309' },
    Rojo: { bg: '#fee2e2', text: '#dc2626' },
};

function chipStyle(level) {
    const c = CHIP_COLORS[level] ?? { bg: '#f1f5f9', text: '#64748b' };
    return { bgcolor: c.bg, color: c.text, fontWeight: 700, fontSize: 11, border: 'none', height: 22 };
}

function WorkspaceIcon({ type }) {
    const isTeam = type === "team";
    const Icon = isTeam ? GroupsIcon : AssignmentOutlinedIcon;
    return (
        <Box
            sx={{
                width: 36,
                height: 36,
                borderRadius: 1.5,
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                bgcolor: isTeam ? "rgba(79, 70, 229, 0.08)" : "rgba(5, 150, 105, 0.08)",
                color: isTeam ? "#4f46e5" : "#059669",
                border: isTeam ? "1px solid rgba(79, 70, 229, 0.14)" : "1px solid rgba(5, 150, 105, 0.14)",
                flex: "0 0 auto",
            }}
        >
            <Icon sx={{ fontSize: 19 }} />
        </Box>
    );
}

function TeamRow({ item, type }) {
    const navigate = useNavigate();
    const { data: riskData, isLoading } = useQuery({
        queryKey: [type === "team" ? "teamRisk" : "projectRisk", item.id, 7],
        queryFn: () => type === "team" ? fetchTeamRisk(item.id, 7) : fetchProjectRisk(item.id, 7),
        staleTime: 60_000,
    });

    const level = riskData?.risk_level ?? "—";
    const pct = riskData?.risk_score_percentage;
    const pctColor = level === 'Rojo' ? '#dc2626' : level === 'Amarillo' ? '#b45309' : level === 'Verde' ? '#16a34a' : 'text.primary';

    return (
        <Box
            className="team-row"
            onClick={() => navigate(`/${type}/${item.id}`)}
        >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flex: 1 }}>
                <WorkspaceIcon type={type} />
                <Box>
                    <Typography variant="body1" fontWeight={700} color="text.primary" sx={{ lineHeight: 1.3 }}>
                        {item.name}
                    </Typography>
                    <Typography variant="caption" color="text.disabled">
                        {type === 'team' ? 'Equipo Organ.' : 'Proyecto Táctico'}
                    </Typography>
                </Box>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <Box sx={{ textAlign: 'right', minWidth: 80 }}>
                    {isLoading ? <Skeleton width={50} /> : (
                        <Typography variant="body2" fontWeight={700} sx={{ color: pctColor }}>
                            {pct !== undefined ? `${pct}%` : "—"}
                        </Typography>
                    )}
                    <Typography variant="caption" color="text.disabled">Riesgo</Typography>
                </Box>

                <Box sx={{ minWidth: 70 }}>
                    {isLoading ? <Skeleton width={56} height={24} /> : (
                        <Chip
                            label={level}
                            size="small"
                            sx={chipStyle(level)}
                        />
                    )}
                </Box>

                <ChevronRightIcon sx={{ color: 'text.disabled', fontSize: 20 }} className="row-chevron" />
            </Box>
        </Box>
    );
}

function TeamSection({ title, items, type }) {
    if (!items.length) return null;
    return (
        <Box sx={{ mb: 5 }}>
            <Typography variant="overline" color="text.disabled" fontWeight={700} sx={{ letterSpacing: 1.5 }}>
                {title} · {items.length}
            </Typography>
            <Paper elevation={0} sx={{ mt: 1.5, borderRadius: 3, border: '1px solid rgba(0,0,0,0.07)', overflow: 'hidden' }}>
                {items.map((it, i) => (
                    <Box key={it.id}>
                        {i > 0 && <Divider sx={{ mx: 2, opacity: 0.5 }} />}
                        <TeamRow item={it} type={type} />
                    </Box>
                ))}
            </Paper>
        </Box>
    );
}

export default function TeamsPage() {
    const location = useLocation();
    const isProjectsView = location.pathname === "/projects";

    const { data: workspacesData, isLoading } = useQuery({
        queryKey: ["myTeamsAndProjects"],
        queryFn: fetchMyTeamsAndProjects,
        staleTime: 60_000,
    });

    const teams = workspacesData?.teams ?? [];
    const projects = workspacesData?.projects ?? [];

    const pageTitle = isProjectsView ? "Proyectos" : "Equipos";
    const pageDesc = isProjectsView
        ? "Riesgo táctico del proyecto: promedio del riesgo contextual de sus integrantes."
        : "Riesgo global del equipo: promedio del riesgo global de sus integrantes.";

    return (
        <Box sx={{ maxWidth: 860, mx: 'auto' }}>
            <Box sx={{ mb: 5 }}>
                <Typography variant="h4" fontWeight={800} sx={{ letterSpacing: -0.5 }}>
                    {pageTitle}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                    {pageDesc}
                </Typography>
            </Box>

            {isLoading ? (
                <Box>
                    {[1, 2, 3].map(i => <Skeleton key={i} variant="rounded" height={64} sx={{ mb: 1.5, borderRadius: 3 }} />)}
                </Box>
            ) : (teams.length === 0 && projects.length === 0) ? (
                <Box sx={{ textAlign: 'center', py: 10, color: 'text.disabled' }}>
                    <Typography variant="body1">No hay equipos ni proyectos asignados</Typography>
                </Box>
            ) : (
                <>
                    {!isProjectsView && <TeamSection title="Equipos Organizativos" items={teams} type="team" />}
                    {isProjectsView && <TeamSection title="Proyectos Tácticos" items={projects} type="project" />}
                </>
            )}
        </Box>
    );
}
