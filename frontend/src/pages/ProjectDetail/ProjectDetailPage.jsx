import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  Box, Typography, Card, CardContent, Button, Chip,
  Alert, Skeleton, ToggleButtonGroup, ToggleButton,
  LinearProgress, Accordion, AccordionSummary, AccordionDetails
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import RefreshIcon from "@mui/icons-material/Refresh";
import LockIcon from "@mui/icons-material/Lock";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import {
  fetchWorkspaceRisk, fetchWorkspaceTrend,
  fetchWorkspaceMembers, fetchWorkspaceMemberRisks, triggerAnalysis, fetchMyWorkspaces
} from "../../api/backend";
import RiskCard from "../../components/RiskCard";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip
} from "recharts";
import "./ProjectDetailPage.css";

const DAY_OPTIONS = [1, 7, 30, 60];
const DAY_LABEL = { 1: "Hoy", 7: "7 Días", 30: "30 Días", 60: "60 Días" };

export default function ProjectDetailPage() {
  const { id } = useParams();
  const workspaceId = Number(id) || 1;
  const navigate = useNavigate();
  const [days, setDays] = useState(7);

  const { data: workspacesData } = useQuery({
    queryKey: ["myWorkspaces"],
    queryFn: fetchMyWorkspaces,
    staleTime: 60_000,
  });

  const wsInfo = workspacesData?.workspaces?.find(w => w.id === workspaceId);

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

  const memberRisksQuery = useQuery({
    queryKey: ["workspaceMemberRisks", workspaceId, days],
    queryFn: () => fetchWorkspaceMemberRisks(workspaceId, days),
    staleTime: 30_000,
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
      <Box className="project-detail-container">
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate("/teams")}
          className="project-detail-back-btn">
          Volver a Mis Equipos
        </Button>
        <Alert severity="error" icon={<LockIcon />} sx={{ borderRadius: 2 }}>
          No tienes permiso para ver este workspace. Contacta con tu manager.
        </Alert>
      </Box>
    );
  }

  const level = riskData?.risk_level;

  // Custom Tooltip for Recharts
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <Box className="project-detail-tooltip">
          <Typography variant="caption" color="text.secondary">{label}</Typography>
          <Typography variant="body2" fontWeight={700} sx={{ color: "#818cf8" }}>
            Riesgo: {payload[0].value}%
          </Typography>
        </Box>
      );
    }
    return null;
  }

  // Trend variation
  let variationText = "—";
  if (trendData.length > 1) {
    const first = trendData[0].risk_score_percentage;
    const last = trendData[trendData.length - 1].risk_score_percentage;
    const diff = (last - first).toFixed(1);
    variationText = diff > 0 ? `+${diff}%` : `${diff}%`;
  }

  return (
    <Box className="project-detail-container">
      <Button startIcon={<ArrowBackIcon />} onClick={() => navigate("/teams")}
        className="project-detail-back-btn">
        Volver a Mis Equipos
      </Button>

      {/* Header Limpio */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={400} sx={{ mb: 1, color: "text.primary" }}>
          {wsInfo ? wsInfo.name : `Workspace #${workspaceId}`}
          <Typography component="span" variant="h5" color="text.secondary" fontWeight={300}>
            {wsInfo ? ` — ${wsInfo.type === 'team' ? 'Equipo' : 'Proyecto'}` : ""}
          </Typography>
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ display: "flex", gap: 1, alignItems: "center" }}>
          {members.length} miembros · {riskData?.sample_size ? `${riskData.sample_size} msjs analizados` : "0 msjs analizados"}
        </Typography>
      </Box>

      {/* Controles de Acción (Periodo + Refrescar) */}
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 3, flexWrap: "wrap", gap: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Periodo: {days === 1 ? "Solo hoy" : `últimos ${days} días`}
        </Typography>
        <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
          <ToggleButtonGroup value={days} exclusive onChange={(_, v) => v && setDays(v)} size="small">
            {DAY_OPTIONS.map((d) => (
              <ToggleButton key={d} value={d} sx={{ px: 2, fontSize: 13, textTransform: "none" }}>{DAY_LABEL[d]}</ToggleButton>
            ))}
          </ToggleButtonGroup>
          <Button
            variant="outlined"
            color="inherit"
            startIcon={<RefreshIcon />}
            onClick={() => triggerMutation.mutate()}
            disabled={triggerMutation.isPending}
            size="small"
            sx={{ textTransform: "none", borderColor: "rgba(255,255,255,0.1)", color: "text.secondary" }}
          >
            {triggerMutation.isPending ? "Analizando…" : "Actualizar"}
          </Button>
        </Box>
      </Box>

      {triggerMutation.isSuccess && (
        <Alert severity="success" sx={{ mb: 3, borderRadius: 2 }}>
          Análisis lanzado en segundo plano. Los datos se actualizarán en breve.
        </Alert>
      )}

      <Box sx={{ display: "flex", flexDirection: "column", gap: 4 }}>

        {/* BLOQUE PRINCIPAL: Riesgo Actual */}
        <Box>
          <Typography variant="h6" fontWeight={700} sx={{ mb: 0.5, color: "text.primary" }}>
            Salud del equipo
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Indicador actual por miembros
          </Typography>
          {riskQuery.isLoading ? (
            <Skeleton variant="rounded" height={200} sx={{ borderRadius: 3 }} />
          ) : (
            <RiskCard
              riskLevel={level}
              riskScore={riskData?.risk_score_percentage}
              sampleSize={members.length}
            />
          )}
        </Box>

        {/* BLOQUE: Tendencia (Línea fina) */}
        <Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Evolución diaria por mensajes
          </Typography>
          <Card sx={{ bgcolor: "transparent", backgroundImage: "none", border: "none", boxShadow: "none" }}>
            <CardContent sx={{ p: 0, pb: "0 !important" }}>
              {trendQuery.isLoading ? (
                <Skeleton variant="rounded" height={200} sx={{ borderRadius: 3 }} />
              ) : trendData.length === 0 ? (
                <Box sx={{ height: 200, display: "flex", alignItems: "center", justifyContent: "center", color: "text.secondary", border: "1px dashed rgba(255,255,255,0.1)", borderRadius: 3 }}>
                  Sin suficientes datos históricos.
                </Box>
              ) : (
                <Box sx={{ height: 260 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.02)" vertical={false} />
                      <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickMargin={10} minTickGap={30} axisLine={false} tickLine={false} />
                      <YAxis stroke="#64748b" fontSize={11} tickFormatter={(v) => `${v}%`} domain={[0, 100]} axisLine={false} tickLine={false} />
                      <RechartsTooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(255,255,255,0.1)', strokeWidth: 1 }} />
                      <Line type="monotone" dataKey="risk_score_percentage" stroke="#818cf8" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: "#818cf8", stroke: "#1e293b", strokeWidth: 2 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </Box>
              )}
              {trendData.length > 1 && (
                <Typography variant="caption" sx={{ color: "text.secondary", display: "block", mt: 1, textAlign: "center" }}>
                  Variación en el periodo: {variationText}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Box>



        {/* BLOQUE: Riesgo por miembro */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" fontWeight={700} sx={{ color: "text.primary", mb: 0.5 }}>
            Riesgo por miembro
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Últimos {days} días · score 0–100 · ordenado por riesgo
          </Typography>
          <Card sx={{
            bgcolor: "rgba(255,255,255,0.02)",
            border: "1px solid rgba(255,255,255,0.06)",
            borderRadius: 3, boxShadow: "none",
          }}>
            <CardContent sx={{ p: 2.5, "&:last-child": { pb: 2.5 } }}>
              {memberRisksQuery.isLoading ? (
                [1, 2, 3].map(i => <Skeleton key={i} width="100%" height={36} sx={{ mb: 1.2, borderRadius: 2 }} />)
              ) : (memberRisksQuery.data?.members ?? []).length === 0 ? (
                <Typography variant="body2" color="text.disabled">Sin datos de miembros.</Typography>
              ) : (
                <Box sx={{ display: "flex", flexDirection: "column", gap: 1.4 }}>
                  {(memberRisksQuery.data?.members ?? []).map((m, idx) => {
                    const pct = m.risk_score_percentage;
                    const noData = pct === null || m.message_count === 0;
                    const color = noData ? "#6b7280"
                      : pct >= 35 ? "#ef4444"
                        : pct >= 20 ? "#f59e0b"
                          : "#22c55e";
                    const isTop = idx === 0 && !noData && pct >= 20;
                    return (
                      <Box key={m.alias} sx={{
                        display: "grid",
                        gridTemplateColumns: "160px 1fr auto",
                        alignItems: "center",
                        gap: 2,
                        opacity: noData ? 0.4 : 1,
                      }}>
                        {/* Columna izquierda: alias + icono top */}
                        <Box sx={{ display: "flex", alignItems: "center", gap: 0.6, overflow: "hidden" }}>
                          {isTop && (
                            <Typography component="span" sx={{ fontSize: 13, lineHeight: 1 }}>⚠️</Typography>
                          )}
                          <Typography variant="body2" fontWeight={600} color="text.primary" noWrap>
                            {m.alias}
                          </Typography>
                        </Box>

                        {/* Columna centro: barra */}
                        {noData ? (
                          <Typography variant="caption" color="text.disabled" sx={{ fontStyle: "italic" }}>
                            Sin mensajes en el periodo
                          </Typography>
                        ) : (
                          <Box sx={{ maxWidth: 320 }}>
                            <LinearProgress
                              variant="determinate"
                              value={pct ?? 0}
                              sx={{
                                height: 3,
                                borderRadius: 3,
                                bgcolor: "rgba(255,255,255,0.06)",
                                "& .MuiLinearProgress-bar": { bgcolor: color, borderRadius: 3 },
                              }}
                            />
                          </Box>
                        )}

                        {/* Columna derecha: % en color + msgs en gris */}
                        <Box sx={{ display: "flex", alignItems: "baseline", gap: 0.5, minWidth: 120, justifyContent: "flex-end" }}>
                          <Typography variant="body2" fontWeight={700} sx={{ color }}>
                            {noData ? "—" : `${pct}%`}
                          </Typography>
                          {!noData && (
                            <Typography variant="caption" color="text.disabled">
                              · {m.message_count} msgs
                            </Typography>
                          )}
                        </Box>
                      </Box>
                    );
                  })}
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>


        {/* BLOQUE: Miembros incluidos */}
        <Box>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1.5 }}>
            <Typography variant="subtitle1" fontWeight={600} sx={{ color: "text.primary", letterSpacing: 0.5 }}>
              MIEMBROS INCLUIDOS EN ANÁLISIS
            </Typography>
            <Typography variant="caption" sx={{ color: "text.disabled" }}>
              🔒 Solo aliases visualizados
            </Typography>
          </Box>
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
            {membersQuery.isLoading ? (
              <Skeleton variant="rounded" width="100%" height={40} sx={{ borderRadius: 2 }} />
            ) : members.length === 0 ? (
              <Typography variant="body2" color="text.secondary">Sin miembros registrados.</Typography>
            ) : (
              members.map((m, i) => (
                <Box key={i} sx={{
                  display: "flex", alignItems: "center", gap: 1,
                  p: 1, px: 1.5,
                  border: "1px solid rgba(255,255,255,0.05)",
                  borderRadius: 2,
                  bgcolor: "rgba(255,255,255,0.01)"
                }}>
                  <Typography variant="body2" color="text.primary" fontWeight={500}>
                    {m.alias}
                  </Typography>
                  <Chip label="Incluido" size="small" sx={{ height: 18, fontSize: 10, bgcolor: "rgba(16,185,129,0.1)", color: "#10b981", border: "none" }} />
                </Box>
              ))
            )}
          </Box>
        </Box>

        {/* BLOQUE: Metodología plegable */}
        <Accordion sx={{
          bgcolor: "transparent",
          boxShadow: "none",
          "&:before": { display: "none" },
          mt: 2
        }}>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon sx={{ color: "text.secondary" }} />}
            sx={{ px: 0, minHeight: 48, "& .MuiAccordionSummary-content": { my: 0 } }}
          >
            <Typography variant="body2" color="text.secondary" sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <InfoOutlinedIcon fontSize="small" /> ¿Cómo se calcula el riesgo?
            </Typography>
          </AccordionSummary>
          <AccordionDetails sx={{ px: 0, pb: 4, pt: 0 }}>
            <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6, maxWidth: 900 }}>
              Nuestro modelo procesa los mensajes codificados del equipo usando transformadores lingüísticos (base RoBERTa), clasificando el texto de forma estructural en diferentes dimensiones emocionales. El algoritmo de <strong>Ponderación Dinámica</strong> evalúa cómo interactúan y qué gravedad implican estas emociones, devolviendo un Índice de Riesgo global. Todo el proceso es "Privacy by Design" y anonimizado en origen.
            </Typography>
          </AccordionDetails>
        </Accordion>

      </Box>
    </Box>
  );
}

