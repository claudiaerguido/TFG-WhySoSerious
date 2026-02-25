import { createTheme } from "@mui/material/styles";

const theme = createTheme({
    palette: {
        mode: "dark",
        primary: {
            main: "#6366f1",
            light: "#818cf8",
            dark: "#4f46e5",
        },
        secondary: {
            main: "#10b981",
        },
        background: {
            default: "#0f172a",
            paper: "#1e293b",
        },
        text: {
            primary: "#f1f5f9",
            secondary: "#94a3b8",
        },
        error: { main: "#ef4444" },
        warning: { main: "#f59e0b" },
        success: { main: "#10b981" },
    },
    typography: {
        fontFamily: "'Inter', 'Roboto', sans-serif",
        h4: { fontWeight: 700 },
        h5: { fontWeight: 700 },
        h6: { fontWeight: 600 },
    },
    shape: { borderRadius: 12 },
    components: {
        MuiCard: {
            styleOverrides: {
                root: {
                    backgroundImage: "none",
                    border: "1px solid rgba(255,255,255,0.07)",
                },
            },
        },
        MuiButton: {
            styleOverrides: {
                root: { textTransform: "none", fontWeight: 600 },
            },
        },
        MuiChip: {
            styleOverrides: {
                root: { fontWeight: 600 },
            },
        },
    },
});

export default theme;
