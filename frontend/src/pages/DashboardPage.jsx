import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
    Box, Grid, Card, CardContent, Typography, Button, Skeleton, Chip,
} from "@mui/material";
import MonitorHeartIcon from "@mui/icons-material/MonitorHeart";
import GroupsIcon from "@mui/icons-material/Groups";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import AssessmentIcon from "@mui/icons-material/Assessment";
import { fetchMyWorkspaces, fetchWorkspaceRisk } from "../api/backend";
import { RISK_COLOR } from "../utils/risk";
import { Alert } from "@mui/material";

const RISK_COLORS = { Verde: "#10b981", Amarillo: "#f59e0b", Rojo: "#ef4444" };

function WorkspaceRiskRow({ ws }) {
    const navigate = useNavigate();
    const { data, isLoading } = useQuery({
        queryKey: ["workspaceRisk", ws.id, 7],
        queryFn: () => fetchWorkspaceRisk(ws.id, 7),
        staleTime: 60_000,
        retry: false,
    });

    const pct = data?.risk_score_percentage;
    const level = data?.risk_level ?? "Verde";
    const color = RISK_COLOR(level);

    return (
        <Card sx={{ mb: 2, bgcolor: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)" }}>
            <CardContent sx={{ p: 2, "&:last-child": { pb: 2 }, display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 2 }}>
                <Box>
                    <Typography variant="subtitle1" fontWeight={700} display="flex" alignItems="center" gap={1}>
                        {ws.name}
                        <Chip label={ws.type === 'team' ? 'Equipo' : 'Proyecto'} size="small" sx={{ height: 20, fontSize: 10 }} />
                    </Typography>
                    <Typography variant="caption" color="text.secondary">ID: {ws.id} · Dueño: {ws.owner_email || "N/A"}</Typography>
                </Box>
                <Box sx={{ display: "flex", alignItems: "center", gap: 3 }}>
                    {isLoading ? (
                        <Skeleton width={80} height={30} />
                    ) : (
                        <Box sx={{ textAlign: "right" }}>
                            <Typography variant="h6" fontWeight={800} color={color} lineHeight={1}>
                                {pct !== undefined ? `${pct}%` : "—"}
                            </Typography>
                            <Typography variant="caption" color="text.secondary" fontWeight={600}>
                                {level.toUpperCase()}
                            </Typography>
                        </Box>
                    )}
                    <Button
                        variant="outlined"
                        size="small"
                        endIcon={<ArrowForwardIcon />}
                        onClick={() => navigate(`/workspaces/${ws.id}`)}
                    >
                        Ver Detalle
                    </Button>
                </Box>
            </CardContent>
        </Card>
    );
}

function KpiCard({ icon, label, value, sub, color }) {
    return (
        <Card sx={{ height: "100%" }}>
            <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 2 }}>
                    <Box
                        sx={{
                            width: 44, height: 44, borderRadius: 2,
                            display: "flex", alignItems: "center", justifyContent: "center",
                            bgcolor: `${color}22`, color,
                        }}
                    >
                        {icon}
                    </Box>
                    <Typography variant="body2" color="text.secondary" fontWeight={600}>
                        {label}
                    </Typography>
                </Box>
                <Typography variant="h4" fontWeight={800} color={color}>
                    {value}
                </Typography>
                {sub && (
                    <Typography variant="caption" color="text.secondary">
                        {sub}
                    </Typography>
                )}
            </CardContent>
        </Card>
    );
}

export default function DashboardPage() {
    const navigate = useNavigate();

    const { data: workspacesData, isLoading: isLoadingWs } = useQuery({
        queryKey: ["myWorkspaces"],
        queryFn: fetchMyWorkspaces,
        staleTime: 60_000,
    });

    const workspaces = workspacesData?.workspaces ?? [];
    const totalTeams = workspaces.filter(w => w.type === "team").length;
    const totalProjects = workspaces.filter(w => w.type === "project").length;

    return (
        <Box>
            {/* Header */}
            <Box mb={4}>
                <Typography variant="h5" fontWeight={800} color="text.primary">
                    Panel de Control General
                </Typography>
                <Typography variant="body2" color="text.secondary" mt={0.5}>
                    Visión global de tus equipos y proyectos asignados
                </Typography>
            </Box>

            {isLoadingWs && (
                <Alert severity="info" sx={{ mb: 3 }}>
                    Cargando métricas de la organización...
                </Alert>
            )}

            {/* KPI cards - Globales */}
            <Grid container spacing={3} mb={4}>
                <Grid item xs={12} sm={4}>
                    <KpiCard
                        icon={<GroupsIcon />}
                        label="Estructuras bajo tu rol"
                        value={isLoadingWs ? "..." : workspaces.length}
                        sub={`${totalTeams} Equipos · ${totalProjects} Proyectos`}
                        color="#6366f1"
                    />
                </Grid>

                <Grid item xs={12} sm={4}>
                    <KpiCard
                        icon={<MonitorHeartIcon />}
                        label="Último Análisis"
                        value="Hoy"
                        sub="Cálculo NLP sobre mensajes recientes"
                        color="#10b981"
                    />
                </Grid>

                <Grid item xs={12} sm={4}>
                    <KpiCard
                        icon={<TrendingUpIcon />}
                        label="Variación Semanal"
                        value="N/A"
                        sub="Histórico en construcción"
                        color="#f59e0b"
                    />
                </Grid>
            </Grid>

            {/* Ranking de Workspaces */}
            <Box mb={4}>
                <Typography variant="h6" fontWeight={700} mb={2}>
                    Monitorización de Nivel de Riesgo
                </Typography>

                {isLoadingWs ? (
                    <Skeleton variant="rounded" height={80} sx={{ mb: 2 }} />
                ) : workspaces.length === 0 ? (
                    <Typography color="text.secondary">No tienes workspaces asignados que monitorizar.</Typography>
                ) : (
                    <Box>
                        {workspaces.map(ws => (
                            <WorkspaceRiskRow key={ws.id} ws={ws} />
                        ))}
                    </Box>
                )}
            </Box>

            {/* Accesos rápidos */}
            <Box mb={3}>
                <Typography variant="h6" fontWeight={700} mb={2}>
                    Accesos rápidos
                </Typography>
                <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
                    <Button
                        variant="contained"
                        startIcon={<MonitorHeartIcon />}
                        onClick={() => navigate("/team-risk")}
                        sx={{ py: 1.5, px: 3 }}
                    >
                        Ver Riesgo del Equipo
                    </Button>
                    <Button
                        variant="outlined"
                        startIcon={<AssessmentIcon />}
                        onClick={() => navigate("/reports")}
                        sx={{ py: 1.5, px: 3 }}
                    >
                        Ver Reportes
                    </Button>
                    <Button
                        variant="outlined"
                        startIcon={<GroupsIcon />}
                        onClick={() => navigate("/teams")}
                        sx={{ py: 1.5, px: 3 }}
                    >
                        Mis Equipos
                    </Button>
                </Box>
            </Box>

            {/* Info privacidad */}
            <Card sx={{ bgcolor: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.2)" }}>
                <CardContent>
                    <Typography variant="body2" color="text.secondary">
                        🔒 <strong style={{ color: "#818cf8" }}>Privacidad garantizada:</strong> Este panel nunca muestra mensajes individuales. Todas las métricas son agregados numéricos anónimos calculados a partir del análisis de lenguaje natural.
                    </Typography>
                </CardContent>
            </Card>
        </Box>
    );
}
