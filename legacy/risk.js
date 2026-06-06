// ─── Colores de riesgo con fallback seguro ───────────────────────────────────
const _RISK = {
    Verde: { mui: "success", text: "success.main" },
    Amarillo: { mui: "warning", text: "warning.main" },
    Rojo: { mui: "error", text: "error.main" },
};
/** Devuelve colores MUI para un nivel dado. Si es null/desconocido → Verde (seguro). */
export const RISK_COLOR = (level) => _RISK[level] ?? _RISK.Verde;

// ─── Formato de porcentaje consistente ──────────────────────────────────────
/**
 * Formatea un valor numérico como porcentaje con 2 decimales.
 * Protección: si v <= 1 asume escala 0-1 y multiplica por 100.
 * (El backend envía valores ya en 0-100, pero dejamos la guardia por si acaso.)
 */
export const fmtPct = (v) => {
    if (v == null) return "—";
    const val = v <= 1 ? v * 100 : v;
    return `${Number(val).toFixed(2)}%`;
};
