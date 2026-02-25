import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
    Box, Typography, Grid, Card, CardContent, Button, Chip,
    Alert, Skeleton, Divider, Table, TableBody, TableCell,
    TableContainer, TableHead, TableRow, Paper, ToggleButtonGroup, ToggleButton,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import RefreshIcon from "@mui/icons-material/Refresh";
import LockIcon from "@mui/icons-material/Lock";
import {
    fetchWorkspaceRisk, fetchWorkspaceTrend,
    fetchWorkspaceMembers, triggerAnalysis,
} from "../api/backend";
import RiskCard from "../components/RiskCard";
import { RISK_COLOR, fmtPct } from "../utils/risk";
import {
    ResponsiveContainer, AreaChart, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Area
} from "recharts";

const DAY_OPTIONS = [7, 30, 60];

export default function ProjectDetailPage() {
    const { id } = useParams();
    const workspaceId = Number(id) || 1;
    const navigate = useNavigate();
    const [days, setDays] = useState(30);

    const riskQuery = useQuery({
        queryKey: ["workspaceRisk", workspaceId, days],
        queryFn: () => fetchWorkspaceRisk(workspaceId, days),
        staleTime: 30_000,
        retry: false,
    });

    const trendQuery = useQuery({
        queryKey: ["workspaceTrend", workspaceId, days],
        queryFn: () => fetchWorkspaceTrend(workspaceId, days),
        staleTime: 30_000,
        retry: false,
    });

    const membersQuery = useQuery({
        queryKey: ["workspaceMembers", workspaceId],
        queryFn: () => fetchWorkspaceMembers(workspaceId),
        staleTime: 120_000,
        retry: false,
    });

    const triggerMutation = useMutation({ mutationFn: triggerAnalysis });

    const riskData = riskQuery.data;
    const trendData = trendQuery.data?.trend ?? [];
    const members = membersQuery.data?.members ?? [];

    if (import.meta.env.DEV && riskData) {
        console.log(`[WorkspaceDetail ${workspaceId}] payload:`, riskData);
    }

    // 403 — acceso denegado
    const is403 = riskQuery.error?.status === 403;
    if (is403) {
        return (
            <Box>
                <Button startIcon={<ArrowBackIcon />} onClick={() => navigate("/teams")}
                    sx={{ mb: 3, color: "text.secondary" }}>
                    Volver
                </Button>
                <Alert severity="error" icon={<LockIcon />}>
                    No tienes permiso para ver este workspace. Contacta con tu manager.
                </Alert>
            </Box>
        );
    }

    const level = riskData?.risk_level;
    const rc = RISK_COLOR(level);

    // Custom Tooltip for Recharts
    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <Box sx={{ bgcolor: "background.paper", p: 1.5, border: "1px solid rgba(255,255,255,0.1)", borderRadius: 1 }}>
                    <Typography variant="caption" color="text.secondary">{label}</Typography>
                    <Typography variant="body2" fontWeight={700} color="primary.light">
                        Riesgo: {payload[0].value}%
                    </Typography>
                </Box>
            );
        }
        return null;
    };

    return (
        <Box>
            <Button startIcon={<ArrowBackIcon />} onClick={() => navigate("/teams")}
                sx={{ mb: 3, color: "text.secondary" }}>
                Volver a Mis Equipos
            </Button>

            {/* Header */}
            <Box mb={4} display="flex" alignItems="center" justifyContent="space-between" flexWrap="wrap" gap={2}>
                <Box>
                    <Typography variant="h5" fontWeight={800} display="flex" alignItems="center" gap={1}>
                        Workspace #{workspaceId}
                        <Chip label={`${members.length} miembros`} size="small" variant="outlined" sx={{ fontSize: 11 }} />
                    </Typography>
                    <Typography variant="body2" color="text.secondary" mt={0.5}>
                        Análisis de bienestar · Últimos {days} días {riskData?.sample_size ? `· ${riskData.sample_size} msjs analizados` : ""}
                    </Typography>
                </Box>
                <Button
                    variant="contained"
                    startIcon={<RefreshIcon />}
                    onClick={() => triggerMutation.mutate()}
                    disabled={triggerMutation.isPending}
                    size="small"
                >
                    {triggerMutation.isPending ? "Analizando…" : "Actualizar análisis"}
                </Button>
            </Box>

            {triggerMutation.isSuccess && (
                <Alert severity="success" sx={{ mb: 3 }}>
                    Análisis lanzado. Los datos se actualizarán en breve.
                </Alert>
            )}

            {/* Selector de período */}
            <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 2 }}>
                <ToggleButtonGroup value={days} exclusive onChange={(_, v) => v && setDays(v)} size="small">
                    {DAY_OPTIONS.map((d) => (
                        <ToggleButton key={d} value={d} sx={{ px: 2, fontSize: 12 }}>{d}d</ToggleButton>
                    ))}
                </ToggleButtonGroup>
            </Box>

            <Grid container spacing={3}>
                {/* Card principal: riesgo actual */}
                <Grid item xs={12} md={4}>
                    {riskQuery.isLoading ? (
                        <Skeleton variant="rounded" height={280} />
                    ) : (
                        <RiskCard
                            riskLevel={level}
                            riskScore={riskData?.risk_score_percentage}
                            sampleSize={riskData?.sample_size}
                        />
                    )}
                </Grid>

                {/* Card: tendencia */}
                <Grid item xs={12} md={8}>
                    <Card sx={{ height: "100%", minHeight: 280 }}>
                        <CardContent>
                            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                                <Typography variant="h6" fontWeight={700}>Evolución del riesgo</Typography>
                                <Chip label={`${days} días`} size="small" variant="outlined" color="primary" />
                            </Box>
                            {trendQuery.isLoading ? (
                                <Skeleton variant="rounded" height={200} />
                            ) : trendData.length === 0 ? (
                                <Box sx={{
                                    height: 200, display: "flex", alignItems: "center",
                                    justifyContent: "center", color: "text.secondary", textAlign: "center", fontSize: 14
                                }}>
                                    Sin suficientes datos históricos todavía.
                                </Box>
                            ) : (
                                <Box sx={{ height: 260, mt: 2 }}>
                                    <ResponsiveContainer width="100%" height="100%">
                                        <AreaChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                            <defs>
                                                <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                                                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                                                </linearGradient>
                                            </defs>
                                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                                            <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickMargin={10} minTickGap={20} />
                                            <YAxis stroke="#94a3b8" fontSize={11} tickFormatter={(v) => `${v}%`} domain={[0, 100]} />
                                            <RechartsTooltip content={<CustomTooltip />} />
                                            <Area type="monotone" dataKey="risk_score_percentage" stroke="#818cf8" strokeWidth={3} fillOpacity={1} fill="url(#colorRisk)" activeDot={{ r: 6, fill: "#818cf8", stroke: "#1e293b", strokeWidth: 2 }} />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                </Box>
                            )}
                        </CardContent>
                    </Card>
                </Grid>

                {/* Tabla de miembros */}
                <Grid item xs={12} md={5}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" fontWeight={700} mb={0.5}>
                                Miembros del workspace
                            </Typography>
                            <Typography variant="caption" color="text.secondary" display="block" mb={2}>
                                🔒 Solo aliases · Sin datos personales identificables
                            </Typography>
                            {membersQuery.isLoading ? (
                                <Skeleton variant="rounded" height={120} />
                            ) : members.length === 0 ? (
                                <Typography color="text.secondary" fontSize={14}>
                                    Sin miembros registrados en este workspace.
                                </Typography>
                            ) : (
                                <TableContainer component={Paper} elevation={0}
                                    sx={{ bgcolor: "rgba(255,255,255,0.02)", borderRadius: 2 }}>
                                    <Table size="small">
                                        <TableHead>
                                            <TableRow>
                                                <TableCell sx={{ color: "text.secondary", fontSize: 11, fontWeight: 700 }}>Alias</TableCell>
                                                <TableCell sx={{ color: "text.secondary", fontSize: 11, fontWeight: 700 }}>Estado</TableCell>
                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            {members.map((m, i) => (
                                                <TableRow key={i}>
                                                    <TableCell sx={{ fontSize: 13, color: "text.secondary" }}>
                                                        👤 {m.alias}
                                                    </TableCell>
                                                    <TableCell>
                                                        <Chip
                                                            label="Incluido en análisis"
                                                            size="small"
                                                            color="success"
                                                            variant="outlined"
                                                            sx={{ fontSize: 10 }}
                                                        />
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </TableContainer>
                            )}
                        </CardContent>
                    </Card>
                </Grid>

                {/* Pesos del modelo */}
                {riskData?.weights_used && Object.keys(riskData.weights_used).length > 0 && (
                    <Grid item xs={12} md={7}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" fontWeight={700} mb={0.5}>
                                    Pesos del modelo de correlación
                                </Typography>
                                <Typography variant="caption" color="text.secondary" display="block" mb={2}>
                                    Importancia relativa de cada emoción · Calculado dinámicamente
                                </Typography>
                                <Grid container spacing={1}>
                                    {Object.entries(riskData.weights_used).map(([k, v]) => (
                                        <Grid item xs={6} sm={4} key={k}>
                                            <Box sx={{
                                                p: 1.5, borderRadius: 2,
                                                bgcolor: "rgba(255,255,255,0.04)", textAlign: "center"
                                            }}>
                                                <Typography variant="caption" color="text.secondary" display="block">
                                                    {k.replace(/_/g, " ")}
                                                </Typography>
                                                <Typography variant="h6" color="primary.light" fontWeight={700}>
                                                    {fmtPct(v)}
                                                </Typography>
                                            </Box>
                                        </Grid>
                                    ))}
                                </Grid>
                            </CardContent>
                        </Card>
                    </Grid>
                )}

                {/* Info NLP Explicativa */}
                <Grid item xs={12}>
                    <Card sx={{ bgcolor: "rgba(99, 102, 241, 0.04)", border: "1px solid rgba(99, 102, 241, 0.1)" }}>
                        <CardContent>
                            <Typography variant="subtitle2" color="primary.light" fontWeight={700} mb={1} display="flex" alignItems="center" gap={1}>
                                🧠 ¿Cómo calcula la IA este riesgo?
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                                Nuestro modelo procesa los mensajes de este equipo usando técnicas de Procesamiento de Lenguaje Natural (NLP).
                                Primero clasificamos las frases mediante modelos transformer (tipo BERT) en 6 dimensiones emocionales: <em>Estrés, Carga Cognitiva, Sensación de Aislamiento, Conflictividad, etc</em>.
                                <br /><br />
                                Luego, se aplica un algoritmo de <strong>Ponderación Dinámica</strong>: no todas las emociones pesan igual; el sistema otorga mayor gravedad a combinaciones críticas (ej. Estrés + Aislamiento), y resta severidad si detecta indicadores de alivio emocional, devolviendo un <strong>Risk Score</strong> de 0 a 100%.
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        </Box>
    );
}
