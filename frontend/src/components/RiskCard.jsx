import { Box, Chip, Typography } from "@mui/material";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";

const LEVEL_CONFIG = {
    Verde: {
        color: "#10b981",
        bg: "rgba(16,185,129,0.06)",
        label: "Riesgo Bajo",
        description: "El equipo mantiene una comunicación estable en las últimas semanas.",
    },
    Amarillo: {
        color: "#f59e0b",
        bg: "rgba(245,158,11,0.06)",
        label: "Riesgo Moderado",
        description: "Se detectan algunos indicadores de tensión o sobrecarga puntual.",
    },
    Rojo: {
        color: "#ef4444",
        bg: "rgba(239,68,68,0.06)",
        label: "Riesgo Elevado",
        description: "Se recomienda revisar la dinámica del equipo con atención.",
    },
};

/**
 * @param {object} props
 * @param {string} props.riskLevel  — "Verde" | "Amarillo" | "Rojo"
 * @param {number} props.riskScore  — Porcentaje 0-100
 * @param {number} props.sampleSize — Número de usuarios analizados
 * @param {number|null} props.prevScore — Score de la semana anterior (para comparativa)
 * @param {boolean} props.loading
 */
export default function RiskCard({ riskLevel, riskScore, sampleSize, prevScore = null, loading }) {
    if (loading) {
        return (
            <Box sx={{
                borderRadius: 2, p: 3,
                background: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.07)",
                color: "text.secondary", fontSize: 14,
            }}>
                Calculando riesgo…
            </Box>
        );
    }

    const cfg = LEVEL_CONFIG[riskLevel] || LEVEL_CONFIG.Verde;

    // Comparativa temporal
    const delta = prevScore !== null && riskScore !== undefined
        ? +(riskScore - prevScore).toFixed(1)
        : null;
    const isDown = delta !== null && delta < 0;
    const isUp = delta !== null && delta > 0;

    return (
        <Box sx={{
            borderRadius: 2,
            p: 3,
            background: cfg.bg,
            border: "1px solid rgba(255,255,255,0.07)",
            display: "flex",
            gap: 2.5,
            alignItems: "flex-start",
        }}>
            {/* Barra lateral de color semáforo */}
            <Box sx={{
                width: 4,
                minHeight: 80,
                borderRadius: 4,
                bgcolor: cfg.color,
                flexShrink: 0,
                mt: 0.5,
            }} />

            {/* Contenido */}
            <Box sx={{ flexGrow: 1 }}>
                {/* Score + badge */}
                <Box sx={{ display: "flex", alignItems: "baseline", gap: 2, flexWrap: "wrap" }}>
                    <Typography
                        sx={{
                            fontSize: 38,
                            fontWeight: 700,
                            color: cfg.color,
                            lineHeight: 1,
                            fontVariantNumeric: "tabular-nums",
                            letterSpacing: "-1px",
                        }}
                    >
                        {riskScore !== null && riskScore !== undefined ? `${riskScore}%` : "—"}
                    </Typography>
                    <Chip
                        label={cfg.label}
                        size="small"
                        sx={{
                            bgcolor: `${cfg.color}20`,
                            color: cfg.color,
                            fontWeight: 700,
                            fontSize: 11,
                            border: `1px solid ${cfg.color}40`,
                            height: 22,
                        }}
                    />
                </Box>

                {/* Comparativa temporal */}
                {delta !== null && (
                    <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, mt: 0.75 }}>
                        {isDown
                            ? <TrendingDownIcon sx={{ fontSize: 14, color: "#10b981" }} />
                            : isUp
                                ? <TrendingUpIcon sx={{ fontSize: 14, color: "#ef4444" }} />
                                : null
                        }
                        <Typography variant="caption" sx={{
                            color: isDown ? "#10b981" : isUp ? "#ef4444" : "text.secondary",
                            fontWeight: 600,
                        }}>
                            {delta > 0 ? "+" : ""}{delta}% respecto a la semana anterior
                        </Typography>
                    </Box>
                )}

                {/* Descripción */}
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1.5, lineHeight: 1.5 }}>
                    {cfg.description}
                </Typography>

                {/* Nota de muestra */}
                {sampleSize !== undefined && (
                    <Typography variant="caption" color="text.disabled" sx={{ display: "block", mt: 1.5 }}>
                        📊 {sampleSize} usuario{sampleSize !== 1 ? "s" : ""} analizados · Sin datos individuales expuestos
                    </Typography>
                )}
            </Box>
        </Box>
    );
}
