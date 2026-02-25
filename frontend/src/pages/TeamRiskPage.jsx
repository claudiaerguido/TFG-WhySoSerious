import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
    Box, Typography, FormControl, Select, MenuItem, InputLabel,
    ToggleButton, ToggleButtonGroup, Grid, Card, CardContent,
    Alert, Skeleton, Divider,
} from "@mui/material";
import { fetchTeamRisk, fetchTeams, fetchTeamTrend } from "../api/backend";
import RiskCard from "../components/RiskCard";
import {
    ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
} from "recharts";

const DAYS_OPTIONS = [7, 30, 60];
const LEVEL_BG = { Verde: "#10b98122", Amarillo: "#f59e0b22", Rojo: "#ef444422" };

export default function TeamRiskPage() {
    const [teamId, setTeamId] = useState(1);
    const [days, setDays] = useState(30);

    const teamsQuery = useQuery({ queryKey: ["teams"], queryFn: fetchTeams, staleTime: 300_000 });
    const riskQuery = useQuery({
        queryKey: ["teamRisk", teamId, days],
        queryFn: () => fetchTeamRisk(teamId, days),
        enabled: !!teamId,
        staleTime: 30_000,
    });
    const trendQuery = useQuery({
        queryKey: ["teamTrend", teamId, days],
        queryFn: () => fetchTeamTrend(teamId, days),
        enabled: !!teamId,
        staleTime: 30_000,
    });

    const teams = teamsQuery.data?.teams ?? [];
    const riskData = riskQuery.data;
    const trendData = trendQuery.data?.trend ?? [];

    // Comparativa vs semana anterior (simulada sobre los datos de tendencia)
    const prevScore = trendData.length >= 2
        ? trendData[trendData.length - 2]?.risk_score_percentage ?? null
        : null;

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <Box sx={{ bgcolor: "background.paper", p: 1.5, border: "1px solid rgba(255,255,255,0.1)", borderRadius: 1 }}>
                    <Typography variant="caption" color="text.secondary">{label}</Typography>
                    <Typography variant="body2" fontWeight={700} color="primary.light">
                        {payload[0].value}%
                    </Typography>
                </Box>
            );
        }
        return null;
    };

    return (
        <Box sx={{ maxWidth: 1200, mx: "auto", px: { xs: 0, sm: 1 } }}>
            {/* Header */}
            <Box mb={4}>
                <Typography variant="h5" fontWeight={700}>Riesgo por Equipo</Typography>
                <Typography variant="body2" color="text.secondary" mt={0.5}>
                    Indicador de bienestar agregado del equipo · Sin datos individuales
                </Typography>
            </Box>

            {/* Controles */}
            <Grid container spacing={2} mb={4} alignItems="center">
                <Grid item xs={12} sm={5}>
                    <FormControl fullWidth size="small">
                        <InputLabel>Equipo</InputLabel>
                        <Select
                            value={teamId}
                            label="Equipo"
                            onChange={(e) => setTeamId(Number(e.target.value))}
                        >
                            {teams.length === 0 && <MenuItem value={1}>Equipo 1 (por defecto)</MenuItem>}
                            {teams.map((t) => (
                                <MenuItem key={t.id} value={t.id}>{t.name}</MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                </Grid>

                <Grid item xs={12} sm={7}>
                    <ToggleButtonGroup
                        value={days}
                        exclusive
                        onChange={(_, v) => v && setDays(v)}
                        size="small"
                    >
                        {DAYS_OPTIONS.map((d) => (
                            <ToggleButton key={d} value={d} sx={{ px: 3, fontWeight: 600 }}>
                                {d} días
                            </ToggleButton>
                        ))}
                    </ToggleButtonGroup>
                </Grid>
            </Grid>

            <Grid container spacing={3}>
                {/* Tarjeta semáforo */}
                <Grid item xs={12} md={5}>
                    {riskQuery.isLoading ? (
                        <Skeleton variant="rounded" height={200} />
                    ) : riskQuery.isError ? (
                        <Alert severity="error">Error al cargar los datos del equipo. ¿Está el backend corriendo?</Alert>
                    ) : (
                        <RiskCard
                            riskLevel={riskData?.risk_level}
                            riskScore={riskData?.risk_score_percentage}
                            sampleSize={riskData?.sample_size}
                            prevScore={prevScore}
                        />
                    )}

                    {/* Pesos usados */}
                    {riskData?.weights_used && (
                        <Card sx={{ mt: 2, bgcolor: "rgba(255,255,255,0.03)" }}>
                            <CardContent>
                                <Typography variant="caption" color="text.secondary" fontWeight={700} display="block" mb={1}>
                                    Pesos de correlación usados
                                </Typography>
                                {Object.entries(riskData.weights_used).map(([k, v]) => (
                                    <Box key={k} sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
                                        <Typography variant="caption" color="text.secondary">{k.replace("_", " ")}</Typography>
                                        <Typography variant="caption" color="primary.light" fontWeight={700}>
                                            {(v * 100).toFixed(1)}%
                                        </Typography>
                                    </Box>
                                ))}
                            </CardContent>
                        </Card>
                    )}
                </Grid>

                {/* Gráfica de tendencia */}
                <Grid item xs={12} md={7}>
                    <Card sx={{ height: "100%", minHeight: 300 }}>
                        <CardContent>
                            <Typography variant="h6" fontWeight={700} mb={2}>
                                Tendencia — últimos {days} días
                            </Typography>
                            {trendQuery.isLoading ? (
                                <Skeleton variant="rounded" height={220} />
                            ) : trendData.length === 0 ? (
                                <Box sx={{
                                    height: 220, display: "flex", alignItems: "center", justifyContent: "center",
                                    color: "text.secondary", fontSize: 14, textAlign: "center",
                                }}>
                                    Sin suficientes datos históricos para mostrar la tendencia.<br />
                                    El gráfico aparecerá después de varios análisis nocturnos.
                                </Box>
                            ) : (
                                <Box sx={{ height: 240, mt: 1 }}>
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={trendData} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                                            <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickMargin={8} minTickGap={15} />
                                            <YAxis stroke="#64748b" fontSize={11} tickFormatter={(v) => `${v}%`} domain={[0, 100]} />
                                            <RechartsTooltip content={<CustomTooltip />} />
                                            <Line
                                                type="monotone"
                                                dataKey="risk_score_percentage"
                                                stroke="#818cf8"
                                                strokeWidth={2}
                                                dot={false}
                                                activeDot={{ r: 4, fill: "#818cf8", stroke: "#1e293b", strokeWidth: 2 }}
                                            />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </Box>
                            )}
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        </Box>
    );
}
