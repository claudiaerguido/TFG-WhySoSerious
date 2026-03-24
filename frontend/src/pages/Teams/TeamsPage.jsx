import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
    Box, Typography, Skeleton, Avatar, Chip, Divider, Paper
} from "@mui/material";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import { fetchMyTeamsAndProjects, fetchTeamRisk, fetchProjectRisk } from "../../api/backend";
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
                <Avatar sx={{
                    bgcolor: type === 'team' ? 'rgba(99,102,241,0.1)' : 'rgba(16,185,129,0.1)',
                    color: type === 'team' ? 'primary.main' : 'success.main',
                    width: 38, height: 38, fontSize: 13, fontWeight: 800
                }}>
                    {item.name.substring(0, 2).toUpperCase()}
                </Avatar>
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
    const { data: workspacesData, isLoading } = useQuery({
        queryKey: ["myTeamsAndProjects"],
        queryFn: fetchMyTeamsAndProjects,
        staleTime: 60_000,
    });

    const teams = workspacesData?.teams ?? [];
    const projects = workspacesData?.projects ?? [];

    return (
        <Box sx={{ maxWidth: 860, mx: 'auto' }}>
            <Box sx={{ mb: 5 }}>
                <Typography variant="h4" fontWeight={800} sx={{ letterSpacing: -0.5 }}>
                    Equipos
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                    Riesgo global del equipo: promedio del riesgo global de sus integrantes.
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
                    <TeamSection title="Equipos Organizativos" items={teams} type="team" />
                    <TeamSection title="Proyectos Tácticos" items={projects} type="project" />
                </>
            )}
        </Box>
    );
}
