import { Box, Chip, Typography } from "@mui/material";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";

const LEVEL_CONFIG = {
    Verde: {
        color: "#10b981",
        bg: "rgba(16,185,129,0.06)",
        label: "Riesgo Bajo",
        description: "Zona de bienestar (0-20%): No se detectan señales relevantes de burnout o tensión. La dinámica de comunicación es estable.",
    },
    Amarillo: {
        color: "#f59e0b",
        bg: "rgba(245,158,11,0.06)",
        label: "Riesgo Moderado",
        description: "Zona de seguimiento (20-35%): Se detectan patrones puntuales de sobrecarga o fatiga. Se recomienda monitorizar la evolución.",
    },
    Rojo: {
        color: "#ef4444",
        bg: "rgba(239,68,68,0.06)",
        label: "Riesgo Elevado",
        description: "Zona de revisión (>35%): Indicadores persistentes de alto riesgo. Se requiere intervención prioritaria y análisis de causas.",
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
            borderRadius: 3,
            p: 3,
            background: "rgba(255,255,255,0.02)",
            border: "1px solid rgba(255,255,255,0.05)",
            display: "flex",
            flexDirection: "column",
            gap: 2,
        }}>
            {/* Score + badge */}
            <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                <Typography
                    sx={{
                        fontSize: 48,
                        fontWeight: 300,
                        color: "text.primary",
                        lineHeight: 1,
                        letterSpacing: "-2px",
                    }}
                >
                    {riskScore !== null && riskScore !== undefined ? `${riskScore}%` : "—"}
                </Typography>
                <Chip
                    label={cfg.label}
                    size="small"
                    sx={{
                        bgcolor: `${cfg.color}15`,
                        color: cfg.color,
                        fontWeight: 600,
                        fontSize: 12,
                        height: 24,
                        border: "none"
                    }}
                />
            </Box>

            {/* Comparativa temporal */}
            {delta !== null && (
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                    {isDown
                        ? <TrendingDownIcon sx={{ fontSize: 16, color: "#10b981" }} />
                        : isUp
                            ? <TrendingUpIcon sx={{ fontSize: 16, color: "#ef4444" }} />
                            : null
                    }
                    <Typography variant="body2" sx={{
                        color: isDown ? "#10b981" : isUp ? "#ef4444" : "text.secondary",
                        fontWeight: 500,
                    }}>
                        {delta > 0 ? "+" : ""}{delta}% respecto a la semana anterior
                    </Typography>
                </Box>
            )}

            {/* Descripción */}
            <Typography variant="body1" color="text.secondary" sx={{ mt: 1, fontWeight: 400 }}>
                {cfg.description}
            </Typography>

            {/* Nota de muestra */}
            {sampleSize !== undefined && (
                <Typography variant="caption" color="text.disabled" sx={{ display: "block", mt: 1 }}>
                    Basado en {sampleSize} miembro{sampleSize !== 1 ? "s" : ""} · Sin datos individuales
                </Typography>
            )}
        </Box>
    );
}
