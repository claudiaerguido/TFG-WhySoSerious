import { useState, useMemo } from "react";
import {
    Box, Typography, Table, TableBody, TableCell, TableContainer,
    TableHead, TableRow, Chip, Button, Dialog, DialogTitle,
    DialogContent, DialogActions, Select, MenuItem, FormControl,
    InputLabel, Stack, Divider,
} from "@mui/material";
import { RISK_COLOR, fmtPct } from "../utils/risk";

// Datos de ejemplo — endpoint histórico planificado para Sprint 5
const SAMPLE_REPORTS = [
    { id: 1, date: "2026-02-23", team: "Equipo Desarrollo", teamId: 1, risk: 27.1, level: "Verde", sample: 2 },
    { id: 2, date: "2026-02-22", team: "Equipo Desarrollo", teamId: 1, risk: 31.5, level: "Amarillo", sample: 2 },
    { id: 3, date: "2026-02-21", team: "Equipo Desarrollo", teamId: 1, risk: 19.2, level: "Verde", sample: 2 },
    { id: 4, date: "2026-02-20", team: "Equipo QA", teamId: 2, risk: 44.0, level: "Amarillo", sample: 1 },
    { id: 5, date: "2026-02-19", team: "Equipo QA", teamId: 2, risk: 71.3, level: "Rojo", sample: 1 },
    { id: 6, date: "2026-02-18", team: "Proyecto Alpha", teamId: 3, risk: 12.5, level: "Verde", sample: 3 },
    { id: 7, date: "2026-02-17", team: "Proyecto Alpha", teamId: 3, risk: 58.9, level: "Amarillo", sample: 3 },
];

const TEAMS = [...new Set(SAMPLE_REPORTS.map((r) => r.team))];
const LEVELS = ["Todos", "Verde", "Amarillo", "Rojo"];

const LEVEL_DOT = {
    Verde: "#10b981",
    Amarillo: "#f59e0b",
    Rojo: "#ef4444",
};

export default function ReportsPage() {
    const [selected, setSelected] = useState(null);
    const [filterTeam, setFilterTeam] = useState("Todos");
    const [filterLevel, setFilterLevel] = useState("Todos");

    const filtered = useMemo(() => SAMPLE_REPORTS.filter((r) => {
        const teamOk = filterTeam === "Todos" || r.team === filterTeam;
        const levelOk = filterLevel === "Todos" || r.level === filterLevel;
        return teamOk && levelOk;
    }), [filterTeam, filterLevel]);

    const today = new Date().toLocaleDateString("es-ES", { day: "numeric", month: "long", year: "numeric" });

    return (
        <Box sx={{ maxWidth: 1100, mx: "auto" }}>
            {/* ── Header ─────────────────────────────────── */}
            <Box mb={4}>
                <Typography variant="h5" fontWeight={700}>Reportes Históricos</Typography>
                <Typography variant="body2" color="text.secondary" mt={0.5}>
                    Historial de análisis de riesgo por equipo · Sin información personal
                </Typography>
            </Box>

            {/* ── Filtros + meta ─────────────────────────── */}
            <Box mb={3} display="flex" alignItems="center" justifyContent="space-between" flexWrap="wrap" gap={2}>
                <Stack direction="row" spacing={1.5} flexWrap="wrap">
                    <FormControl size="small" sx={{ minWidth: 180 }}>
                        <InputLabel>Equipo / Proyecto</InputLabel>
                        <Select
                            value={filterTeam}
                            label="Equipo / Proyecto"
                            onChange={(e) => setFilterTeam(e.target.value)}
                        >
                            <MenuItem value="Todos">Todos</MenuItem>
                            {TEAMS.map((t) => <MenuItem key={t} value={t}>{t}</MenuItem>)}
                        </Select>
                    </FormControl>

                    <FormControl size="small" sx={{ minWidth: 140 }}>
                        <InputLabel>Nivel</InputLabel>
                        <Select
                            value={filterLevel}
                            label="Nivel"
                            onChange={(e) => setFilterLevel(e.target.value)}
                        >
                            {LEVELS.map((l) => <MenuItem key={l} value={l}>{l}</MenuItem>)}
                        </Select>
                    </FormControl>

                    {(filterTeam !== "Todos" || filterLevel !== "Todos") && (
                        <Button
                            size="small"
                            variant="text"
                            onClick={() => { setFilterTeam("Todos"); setFilterLevel("Todos"); }}
                            sx={{ color: "text.secondary" }}
                        >
                            Limpiar
                        </Button>
                    )}
                </Stack>

                {/* Meta info — microdetalle profesional */}
                <Typography variant="caption" color="text.disabled" sx={{ whiteSpace: "nowrap" }}>
                    Mostrando {filtered.length} registro{filtered.length !== 1 ? "s" : ""} · Actualizado {today}
                </Typography>
            </Box>

            {/* ── Tabla minimalista ──────────────────────── */}
            <TableContainer sx={{ borderRadius: 2, border: "1px solid rgba(255,255,255,0.07)", overflow: "hidden" }}>
                <Table>
                    <TableHead>
                        <TableRow sx={{ bgcolor: "rgba(255,255,255,0.025)" }}>
                            <TableCell sx={{ color: "text.disabled", fontSize: 11, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", borderBottom: "1px solid rgba(255,255,255,0.06)", py: 1.5 }}>Fecha</TableCell>
                            <TableCell sx={{ color: "text.disabled", fontSize: 11, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", borderBottom: "1px solid rgba(255,255,255,0.06)", py: 1.5 }}>Equipo / Proyecto</TableCell>
                            <TableCell sx={{ color: "text.disabled", fontSize: 11, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", borderBottom: "1px solid rgba(255,255,255,0.06)", py: 1.5 }}>Riesgo</TableCell>
                            <TableCell sx={{ color: "text.disabled", fontSize: 11, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", borderBottom: "1px solid rgba(255,255,255,0.06)", py: 1.5 }}>Nivel</TableCell>
                            <TableCell sx={{ color: "text.disabled", fontSize: 11, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", borderBottom: "1px solid rgba(255,255,255,0.06)", py: 1.5 }}>Muestra</TableCell>
                            <TableCell sx={{ borderBottom: "1px solid rgba(255,255,255,0.06)", py: 1.5 }} />
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {filtered.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={6} align="center" sx={{ color: "text.secondary", py: 5, border: 0 }}>
                                    No hay reportes que coincidan con los filtros seleccionados.
                                </TableCell>
                            </TableRow>
                        ) : filtered.map((r, idx) => {
                            const rc = RISK_COLOR(r.level);
                            const dotColor = LEVEL_DOT[r.level] ?? "#64748b";
                            return (
                                <TableRow
                                    key={r.id}
                                    sx={{
                                        bgcolor: "transparent",
                                        "&:hover": { bgcolor: "rgba(255,255,255,0.025)" },
                                        "& td": { borderBottom: idx === filtered.length - 1 ? "none" : "1px solid rgba(255,255,255,0.05)" },
                                    }}
                                >
                                    {/* Fecha */}
                                    <TableCell sx={{ py: 2, color: "text.disabled", fontSize: 12 }}>
                                        {r.date}
                                    </TableCell>

                                    {/* Nombre con punto de color */}
                                    <TableCell sx={{ py: 2 }}>
                                        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                                            <Box sx={{ width: 7, height: 7, borderRadius: "50%", bgcolor: dotColor, flexShrink: 0 }} />
                                            <Typography variant="body2" fontWeight={600} color="text.primary">
                                                {r.team}
                                            </Typography>
                                        </Box>
                                    </TableCell>

                                    {/* Riesgo */}
                                    <TableCell sx={{ py: 2 }}>
                                        <Typography variant="body2" fontWeight={700} sx={{ color: dotColor }}>
                                            {fmtPct(r.risk)}
                                        </Typography>
                                    </TableCell>

                                    {/* Nivel badge plano */}
                                    <TableCell sx={{ py: 2 }}>
                                        <Chip
                                            label={r.level}
                                            size="small"
                                            sx={{
                                                height: 20,
                                                fontSize: 11,
                                                fontWeight: 700,
                                                bgcolor: `${dotColor}18`,
                                                color: dotColor,
                                                border: `1px solid ${dotColor}35`,
                                            }}
                                        />
                                    </TableCell>

                                    {/* Muestra */}
                                    <TableCell sx={{ py: 2, color: "text.disabled", fontSize: 12 }}>
                                        {r.sample} usu.
                                    </TableCell>

                                    {/* Acción */}
                                    <TableCell sx={{ py: 2 }} align="right">
                                        <Button
                                            size="small"
                                            variant="text"
                                            onClick={() => setSelected(r)}
                                            sx={{ color: "text.secondary", fontSize: 12, minWidth: "auto", px: 1 }}
                                        >
                                            Ver →
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            );
                        })}
                    </TableBody>
                </Table>
            </TableContainer>

            {/* ── Modal detalle ──────────────────────────── */}
            <Dialog
                open={!!selected}
                onClose={() => setSelected(null)}
                PaperProps={{ sx: { bgcolor: "background.paper", borderRadius: 2, minWidth: 340, border: "1px solid rgba(255,255,255,0.08)" } }}
            >
                <DialogTitle fontWeight={700} sx={{ pb: 1 }}>
                    Reporte · {selected?.date}
                </DialogTitle>
                <DialogContent>
                    {selected && (() => {
                        const rc = RISK_COLOR(selected.level);
                        const dotColor = LEVEL_DOT[selected.level] ?? "#64748b";
                        return (
                            <Box>
                                {/* Indicador principal */}
                                <Box sx={{
                                    display: "flex", alignItems: "center", gap: 2.5,
                                    p: 2, mb: 2.5, borderRadius: 1.5,
                                    bgcolor: `${dotColor}0e`,
                                    border: `1px solid ${dotColor}30`,
                                }}>
                                    <Box sx={{ width: 3, minHeight: 44, borderRadius: 4, bgcolor: dotColor, flexShrink: 0 }} />
                                    <Box>
                                        <Typography variant="caption" color="text.secondary">Índice de riesgo</Typography>
                                        <Typography variant="h4" fontWeight={700} color={dotColor} lineHeight={1} sx={{ letterSpacing: "-1px" }}>
                                            {fmtPct(selected.risk)}
                                        </Typography>
                                    </Box>
                                    <Chip
                                        label={selected.level}
                                        size="small"
                                        sx={{
                                            ml: "auto",
                                            height: 22, fontSize: 11, fontWeight: 700,
                                            bgcolor: `${dotColor}20`, color: dotColor,
                                            border: `1px solid ${dotColor}40`,
                                        }}
                                    />
                                </Box>

                                <Divider sx={{ mb: 2, borderColor: "rgba(255,255,255,0.06)" }} />

                                <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
                                    <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                                        <Typography variant="body2" color="text.secondary">Equipo</Typography>
                                        <Typography variant="body2" fontWeight={600}>{selected.team}</Typography>
                                    </Box>
                                    <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                                        <Typography variant="body2" color="text.secondary">Usuarios analizados</Typography>
                                        <Typography variant="body2" fontWeight={600}>{selected.sample}</Typography>
                                    </Box>
                                </Box>

                                <Typography variant="caption" color="text.disabled" sx={{ display: "block", mt: 2.5, lineHeight: 1.6 }}>
                                    🔒 Este reporte no contiene mensajes ni datos personales. Las métricas son agregados anónimos calculados por el modelo NLP.
                                </Typography>
                            </Box>
                        );
                    })()}
                </DialogContent>
                <DialogActions sx={{ px: 3, pb: 2 }}>
                    <Button onClick={() => setSelected(null)} size="small" sx={{ color: "text.secondary" }}>Cerrar</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}
