import { useQuery, useQueries } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
    Box, Grid, Card, CardContent, Typography, Button, Skeleton, Chip,
} from "@mui/material";
import MonitorHeartIcon from "@mui/icons-material/MonitorHeart";
import GroupsIcon from "@mui/icons-material/Groups";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import { fetchMyWorkspaces, fetchWorkspaceRisk } from "../../api/backend";
import { RISK_COLOR } from "../../utils/risk";
import { Alert } from "@mui/material";
import { useMe } from "../../context/AuthContext";
import "./DashboardPage.css";

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
    const sampleSize = data?.sample_size ?? 0;
    const color = RISK_COLOR(level);

    return (
        <Card className="workspace-row-card">
            <CardContent className="workspace-row-content">
                {/* Info Column (Name + Type) */}
                <Box className="workspace-info-col">
                    <Typography className="workspace-name-text">
                        {ws.name}
                    </Typography>
                    <Chip
                        label={ws.type === 'team' ? 'Equipo' : 'Proyecto'}
                        variant="outlined"
                        color={ws.type === 'team' ? 'primary' : 'secondary'}
                        className="workspace-chip"
                    />
                </Box>

                {/* Metrics Column (Risk + Sample + Action) */}
                <Box className="workspace-metrics-col">
                    {isLoading ? (
                        <Skeleton width={120} height={30} />
                    ) : (
                        <>
                            <Box className="workspace-metric-item">
                                <Box className="workspace-score-text">
                                    <Typography variant="body1" fontWeight={800} color={color}>
                                        {pct !== undefined ? `${pct}%` : "—"}
                                    </Typography>
                                    {pct !== undefined && (
                                        <Chip
                                            label={level}
                                            size="small"
                                            className="workspace-level-badge"
                                            sx={{ bgcolor: `${color}18`, color: color, px: 0.5 }}
                                        />
                                    )}
                                </Box>
                            </Box>
                        </>
                    )}
                    <Button
                        variant="contained"
                        color="inherit"
                        size="small"
                        endIcon={<ArrowForwardIcon sx={{ fontSize: 16 }} />}
                        onClick={() => navigate(`/workspaces/${ws.id}`)}
                        className="workspace-action-btn"
                        sx={{ bgcolor: "rgba(255,255,255,0.05)", "&:hover": { bgcolor: "rgba(255,255,255,0.1)" } }}
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
        <Card className="kpi-card">
            <CardContent className="kpi-card-content">
                <Box className="kpi-card-header">
                    <Box
                        className="kpi-card-icon-wrapper"
                        sx={{ bgcolor: `${color}15`, color }}
                    >
                        {icon}
                    </Box>
                    <Typography variant="body2" color="text.secondary" fontWeight={600}>
                        {label}
                    </Typography>
                </Box>
                <Typography
                    variant={typeof value === 'string' && value.length > 6 ? "h5" : "h4"}
                    fontWeight={800}
                    color="text.primary"
                    sx={{ mb: 0.5 }}
                >
                    {value}
                </Typography>
                {sub && (
                    <Typography variant="caption" color="text.disabled" fontWeight={500}>
                        {sub}
                    </Typography>
                )}
            </CardContent>
        </Card>
    );
}

export default function DashboardPage() {
    const navigate = useNavigate();
    const { user } = useMe();
    const isPrivileged = user?.role === "admin" || user?.role === "manager";

    const { data: workspacesData, isLoading: isLoadingWs } = useQuery({
        queryKey: ["myWorkspaces"],
        queryFn: fetchMyWorkspaces,
        staleTime: 60_000,
    });

    const workspaces = workspacesData?.workspaces ?? [];
    const totalTeams = workspaces.filter(w => w.type === "team").length;
    const totalProjects = workspaces.filter(w => w.type === "project").length;

    // Para admin/manager: cargar todos los riesgos en paralelo y calcular la media global
    const riskQueries = useQueries({
        queries: isPrivileged ? workspaces.map(ws => ({
            queryKey: ["workspaceRisk", ws.id, 7],
            queryFn: () => fetchWorkspaceRisk(ws.id, 7),
            staleTime: 60_000,
            retry: false,
        })) : [],
    });
    const allLoaded = riskQueries.length > 0 && riskQueries.every(q => !q.isLoading);
    const scores = riskQueries.map(q => q.data?.risk_score_percentage).filter(v => v !== undefined);
    const globalRisk = scores.length > 0 ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : null;
    const globalLevel = globalRisk === null ? null : globalRisk >= 66 ? "Rojo" : globalRisk >= 33 ? "Amarillo" : "Verde";
    const globalColor = globalLevel ? RISK_COLOR(globalLevel) : "#6366f1";

    return (
        <Box className="dashboard-container">
            {/* Header */}
            <Box className="dashboard-header-container">
                <Typography variant="h5" fontWeight={800} color="text.primary">
                    Panel de Control General
                </Typography>
                <Typography variant="body2" color="text.secondary" mt={0.5}>
                    Visión global de tus equipos y proyectos asignados
                </Typography>
            </Box>

            {isLoadingWs && (
                <Alert severity="info" className="dashboard-loading-alert">
                    Cargando métricas de la organización...
                </Alert>
            )}

            {/* KPI cards */}
            <Grid container spacing={3} className="dashboard-grid-container">
                <Grid item xs={12} sm={isPrivileged ? 3 : 4}>
                    <KpiCard
                        icon={<GroupsIcon />}
                        label="Workspaces visibles"
                        value={isLoadingWs ? "..." : workspaces.length}
                        sub={`${totalTeams} Equipos · ${totalProjects} Proyectos`}
                        color="#6366f1"
                    />
                </Grid>

                <Grid item xs={12} sm={isPrivileged ? 3 : 4}>
                    <KpiCard
                        icon={<MonitorHeartIcon />}
                        label="Último Análisis"
                        value="Hoy"
                        sub="Procesado autom. nocturno"
                        color="#10b981"
                    />
                </Grid>

                <Grid item xs={12} sm={isPrivileged ? 3 : 4}>
                    <KpiCard
                        icon={<TrendingUpIcon />}
                        label="Variación Semanal"
                        value="N/A"
                        sub="Necesita más histórico"
                        color="#f59e0b"
                    />
                </Grid>

                {/* KPI Riesgo Global — solo admin/manager */}
                {isPrivileged && (
                    <Grid item xs={12} sm={3}>
                        <KpiCard
                            icon={<WarningAmberIcon />}
                            label="Riesgo Global Org."
                            value={!allLoaded ? "..." : globalRisk !== null ? `${globalRisk}%` : "—"}
                            sub={globalLevel ? `Nivel ${globalLevel} · ${scores.length} workspaces` : "Calculando..."}
                            color={globalColor}
                        />
                    </Grid>
                )}
            </Grid>

            {/* Lista compacta de Workspaces */}
            <Box className="dashboard-ranking-section">
                <Typography variant="h6" fontWeight={700} className="dashboard-ranking-title">
                    Monitorización Continua
                </Typography>

                {isLoadingWs ? (
                    <Skeleton variant="rounded" height={80} className="dashboard-skeleton" />
                ) : workspaces.length === 0 ? (
                    <Typography color="text.secondary">No tienes workspaces asignados que monitorizar.</Typography>
                ) : (
                    <Box sx={{ bgcolor: "background.paper", p: 2, borderRadius: 3, border: "1px solid rgba(255,255,255,0.05)" }}>
                        {workspaces.map(ws => (
                            <WorkspaceRiskRow key={ws.id} ws={ws} />
                        ))}
                    </Box>
                )}
            </Box>

            {/* Info privacidad */}
            <Card className="dashboard-privacy-card" sx={{ mt: 4, borderRadius: 3 }}>
                <CardContent sx={{ py: 2, "&:last-child": { pb: 2 } }}>
                    <Typography variant="body2" color="text.secondary">
                        🔒 <strong className="privacy-highlight">Contexto de privacidad:</strong> Este panel es 100% anónimo. Solo se visualizan medias agregadas de bienestar por equipo. Nunca se leen mensajes individuales.
                    </Typography>
                </CardContent>
            </Card>
        </Box>
    );
}

