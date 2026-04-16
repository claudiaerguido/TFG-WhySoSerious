import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Box, Typography, Card, CardContent, Button, Chip,
  Alert, Skeleton, ToggleButtonGroup, ToggleButton,
  LinearProgress, Accordion, AccordionSummary, AccordionDetails,
  Divider, Paper, TextField
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
  triggerAnalysis, fetchMyTeamsAndProjects,
  fetchProjectsCatalog, addProjectMember, removeProjectMember
} from "../../api/backend";
import { useMe } from "../../context/AuthContext";
import RiskCard from "../../components/RiskCard";
import IconButton from "@mui/material/IconButton";
import DeleteIcon from "@mui/icons-material/Delete";
import AddIcon from "@mui/icons-material/Add";
import { MenuItem, Select, FormControl } from "@mui/material";
import RiskTrendChart from "../../components/RiskTrendChart";
import { useRiskFilters } from "../../hooks/useRiskFilters";
import "./ProjectDetailPage.css";

const DAY_OPTIONS = [1, 7, 30, 60];
const DAY_LABEL = { 1: "Últimas 24h", 7: "7 Días", 30: "30 Días", 60: "60 Días", "fiscal": "FY Actual", "fiscal-prev": "FY Anterior" };

function MemberRiskRow({ member, type, days, rangeMode = "preset", customRange = {} }) {
  const { id: teamId } = useParams();
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState(false);
  const [selectedProject, setSelectedProject] = useState("");
  const { user } = useMe();
  const queryClient = useQueryClient();

  const memberEmail = member.email || member.user_email;
  const canManage = user?.role === "admin" || (user?.role === "manager" && type === "team");

  const queryStart = rangeMode === "custom" ? customRange.start : null;
  const queryEnd = rangeMode === "custom" ? customRange.end : null;

  const { data: breakdown, isLoading } = useQuery({
    queryKey: ["memberBreakdown", memberEmail, days, rangeMode, queryStart, queryEnd],
    queryFn: () => fetchTeamMemberBreakdown(memberEmail, days, queryStart, queryEnd),
    enabled: expanded && type === "team" && !member.projects,
    staleTime: 60_000,
  });

  const { data: catalog } = useQuery({
    queryKey: ["projectsCatalog"],
    queryFn: fetchProjectsCatalog,
    enabled: expanded && canManage,
    staleTime: 300_000,
  });

  const addMutation = useMutation({
    mutationFn: (pid) => addProjectMember(memberEmail, pid),
    onSuccess: () => {
      const numericId = Number(teamId);
      // Invalidamos por prefijo para que afecte a todos los filtros de tiempo (7, 30, 60 días, etc.)
      queryClient.invalidateQueries({ queryKey: ["memberBreakdown", memberEmail] });
      queryClient.invalidateQueries({ queryKey: ["teamRisk", numericId] });
      queryClient.invalidateQueries({ queryKey: ["projectRisk", numericId] });
      setSelectedProject("");
    },
  });

  const removeMutation = useMutation({
    mutationFn: (pid) => removeProjectMember(memberEmail, pid),
    onSuccess: () => {
      const numericId = Number(teamId);
      // Invalidamos por prefijo para que afecte a todos los filtros de tiempo
      queryClient.invalidateQueries({ queryKey: ["memberBreakdown", memberEmail] });
      queryClient.invalidateQueries({ queryKey: ["teamRisk", numericId] });
      queryClient.invalidateQueries({ queryKey: ["projectRisk", numericId] });
    },
  });

  const displayBreakdown = member.projects || breakdown || [];
  const pct = type === "team" ? member.global_risk : member.project_risk;
  const noData = pct === null || pct === undefined;

  const color = noData
    ? "#94a3b8"
    : pct >= 35
      ? "#ef4444"
      : pct >= 20
        ? "#f59e0b"
        : "#22c55e";

  return (
    <Card className="member-card">
      {/* Cabecera */}
      <Box className="member-card-header">
        <Box className="member-area">
          <Box className="member-name-row">
            <Typography
              variant="subtitle1"
              className="member-name-text"
              sx={{ cursor: "pointer", "&:hover": { color: "#4f46e5" } }}
              onClick={() => navigate(`/employee/${memberEmail}`)}
            >
              {member.display_name || member.alias}
            </Typography>

            {member.role !== "employee" && (
              <Chip
                label={member.role === "manager" ? "Manager" : "Admin"}
                size="small"
                className="member-chip-role"
              />
            )}
          </Box>

          <Typography variant="body2" className="member-risk-label">
            {type === "team" ? "Riesgo global" : "Riesgo táctico"}
            {member.role !== "employee" ? " · Excluido de la media" : ""}
          </Typography>
        </Box>

        <Box className="member-risk-visuals">
          <Box className="member-progress-container">
            <LinearProgress
              variant="determinate"
              value={pct ?? 0}
              className="member-progress-bar"
              sx={{ "& .MuiLinearProgress-bar": { bgcolor: color } }}
            />
          </Box>

          <Typography
            variant="subtitle1"
            className="member-risk-pct"
            sx={{ color }}
          >
            {noData ? "—" : `${pct}%`}
          </Typography>

          {(type === "team" || displayBreakdown.length > 0) && (
            <IconButton
              size="small"
              onClick={() => setExpanded(!expanded)}
              className="member-expand-btn"
            >
              <ExpandMoreIcon
                sx={{
                  transform: expanded ? "rotate(180deg)" : "rotate(0deg)",
                  transition: "0.2s ease",
                }}
              />
            </IconButton>
          )}
        </Box>
      </Box>

      {/* Detalle desplegable */}
      {expanded && (
        <Box className="member-detail-area">
          <Divider className="member-detail-divider" />

          <Typography
            variant="caption"
            className="member-detail-title"
          >
            Proyectos asociados
          </Typography>

          {isLoading ? (
            <LinearProgress sx={{ borderRadius: 999, mb: 2 }} className="member-detail-loader" />
          ) : displayBreakdown.length === 0 ? (
            <Paper
              variant="outlined"
              className="member-no-data-paper"
            >
              <Typography variant="body2" sx={{ color: "#64748b" }}>
                Sin proyectos activos en este periodo.
              </Typography>
            </Paper>
          ) : (
            <Box className="member-table">
              {/* Cabecera mini tabla */}
              <Box className="member-table-header">
                <Typography variant="caption" className="member-table-header-cell">
                  Proyecto
                </Typography>
                <Typography variant="caption" className="member-table-header-cell" align="right">
                  Riesgo
                </Typography>
                <Typography variant="caption" className="member-table-header-cell" align="center">
                  Acción
                </Typography>
              </Box>

              {/* Filas */}
              {displayBreakdown.map((p, idx) => {
                const projectRisk = p.project_risk;
                const projectColor =
                  projectRisk === null || projectRisk === undefined
                    ? "#94a3b8"
                    : projectRisk >= 35
                      ? "#ef4444"
                      : projectRisk >= 20
                        ? "#f59e0b"
                        : "#22c55e";

                return (
                  <Box
                    key={p.project_id}
                    className="member-table-row"
                  >
                    <Typography variant="body2" className="member-project-name">
                      {p.project_name}
                    </Typography>

                    <Typography
                      variant="body2"
                      className="member-project-risk"
                      sx={{ color: projectColor }}
                    >
                      {projectRisk === null || projectRisk === undefined ? "—" : `${projectRisk}%`}
                    </Typography>

                    <Box className="member-project-action">
                      {canManage && (
                        <IconButton
                          size="small"
                          onClick={() => removeMutation.mutate(p.project_id)}
                          sx={{ color: "#ef4444" }}
                        >
                          <DeleteIcon sx={{ fontSize: 16 }} />
                        </IconButton>
                      )}
                    </Box>
                  </Box>
                );
              })}
            </Box>
          )}

          {/* Añadir proyecto */}
          {canManage && catalog && (
            <Box className="member-add-area">
              <FormControl size="small" sx={{ minWidth: 240 }}>
                <Select
                  value={selectedProject}
                  onChange={(e) => setSelectedProject(e.target.value)}
                  displayEmpty
                  className="member-add-select"
                >
                  <MenuItem value="" disabled>
                    Seleccionar proyecto…
                  </MenuItem>
                  {catalog
                    .filter((p) => !displayBreakdown.some((dp) => dp.project_id === p.id))
                    .map((p) => (
                      <MenuItem key={p.id} value={p.id}>
                        {p.name}
                      </MenuItem>
                    ))}
                </Select>
              </FormControl>

              <Button
                variant="contained"
                startIcon={<AddIcon />}
                disabled={!selectedProject || addMutation.isPending}
                onClick={() => addMutation.mutate(selectedProject)}
                className="member-add-btn"
              >
                Añadir
              </Button>
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
  const {
    days, rangeMode, customRange, setCustomRange,
    queryStart, queryEnd, handleFilterChange
  } = useRiskFilters(7);

  const riskQuery = useQuery({
    queryKey: [type === "team" ? "teamRisk" : "projectRisk", itemId, days, rangeMode, queryStart, queryEnd],
    queryFn: () => type === "team" ? fetchTeamRisk(itemId, days, queryStart, queryEnd) : fetchProjectRisk(itemId, days, queryStart, queryEnd),
    staleTime: 30_000,
  });

  const trendQuery = useQuery({
    queryKey: [type === "team" ? "teamTrend" : "projectTrend", itemId, days, rangeMode, queryStart, queryEnd],
    queryFn: () => type === "team" ? fetchTeamTrend(itemId, days, queryStart, queryEnd) : fetchProjectTrend(itemId, days, queryStart, queryEnd),
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
          {riskData?.members?.filter(m => m.role === 'employee').length ?? 0} integrantes analizados
        </Typography>
      </Box>

      {/* Controles de Acción (Periodo + Refrescar) */}
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 3, flexWrap: "wrap", gap: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Periodo: {rangeMode === "preset" ? DAY_LABEL[days] : DAY_LABEL[rangeMode]}
        </Typography>
        <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
          {rangeMode === "custom" && (
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                label="Inicio"
                type="date"
                size="small"
                InputLabelProps={{ shrink: true }}
                value={customRange.start}
                onChange={e => setCustomRange(prev => ({ ...prev, start: e.target.value }))}
                sx={{ width: 140 }}
              />
              <TextField
                label="Fin"
                type="date"
                size="small"
                InputLabelProps={{ shrink: true }}
                value={customRange.end}
                onChange={e => setCustomRange(prev => ({ ...prev, end: e.target.value }))}
                sx={{ width: 140 }}
              />
            </Box>
          )}
          <ToggleButtonGroup
            value={rangeMode === 'preset' ? days : rangeMode}
            exclusive
            onChange={(_, v) => handleFilterChange(v)}
            size="small"
          >
            {DAY_OPTIONS.map((d) => (
              <ToggleButton key={d} value={d} sx={{ px: 2, fontSize: 13, textTransform: "none" }}>{DAY_LABEL[d]}</ToggleButton>
            ))}
            <ToggleButton value="fiscal" sx={{ px: 2, fontSize: 13, textTransform: "none" }}>FY Actual</ToggleButton>
            <ToggleButton value="fiscal-prev" sx={{ px: 2, fontSize: 13, textTransform: "none" }}>FY Anterior</ToggleButton>
            <ToggleButton value="custom" sx={{ px: 2, fontSize: 13, textTransform: "none" }}>Personalizado</ToggleButton>
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
            {type === 'team'
              ? 'Riesgo global del equipo: promedio del riesgo global de sus integrantes.'
              : 'Riesgo táctico del proyecto: promedio del riesgo contextual de sus integrantes dentro de este proyecto.'}
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
                <Box sx={{ mt: 2 }}>
                  <RiskTrendChart data={trendData} days={days} startDate={queryStart} endDate={queryEnd} />
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
        <Box className="member-list-section">
          <Typography variant="h6" className="member-list-title">
            Desglose por Miembro
          </Typography>
          <Typography
            variant="body2"
            className="member-list-subtitle"
          >
            Riesgo total del empleado a través de todos sus proyectos activos.
          </Typography>

          {riskQuery.isLoading ? (
            <Skeleton variant="rounded" height={200} sx={{ borderRadius: 2 }} />
          ) : (
            <Box className="member-list-container">
              {/* Sección de Managers (si es equipo) */}
              {type === "team" && (riskData?.members ?? []).filter(m => m.role !== 'employee').map(m => (
                <Box key={m.email} sx={{ mb: 1 }}>
                  <Typography variant="caption" color="text.disabled" sx={{ ml: 1, mb: 0.5, display: "block", fontWeight: 700 }}>RESPONSABLE / GESTIÓN</Typography>
                  <MemberRiskRow member={m} type={type} days={days} rangeMode={rangeMode} customRange={customRange} />
                </Box>
              ))}

              {/* Sección de Empleados */}
              {(riskData?.members ?? []).filter(m => m.role === 'employee').map((m) => (
                <MemberRiskRow key={m.email} member={m} type={type} days={days} rangeMode={rangeMode} customRange={customRange} />
              ))}
            </Box>
          )}
        </Box>

        {/* BLOQUE: Metodología plegable */}
        <Accordion className="methodology-accordion">
          <AccordionSummary
            expandIcon={<ExpandMoreIcon sx={{ color: "text.secondary" }} />}
            className="methodology-summary"
          >
            <Typography variant="body2" color="text.secondary" className="methodology-summary-text">
              <InfoOutlinedIcon fontSize="small" /> ¿Cómo se calcula el riesgo?
            </Typography>
          </AccordionSummary>
          <AccordionDetails className="methodology-details">
            <Typography variant="body2" color="text.secondary" className="methodology-details-text">
              {type === 'team'
                ? "El riesgo global del equipo se calcula como la media de los niveles de estrés detectados en las comunicaciones de sus miembros operativos (employees). Los perfiles de gestión (managers/admins) se muestran para visibilidad pero no afectan al promedio del equipo para evitar sesgos."
                : "El riesgo táctico del proyecto evalúa específicamente cómo los mensajes intercambiados dentro de este proyecto afectan al bienestar de los participantes, permitiendo identificar fricciones en entregas o flujos de trabajo específicos."}
              <br /><br />
              Nuestro modelo procesa los mensajes codificados usando transformadores lingüísticos (base RoBERTa), clasificando el texto en dimensiones emocionales. Todo el proceso es "Privacy by Design" y anonimizado en origen.
            </Typography>
          </AccordionDetails>
        </Accordion>

      </Box>
    </Box>
  );
}

