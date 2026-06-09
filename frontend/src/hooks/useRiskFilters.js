import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchAdminSettings } from "../api/api";

/**
 * Hook para gestionar los filtros de análisis de riesgo (días, rango personalizado y año fiscal).
 */
export function useRiskFilters(initialDays = 7) {
    const [days, setDays] = useState(initialDays);
    const [rangeMode, setRangeMode] = useState("preset"); // preset | custom | fiscal | fiscal-prev
    const [customRange, setCustomRange] = useState({ start: '', end: '' });

    // Fetch org settings for fiscal year dates
    const { data: fySettings } = useQuery({
        queryKey: ["adminSettings"],
        queryFn: fetchAdminSettings,
        staleTime: 300_000,
    });

    const handleFilterChange = (newValue) => {
        if (newValue === 'custom') {
            setRangeMode('custom');
        } else if (newValue === 'fiscal') {
            setRangeMode('fiscal');
        } else if (newValue === 'fiscal-prev') {
            setRangeMode('fiscal-prev');
        } else if (newValue) {
            setRangeMode('preset');
            setDays(newValue);
        }
    };

    const customDatesReady = Boolean(customRange.start && customRange.end);

    // Fechas derivadas según el modo de filtro seleccionado
    const queryStart =
        rangeMode === "custom" ? customRange.start :
            rangeMode === "fiscal" ? fySettings?.fy_start_date :
                rangeMode === "fiscal-prev" ? fySettings?.prev_fy_start_date :
                    null;

    const queryEnd =
        rangeMode === "custom" ? customRange.end :
            rangeMode === "fiscal" ? fySettings?.fy_end_date :
                rangeMode === "fiscal-prev" ? fySettings?.prev_fy_end_date :
                    null;

    return {
        days,
        rangeMode,
        customRange,
        setCustomRange,
        queryStart,
        queryEnd,
        customDatesReady,
        handleFilterChange,
        fySettings
    };
}
