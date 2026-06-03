import React, { useMemo } from "react";
import {
    ResponsiveContainer,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip as RechartsTooltip,
    ReferenceLine,
    ReferenceArea,
    Brush
} from "recharts";
import { Typography, Paper, Box } from "@mui/material";

const getStatus = (value) => {
    if (value >= 35) return { label: "Riesgo Alto", color: "#ef4444", bg: "rgba(239, 68, 68, 0.05)" };
    if (value >= 20) return { label: "Riesgo Moderado", color: "#f59e0b", bg: "rgba(245, 158, 11, 0.05)" };
    return { label: "Riesgo Bajo", color: "#22c55e", bg: "rgba(34, 197, 94, 0.05)" };
};

const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !label) return null;

    const point = payload?.[0]?.payload;
    const value = point?.risk_score_percentage ?? 0;
    const hasRealData = point?.hasRealData;
    const { label: statusLabel, color: statusColor } = getStatus(value);

    return (
        <Paper
            elevation={0}
            sx={{
                p: 1.5,
                bgcolor: "rgba(15, 23, 42, 0.96)",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: 2,
                boxShadow: "0 10px 30px rgba(2, 6, 23, 0.28)",
            }}
        >
            <Typography variant="caption" sx={{ color: "#94a3b8", display: "block", mb: 0.5 }}>
                {label}
            </Typography>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <Typography variant="body2" fontWeight={700} sx={{ color: "#fff" }}>
                    {value}%
                </Typography>
                <Typography variant="caption" fontWeight={700} sx={{
                    px: 1, py: 0.2, borderRadius: 1,
                    bgcolor: `${statusColor}20`, color: statusColor,
                    fontSize: 10, textTransform: 'uppercase'
                }}>
                    {statusLabel}
                </Typography>
            </Box>

            {!hasRealData && (
                <Typography variant="caption" sx={{ color: "#cbd5e1", fontStyle: "italic", display: 'block' }}>
                    Dato interpolado (sin mensajes)
                </Typography>
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
        const [sy, sm, sd] = startDate.split('-');
        const [ey, em, ed] = endDate.split('-');
        startObj = new Date(sy, sm - 1, sd);
        endObj = new Date(ey, em - 1, ed);
    } else {
        const todayStr = getTodayStr();
        const [ty, tm, td] = todayStr.split('-');
        endObj = new Date(ty, tm - 1, td);
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

function getTodayStr() {
    const today = new Date();
    return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
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
            fill="#6366f1"
            stroke="#ffffff"
            strokeWidth={2}
            opacity={1}
        />
    );
}

const RiskTrendChart = ({ data = [], days = 7, startDate = null, endDate = null, height = 280 }) => {
    const todayStr = getTodayStr();

    const processedData = useMemo(
        () => buildContinuousSeries(data, startDate, endDate, days),
        [data, startDate, endDate, days]
    );

    const hasAnyRealData = processedData.some((d) => d.hasRealData);

    return (
        <Box sx={{ width: "100%" }}>
            <Box sx={{ width: "100%", height }}>
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                        data={processedData}
                        margin={{ top: 20, right: 60, left: 10, bottom: 0 }}
                    >
                        <ReferenceArea y1={0} y2={20} fill="#22c55e" fillOpacity={0.07} isFront={false} />
                        <ReferenceArea y1={20} y2={35} fill="#f59e0b" fillOpacity={0.12} isFront={false} />
                        <ReferenceArea y1={35} y2={100} fill="#ef4444" fillOpacity={0.10} isFront={false} />

                        <CartesianGrid
                            strokeDasharray="3 3"
                            stroke="rgba(15, 23, 42, 0.04)"
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
                            ticks={[0, 20, 35, 50, 75, 100]}
                            axisLine={false}
                            tickLine={false}
                        />

                        <RechartsTooltip content={<CustomTooltip />} cursor={{ stroke: "rgba(129, 140, 248, 0.18)", strokeWidth: 1 }} />

                        <Line
                            type="monotone"
                            dataKey="risk_score_percentage"
                            stroke={hasAnyRealData ? "#6366f1" : "rgba(148, 163, 184, 0.4)"}
                            strokeWidth={3}
                            dot={renderDot}
                            activeDot={{ r: 6, fill: "#6366f1", stroke: "#fff", strokeWidth: 2 }}
                            isAnimationActive={false}
                        />

                        {processedData.some(d => d.date === todayStr) && (
                            <ReferenceLine
                                x={todayStr}
                                stroke="rgba(148, 163, 184, 0.4)"
                                strokeWidth={1}
                                strokeDasharray="4 4"
                                ifOverflow="visible"
                                label={{ value: 'Hoy', position: 'top', offset: 5, fill: '#94a3b8', fontSize: 10, fontWeight: 500 }}
                            />
                        )}

                        <ReferenceLine
                            y={20}
                            stroke="#f59e0b"
                            strokeDasharray="3 3"
                            strokeOpacity={0.6}
                            label={{ value: 'MODERADO (20%)', position: 'right', fill: '#d97706', fontSize: 9, fontWeight: 700, offset: 5 }}
                        />
                        <ReferenceLine
                            y={35}
                            stroke="#ef4444"
                            strokeDasharray="3 3"
                            strokeOpacity={0.6}
                            label={{ value: 'ALTO', position: 'right', fill: '#dc2626', fontSize: 9, fontWeight: 700, offset: 5 }}
                        />
                        <Brush
                            dataKey="date"
                            height={25}
                            stroke="#6366f1"
                            fill="rgba(99, 102, 241, 0.05)"
                            travellerWidth={10}
                            tickFormatter={formatDateLabel}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </Box>
        </Box>
    );
};

export default RiskTrendChart;