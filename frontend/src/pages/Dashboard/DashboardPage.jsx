import { useQuery, useQueries } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
    Box, Grid, Card, CardContent, Typography, Button, Skeleton, Chip, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Avatar, IconButton, Alert
} from "@mui/material";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import MoreHorizIcon from "@mui/icons-material/MoreHoriz";
import { fetchMyWorkspaces, fetchWorkspaceRisk } from "../../api/backend";
import { useMe } from "../../context/AuthContext";
import "./DashboardPage.css";

const CHIP_COLORS = {
    Verde: { bg: '#dcfce7', text: '#16a34a' },
    Amarillo: { bg: '#fef9c3', text: '#b45309' },
    Rojo: { bg: '#fee2e2', text: '#dc2626' },
};
function chipStyle(level) {
    const c = CHIP_COLORS[level] ?? { bg: '#f1f5f9', text: '#64748b' };
    return { bgcolor: c.bg, color: c.text, fontWeight: 700, fontSize: '11px', borderRadius: 1 };
}
function pctColor(level) {
    return (CHIP_COLORS[level] ?? { text: 'inherit' }).text;
}

function KpiCard({ title, value, badgeText, badgeType, subText }) {
    return (
        <Card className="kpi-card" sx={{ height: '100%', borderRadius: 3, display: 'flex', flexDirection: 'column', transition: 'transform 0.2s', '&:hover': { transform: 'translateY(-2px)' } }}>
            <CardContent className="kpi-card-content" sx={{ p: 3, pb: "24px !important", flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                <Box className="kpi-card-header" sx={{ mb: 1.5 }}>
                    <Box className="kpi-card-title-group">
                        <Typography variant="caption" color="text.secondary" fontWeight={700} sx={{ textTransform: 'uppercase', letterSpacing: 1, fontSize: '11px' }}>
                            {title}
                        </Typography>
                    </Box>
                </Box>
                <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                    <Typography variant="h4" fontWeight={800} color="text.primary" sx={{ mb: 1.5, lineHeight: 1.2 }}>
                        {value}
                    </Typography>
                    {(badgeText || subText) && (
                        <Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: 'wrap' }}>
                            {badgeText && (
                                <Box className={`kpi-badge kpi-badge-${badgeType}`} sx={{ py: 0.3, px: 1, minHeight: '22px' }}>
                                    {badgeType === "up" && <ArrowUpwardIcon sx={{ fontSize: 14 }} />}
                                    {badgeType === "down" && <ArrowDownwardIcon sx={{ fontSize: 14 }} />}
                                    <Typography variant="caption" fontWeight={700} sx={{ fontSize: '11px' }}>{badgeText}</Typography>
                                </Box>
                            )}
                            {subText && (
                                <Typography variant="caption" color="text.secondary" fontWeight={500} sx={{ fontSize: '12px', whiteSpace: 'nowrap' }}>
                                    {subText}
                                </Typography>
                            )}
                        </Box>
                    )}
                </Box>
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

    const riskQueries = useQueries({
        queries: workspaces.map(ws => ({
            queryKey: ["workspaceRisk", ws.id, 7],
            queryFn: () => fetchWorkspaceRisk(ws.id, 7),
            staleTime: 60_000,
            retry: false,
        }))
    });

    const allLoaded = riskQueries.length > 0 && riskQueries.every(q => !q.isLoading);

    const workspacesWithRisk = workspaces.map((ws, i) => {
        const riskData = riskQueries[i].data;
        const isLoading = riskQueries[i].isLoading;
        const pct = riskData?.risk_score_percentage;
        const level = riskData?.risk_level ?? "Verde";
        return { ...ws, riskData, isLoading, pct, level };
    });

    const scores = workspacesWithRisk.map(w => w.pct).filter(v => v !== undefined);
    const globalRisk = scores.length > 0 ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : null;
    const globalLevel = globalRisk === null ? null : globalRisk >= 66 ? "Rojo" : globalRisk >= 33 ? "Amarillo" : "Verde";

    const today = new Date();
    const dateStr = today.toLocaleDateString("es-ES", { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    const formattedDate = dateStr.charAt(0).toUpperCase() + dateStr.slice(1);

    return (
        <Box className="dashboard-container">
            <Box className="dashboard-header-container" sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
                <Box>
                    <Typography variant="h5" fontWeight={800} color="text.primary">
                        ¡Bienvenido de nuevo, {user?.display_name?.split(' ')[0] ?? 'Usuario'}!
                    </Typography>
                    <Typography variant="body2" color="text.secondary" mt={0.5} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {formattedDate} <span style={{ color: '#cbd5e1' }}>|</span> Visión global de tu bienestar organizacional
                    </Typography>
                </Box>
            </Box>

            {isLoadingWs && (
                <Alert severity="info" className="dashboard-loading-alert" sx={{ mb: 3 }}>
                    Cargando métricas de la organización...
                </Alert>
            )}

            {/* Top Row: KPI cards */}
            <Grid container spacing={2} className="dashboard-grid-container" sx={{ mb: 4, alignItems: 'stretch' }}>
                <Grid item xs={12} sm={6} md={3} sx={{ display: 'flex' }}>
                    <Box sx={{ width: '100%' }}>
                        <KpiCard
                            title="Workspaces visibles"
                            value={isLoadingWs ? "..." : workspaces.length}
                            badgeText={totalTeams.toString()}
                            badgeType="circle"
                            subText={`Equipos · ${totalProjects} Proyectos`}
                        />
                    </Box>
                </Grid>

                <Grid item xs={12} sm={6} md={3} sx={{ display: 'flex' }}>
                    <Box sx={{ width: '100%' }}>
                        <KpiCard
                            title="Último Análisis"
                            value="Hoy"
                            badgeText="Completado"
                            badgeType="up"
                            subText="Procesado autom. nocturno"
                        />
                    </Box>
                </Grid>

                <Grid item xs={12} sm={6} md={3} sx={{ display: 'flex' }}>
                    <Box sx={{ width: '100%' }}>
                        <KpiCard
                            title="Workspaces en Riesgo"
                            value={!allLoaded ? "..." : (workspacesWithRisk.filter(w => w.level === "Rojo" || w.level === "Amarillo").length).toString()}
                            badgeText="Atención"
                            badgeType={(workspacesWithRisk.filter(w => w.level === "Rojo" || w.level === "Amarillo").length) > 0 ? "down" : "neutral"}
                            subText="Requieren revisión"
                        />
                    </Box>
                </Grid>

                <Grid item xs={12} sm={6} md={3} sx={{ display: 'flex' }}>
                    <Box sx={{ width: '100%' }}>
                        <KpiCard
                            title="Riesgo Global Org."
                            value={!allLoaded ? "..." : globalRisk !== null ? `${globalRisk}%` : "—"}
                            badgeText={globalLevel || "-"}
                            badgeType={globalLevel === "Rojo" ? "down" : globalLevel === "Amarillo" ? "neutral" : "up"}
                            subText={"Basado en " + scores.length + " workspaces"}
                        />
                    </Box>
                </Grid>
            </Grid>

            {/* Bottom Row: Data Table */}
            <Card sx={{ borderRadius: 3, border: '1px solid rgba(0,0,0,0.05)', boxShadow: '0 4px 20px rgba(0,0,0,0.03)', mb: 4 }}>
                <CardContent sx={{ p: 4, pb: "32px !important" }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <Typography variant="h6" fontWeight={700}>Detalles de Workspaces</Typography>
                            <Chip label={`${workspaces.length} activos`} size="small" sx={{ bgcolor: 'rgba(0,0,0,0.04)', fontWeight: 600, color: 'text.secondary' }} />
                        </Box>
                    </Box>

                    <TableContainer sx={{ border: '1px solid rgba(0,0,0,0.04)', borderRadius: 2 }}>
                        <Table sx={{ minWidth: 650 }}>
                            <TableHead sx={{ bgcolor: '#f8fafc' }}>
                                <TableRow>
                                    <TableCell sx={{ fontWeight: 700, color: 'text.secondary', borderBottom: '1px solid rgba(0,0,0,0.04)' }}>Nombre completo</TableCell>
                                    <TableCell sx={{ fontWeight: 700, color: 'text.secondary', borderBottom: '1px solid rgba(0,0,0,0.04)' }}>Tipo</TableCell>
                                    <TableCell sx={{ fontWeight: 700, color: 'text.secondary', borderBottom: '1px solid rgba(0,0,0,0.04)' }}>Muestra</TableCell>
                                    <TableCell sx={{ fontWeight: 700, color: 'text.secondary', borderBottom: '1px solid rgba(0,0,0,0.04)' }}>Puntuación Riesgo</TableCell>
                                    <TableCell sx={{ fontWeight: 700, color: 'text.secondary', borderBottom: '1px solid rgba(0,0,0,0.04)' }}>Nivel</TableCell>
                                    <TableCell align="right" sx={{ fontWeight: 700, color: 'text.secondary', borderBottom: '1px solid rgba(0,0,0,0.04)' }}>Acción</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {workspacesWithRisk.length === 0 && !isLoadingWs ? (
                                    <TableRow>
                                        <TableCell colSpan={6} align="center" sx={{ py: 6, color: 'text.secondary' }}>
                                            No tienes workspaces asignados que monitorizar.
                                        </TableCell>
                                    </TableRow>
                                ) : workspacesWithRisk.map((ws) => (
                                    <TableRow key={ws.id} hover sx={{ '&:last-child td, &:last-child th': { border: 0 }, cursor: 'pointer', transition: 'background-color 0.2s' }} onClick={() => navigate(`/workspaces/${ws.id}`)}>
                                        <TableCell sx={{ borderBottom: '1px solid rgba(0,0,0,0.03)', py: 2 }}>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                                <Avatar sx={{ width: 36, height: 36, bgcolor: ws.type === 'team' ? 'primary.main' : 'secondary.main', fontSize: 14, fontWeight: 700 }}>
                                                    {ws.name.substring(0, 2).toUpperCase()}
                                                </Avatar>
                                                <Typography variant="body2" fontWeight={700} color="text.primary">
                                                    {ws.name}
                                                </Typography>
                                            </Box>
                                        </TableCell>
                                        <TableCell sx={{ borderBottom: '1px solid rgba(0,0,0,0.03)' }}>
                                            <Typography variant="body2" color="text.secondary" fontWeight={500}>
                                                {ws.type === "team" ? "Equipo" : "Proyecto"}
                                            </Typography>
                                        </TableCell>
                                        <TableCell sx={{ borderBottom: '1px solid rgba(0,0,0,0.03)' }}>
                                            <Typography variant="body2" color="text.secondary" fontWeight={500}>
                                                {ws.riskData?.sample_size ?? 0} eval.
                                            </Typography>
                                        </TableCell>
                                        <TableCell sx={{ borderBottom: '1px solid rgba(0,0,0,0.03)' }}>
                                            {ws.isLoading ? (
                                                <Skeleton width={40} />
                                            ) : (
                                                <Typography variant="body2" fontWeight={800} sx={{ color: pctColor(ws.level) }}>
                                                    {ws.pct !== undefined ? `${ws.pct}%` : "—"}
                                                </Typography>
                                            )}
                                        </TableCell>
                                        <TableCell sx={{ borderBottom: '1px solid rgba(0,0,0,0.03)' }}>
                                            {ws.isLoading ? (
                                                <Skeleton width={60} />
                                            ) : (
                                                <Chip
                                                    label={ws.level}
                                                    size="small"
                                                    sx={chipStyle(ws.level)}
                                                />
                                            )}
                                        </TableCell>
                                        <TableCell align="right" sx={{ borderBottom: '1px solid rgba(0,0,0,0.03)' }}>
                                            <IconButton size="small">
                                                <MoreHorizIcon sx={{ color: 'text.disabled' }} />
                                            </IconButton>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </CardContent>
            </Card>

            <Card className="dashboard-privacy-card" sx={{ mt: 2, borderRadius: 3, bgcolor: 'rgba(0,0,0,0.01)', border: '1px dashed rgba(0,0,0,0.05)' }}>
                <CardContent sx={{ py: 2, "&:last-child": { pb: 2 } }}>
                    <Typography variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <InfoOutlinedIcon sx={{ fontSize: 18 }} />
                        <Box component="span" sx={{ fontWeight: 600 }}>Privacidad por diseño:</Box>
                        Solo se visualizan medias agregadas por equipo para proteger la individualidad.
                    </Typography>
                </CardContent>
            </Card>
        </Box>
    );
}
