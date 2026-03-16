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
import { useLocation } from "react-router-dom";
import {
  fetchTeamRisk, fetchTeamTrend,
  fetchProjectRisk, fetchProjectTrend,
  fetchTeamMemberBreakdown,
  triggerAnalysis, fetchMyTeamsAndProjects
} from "../../api/backend";
import RiskCard from "../../components/RiskCard";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip
} from "recharts";
import "./ProjectDetailPage.css";

const DAY_OPTIONS = [1, 7, 30, 60];
const DAY_LABEL = { 1: "Hoy", 7: "7 Días", 30: "30 Días", 60: "60 Días" };

function MemberRiskRow({ member, type, days }) {
  const [expanded, setExpanded] = useState(false);
  const { data: breakdown, isLoading } = useQuery({
    queryKey: ["memberBreakdown", member.email, days],
    queryFn: () => fetchTeamMemberBreakdown(member.email, days),
    enabled: expanded && type === "team" && !member.projects, // Solo si el backend no lo incluyó ya
    staleTime: 60_000,
  });

  const displayBreakdown = member.projects || breakdown || [];

  const pct = type === "team" ? member.global_risk : member.project_risk;
  const noData = pct === null || pct === undefined;
  const color = noData ? "#6b7280" : pct >= 35 ? "#ef4444" : pct >= 20 ? "#f59e0b" : "#22c55e";

  return (
    <Card sx={{ bgcolor: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 3, boxShadow: "none" }}>
      <Box sx={{ p: 2, display: "flex", alignItems: "center", gap: 2 }}>
        <Box sx={{ flex: 1 }}>
          <Typography variant="body2" fontWeight={700} color="text.primary">
            {member.display_name || member.alias}
          </Typography>
          <Typography variant="caption" color="text.disabled">{type === "team" ? "Riesgo Global" : "Riesgo Táctico"}</Typography>
        </Box>
        <Box sx={{ width: 120 }}>
          <LinearProgress variant="determinate" value={pct ?? 0} sx={{ height: 4, borderRadius: 2, bgcolor: "rgba(255,255,255,0.05)", "& .MuiLinearProgress-bar": { bgcolor: color } }} />
        </Box>
        <Typography variant="body2" fontWeight={800} sx={{ color, minWidth: 45, textAlign: "right" }}>
          {noData ? "—" : `${pct}%`}
        </Typography>
        {type === "team" && (
          <Button size="small" variant="text" color="inherit" onClick={() => setExpanded(!expanded)} sx={{ minWidth: 32, p: 0.5, color: "text.secondary" }}>
            <ExpandMoreIcon sx={{ transform: expanded ? "rotate(180deg)" : "none", transition: "0.2s" }} />
          </Button>
        )}
      </Box>

      {expanded && type === "team" && (
        <Box sx={{ px: 2, pb: 2, pt: 1, borderTop: "1px solid rgba(255,255,255,0.04)" }}>
          <Typography variant="caption" color="text.disabled" fontWeight={700} sx={{ mb: 1, display: "block" }}>
            DESGLOSE POR PROYECTO
          </Typography>
          {isLoading ? <LinearProgress sx={{ mt: 1 }} /> : displayBreakdown.length === 0 ? (
            <Typography variant="caption" color="text.disabled">Sin proyectos activos en este periodo.</Typography>
          ) : (
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
              {displayBreakdown.map(p => (
                <Box key={p.project_id} sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <Typography variant="caption" color="text.primary">{p.project_name}</Typography>
                  <Typography variant="caption" fontWeight={700} sx={{ color: p.project_risk >= 20 ? "#f59e0b" : "#22c55e" }}>
                    {p.project_risk === null || p.project_risk === undefined ? "—" : `${p.project_risk}%`}
                  </Typography>
                </Box>
              ))}
            </Box>
          )}
        </Box>
      )}
    </Card>
  );
}

export default function ProjectDetailPage() {
  const { id } = useParams();
  const itemId = Number(id);
  const navigate = useNavigate();
  const location = useLocation();
  const type = location.pathname.includes("/team/") ? "team" : "project";
  const [days, setDays] = useState(7);

  const riskQuery = useQuery({
    queryKey: [type === "team" ? "teamRisk" : "projectRisk", itemId, days],
    queryFn: () => type === "team" ? fetchTeamRisk(itemId, days) : fetchProjectRisk(itemId, days),
    staleTime: 30_000,
  });

  const trendQuery = useQuery({
    queryKey: [type === "team" ? "teamTrend" : "projectTrend", itemId, days],
    queryFn: () => type === "team" ? fetchTeamTrend(itemId, days) : fetchProjectTrend(itemId, days),
    staleTime: 30_000,
  });

  const triggerMutation = useMutation({ mutationFn: triggerAnalysis });

  const riskData = riskQuery.data;
  const trendData = trendQuery.data?.trend ?? [];

  if (import.meta.env.DEV && riskData) {
    console.log(`[WorkspaceDetail ${itemId}] payload:`, riskData);
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
        Volver a Equipos y Proyectos
      </Button>

      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={400} sx={{ mb: 1, color: "text.primary" }}>
          {type === 'team' ? 'Equipo' : 'Proyecto'} #{itemId}
          <Typography component="span" variant="h5" color="text.secondary" fontWeight={300}>
            {type === 'team' ? " — Riesgo Global" : " — Riesgo Táctico"}
          </Typography>
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ display: "flex", gap: 1, alignItems: "center" }}>
          {riskData?.members?.length ?? 0} miembros
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
            {type === 'team' ? 'Bienestar Organizativo' : 'Indicador del Proyecto'}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {type === 'team' ? 'Riesgo medio global de los miembros' : 'Influencia del proyecto en el agotamiento'}
          </Typography>
          {riskQuery.isLoading ? (
            <Skeleton variant="rounded" height={200} sx={{ borderRadius: 3 }} />
          ) : (
            <RiskCard
              riskLevel={level}
              riskScore={riskData?.risk_score_percentage}
              sampleSize={riskData?.members?.length ?? 0}
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



        {/* BLOQUE: Detalle por Miembro */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" fontWeight={700} sx={{ color: "text.primary", mb: 0.5 }}>
            {type === 'team' ? 'Desglose por Miembro' : 'Riesgo en el Proyecto'}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {type === 'team'
              ? 'Muestra el riesgo global del empleado y sus proyectos activos'
              : 'Riesgo contextual del empleado dentro de este proyecto específico'}
          </Typography>

          {riskQuery.isLoading ? (
            <Skeleton variant="rounded" height={200} sx={{ borderRadius: 2 }} />
          ) : (
            <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
              {(riskData?.members ?? []).map((m) => (
                <MemberRiskRow key={m.alias} member={m} type={type} days={days} />
              ))}
            </Box>
          )}
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
              {type === 'team'
                ? "El riesgo global del equipo se calcula como la media de los niveles de estrés detectados en las comunicaciones de sus miembros en todos sus contextos de trabajo. Es un indicador de bienestar general a largo plazo."
                : "El riesgo táctico del proyecto evalúa específicamente cómo los mensajes intercambiados dentro de este proyecto afectan al agotamiento de los participantes, permitiendo identificar fricciones en entregas o flujos de trabajo específicos."}
              <br /><br />
              Nuestro modelo procesa los mensajes codificados usando transformadores lingüísticos (base RoBERTa), clasificando el texto en dimensiones emocionales. Todo el proceso es "Privacy by Design" y anonimizado en origen.
            </Typography>
          </AccordionDetails>
        </Accordion>

      </Box>
    </Box>
  );
}

