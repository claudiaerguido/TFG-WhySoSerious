import React, { useMemo } from "react";
import {
    ResponsiveContainer,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip as RechartsTooltip,
} from "recharts";
import { Typography, Paper, Box, Alert } from "@mui/material";

const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !label) return null;

    const point = payload?.[0]?.payload;
    const value = point?.risk_score_percentage ?? 0;
    const hasRealData = point?.hasRealData;

    return (
        <Paper
            elevation={0}
            sx={{
                p: 1.5,
                bgcolor: "rgba(15, 23, 42, 0.96)",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: 2,
                boxShadow: "0 10px 30px rgba(2, 6, 23, 0.28)",
            }}
        >
            <Typography
                variant="caption"
                sx={{ color: "#94a3b8", display: "block", mb: 0.5 }}
            >
                {label}
            </Typography>

            {hasRealData ? (
                <Typography variant="body2" fontWeight={700} sx={{ color: "#818cf8" }}>
                    Riesgo: {value}%
                </Typography>
            ) : (
                <>
                    <Typography variant="body2" fontWeight={700} sx={{ color: "#818cf8" }}>
                        Riesgo visual: {value}%
                    </Typography>
                    <Typography
                        variant="caption"
                        sx={{ color: "#cbd5e1", fontStyle: "italic" }}
                    >
                        No hay datos reales para este día
                    </Typography>
                </>
            )}
        </Paper>
    );
};

function buildContinuousSeries(data, startDate, endDate, days) {
    const safeData = Array.isArray(data) ? data : [];
    const map = new Map(
        safeData.map((item) => [item.date, item.risk_score_percentage])
    );

    let startObj, endObj;
    if (startDate && endDate) {
        // Enforce parsing as local dates matching YYYY-MM-DD
        const [sy, sm, sd] = startDate.split('-');
        const [ey, em, ed] = endDate.split('-');
        startObj = new Date(sy, sm - 1, sd);
        endObj = new Date(ey, em - 1, ed);
    } else {
        const today = new Date();
        endObj = new Date(today.getFullYear(), today.getMonth(), today.getDate());
        startObj = new Date(endObj);
        startObj.setDate(startObj.getDate() - days + 1);
    }

    const diffTime = endObj - startObj;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;

    const result = [];
    const hasAnyRealData = safeData.length > 0;
    let lastKnownValue = null;

    for (let i = 0; i < diffDays; i++) {
        const d = new Date(startObj);
        d.setDate(d.getDate() + i);

        const yyyy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, "0");
        const dd = String(d.getDate()).padStart(2, "0");
        const dateStr = `${yyyy}-${mm}-${dd}`;

        if (map.has(dateStr)) {
            const realValue = map.get(dateStr);
            lastKnownValue = realValue;

            result.push({
                date: dateStr,
                risk_score_percentage: realValue,
                hasRealData: true,
            });
        } else {
            result.push({
                date: dateStr,
                risk_score_percentage: hasAnyRealData
                    ? (lastKnownValue ?? safeData[0]?.risk_score_percentage ?? 0)
                    : 0,
                hasRealData: false,
            });
        }
    }

    return result;
}

function formatDateLabel(dateStr) {
    if (!dateStr) return "";
    const [, month, day] = dateStr.split("-");
    return `${day}/${month}`;
}

function renderDot(props) {
    const { cx, cy, payload } = props;
    if (!payload || !payload.hasRealData) return null;

    return (
        <circle
            cx={cx}
            cy={cy}
            r={4}
            fill="#f43f5e"
            stroke="#ffffff"
            strokeWidth={2}
            opacity={1}
        />
    );
}

const RiskTrendChart = ({ data = [], days = 7, startDate = null, endDate = null, height = 260 }) => {
    const processedData = useMemo(
        () => buildContinuousSeries(data, startDate, endDate, days),
        [data, startDate, endDate, days]
    );

    const hasAnyRealData = processedData.some((d) => d.hasRealData);
    const hasMissingData = processedData.some((d) => !d.hasRealData);

    return (
        <Box sx={{ width: "100%" }}>
            {!hasAnyRealData ? (
                <Alert
                    severity="info"
                    sx={{
                        mb: 2,
                        borderRadius: 2,
                        bgcolor: "#f8fafc",
                        color: "#475569",
                        "& .MuiAlert-icon": { color: "#64748b" },
                    }}
                >
                    No hay datos en este rango. Se muestra una línea base solo como referencia visual.
                </Alert>
            ) : hasMissingData ? (
                <Alert
                    severity="info"
                    sx={{
                        mb: 2,
                        borderRadius: 2,
                        bgcolor: "#f8fafc",
                        color: "#475569",
                        "& .MuiAlert-icon": { color: "#64748b" },
                    }}
                >
                    Algunos días no tienen datos; la gráfica mantiene continuidad visual con el último valor disponible.
                </Alert>
            ) : null}

            <Box sx={{ width: "100%", height }}>
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                        data={processedData}
                        margin={{ top: 10, right: 12, left: -20, bottom: 0 }}
                    >
                        <CartesianGrid
                            strokeDasharray="3 3"
                            stroke="rgba(15, 23, 42, 0.06)"
                            vertical={false}
                        />

                        <XAxis
                            dataKey="date"
                            stroke="#64748b"
                            fontSize={11}
                            tickMargin={10}
                            minTickGap={24}
                            axisLine={false}
                            tickLine={false}
                            tickFormatter={formatDateLabel}
                        />

                        <YAxis
                            stroke="#64748b"
                            fontSize={11}
                            tickFormatter={(v) => `${v}%`}
                            domain={[0, 100]}
                            ticks={[0, 25, 50, 75, 100]}
                            axisLine={false}
                            tickLine={false}
                        />

                        <RechartsTooltip
                            content={<CustomTooltip />}
                            cursor={{ stroke: "rgba(129, 140, 248, 0.18)", strokeWidth: 1 }}
                        />

                        <Line
                            type="linear"
                            dataKey="risk_score_percentage"
                            stroke={hasAnyRealData ? "#818cf8" : "rgba(148, 163, 184, 0.6)"}
                            strokeWidth={2.5}
                            dot={renderDot}
                            activeDot={{
                                r: 5,
                                fill: "#818cf8",
                                stroke: "#ffffff",
                                strokeWidth: 2,
                            }}
                            isAnimationActive={false}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </Box>
        </Box>
    );
};

export default RiskTrendChart;