import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
    Box, Typography, Card, CardContent, Button, Alert, Skeleton,
    ToggleButtonGroup, ToggleButton, Divider, Paper
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import LockIcon from "@mui/icons-material/Lock";
import {
    fetchEmployeeProfile,
    fetchEmployeeTrend
} from "../../api/backend";
import RiskCard from "../../components/RiskCard";
import RiskTrendChart from "../../components/RiskTrendChart";
import "./EmployeeProfilePage.css";

const DAY_OPTIONS = [1, 7, 30, 60];
const DAY_LABEL = { 1: "24h", 7: "7 Días", 30: "30 Días", 60: "60 Días" };

export default function EmployeeProfilePage() {
    const { email } = useParams();
    const navigate = useNavigate();
    const [days, setDays] = useState(7);

    console.log("[EmployeeProfile] Mostrando perfil:", email);

    const profileQuery = useQuery({
        queryKey: ["employeeProfile", email, days],
        queryFn: () => fetchEmployeeProfile(email, days),
        staleTime: 60_000,
    });

    const trendQuery = useQuery({
        queryKey: ["employeeTrend", email, days],
        queryFn: () => fetchEmployeeTrend(email, days),
        staleTime: 60_000,
    });

    const profile = profileQuery.data;
    const trendData = trendQuery.data?.trend ?? [];

    if (profileQuery.error?.status === 403) {
        return (
            <Box sx={{ p: 4 }}>
                <Alert severity="error" icon={<LockIcon />}>
                    No tienes permiso para ver el perfil de este empleado.
                </Alert>
            </Box>
        );
    }

    if (profileQuery.isError) {
        return (
            <Box sx={{ p: 4 }}>
                <Alert severity="error">
                    Error al cargar el perfil: {profileQuery.error?.message || "Error desconocido"}
                </Alert>
            </Box>
        );
    }


    return (
        <Box className="project-detail-container">
            <Button
                startIcon={<ArrowBackIcon />}
                onClick={() => navigate(-1)}
                className="project-detail-back-btn"
            >
                Volver
            </Button>

            {/* Header */}
            <Box sx={{ mb: 4 }}>
                {profileQuery.isLoading ? (
                    <Skeleton width={300} height={40} />
                ) : (
                    <>
                        <Typography variant="h4" fontWeight={400} sx={{ mb: 0.5 }}>
                            {profile?.display_name}
                        </Typography>
                        <Typography variant="body1" color="text.secondary">
                            {profile?.role === 'manager' ? 'Manager' : 'Employee'} · {email}
                        </Typography>
                    </>
                )}
            </Box>

            {/* Controles */}
            <Box sx={{ display: "flex", justifyContent: "space-between", mb: 3 }}>
                <Typography variant="body2" color="text.secondary">
                    Análisis de los últimos {days} días
                </Typography>
                <ToggleButtonGroup
                    value={days}
                    exclusive
                    onChange={(_, v) => v && setDays(v)}
                    size="small"
                >
                    {DAY_OPTIONS.map((d) => (
                        <ToggleButton key={d} value={d} sx={{ px: 2, fontSize: 12 }}>
                            {DAY_LABEL[d]}
                        </ToggleButton>
                    ))}
                </ToggleButtonGroup>
            </Box>

            <Box sx={{ display: "flex", flexDirection: "column", gap: 4 }}>
                {/* Riesgo Global */}
                <Box>
                    <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
                        Riesgo Global Consolidado
                    </Typography>
                    {profileQuery.isLoading ? (
                        <Skeleton variant="rounded" height={180} />
                    ) : (
                        <RiskCard
                            riskLevel={profile?.risk_level}
                            riskScore={profile?.global_risk}
                            sampleSize={1}
                        />
                    )}
                </Box>

                {/* Evolución */}
                <Box>
                    <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
                        Evolución del Bienestar
                    </Typography>
                    <Card sx={{ bgcolor: "transparent", backgroundImage: "none", border: "none", boxShadow: "none" }}>
                        <CardContent sx={{ p: 0 }}>
                            {trendQuery.isLoading ? (
                                <Skeleton variant="rounded" height={220} />
                            ) : trendData.length === 0 ? (
                                <Paper variant="outlined" sx={{ p: 4, textAlign: "center", bgcolor: "transparent", borderStyle: "dashed" }}>
                                    <Typography variant="body2" color="text.secondary">Sin datos históricos suficientes</Typography>
                                </Paper>
                            ) : (
                                <Box sx={{ mt: 2 }}>
                                    <RiskTrendChart data={trendData} days={days} />
                                </Box>
                            )}
                        </CardContent>
                    </Card>
                </Box>

                {/* Proyectos */}
                <Box>
                    <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
                        Desglose por Proyectos Activos
                    </Typography>
                    {profileQuery.isLoading ? (
                        <Skeleton variant="rounded" height={100} />
                    ) : (
                        <Box className="member-table">
                            <Box className="member-table-header">
                                <Typography variant="caption" className="member-table-header-cell">Proyecto</Typography>
                                <Typography variant="caption" className="member-table-header-cell" align="right">Riesgo Detectado</Typography>
                            </Box>
                            {profile?.projects?.map((p) => {
                                const projectColor =
                                    p.project_risk === null || p.project_risk === undefined
                                        ? "#94a3b8"
                                        : p.project_risk >= 35
                                            ? "#ef4444"
                                            : p.project_risk >= 20
                                                ? "#f59e0b"
                                                : "#22c55e";
                                return (
                                    <Box key={p.project_id} className="member-table-row" sx={{ gridTemplateColumns: "1fr 100px" }}>
                                        <Typography variant="body2" sx={{ fontWeight: 500 }}>{p.project_name}</Typography>
                                        <Typography variant="body2" sx={{ textAlign: "right", fontWeight: 700, color: projectColor }}>
                                            {p.project_risk}%
                                        </Typography>
                                    </Box>
                                );
                            })}
                        </Box>
                    )}
                </Box>
            </Box>
        </Box>
    );
}
