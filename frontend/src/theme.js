import { createTheme } from "@mui/material/styles";

const theme = createTheme({
    palette: {
        mode: "light",
        primary: {
            main: "#6366f1", // Indigo premium
            light: "#818cf8",
            dark: "#4f46e5",
            contrastText: "#ffffff",
        },
        secondary: {
            main: "#10b981", // Emerald
        },
        background: {
            default: "#f8fafc", // Slate 50
            paper: "#ffffff",
        },
        text: {
            primary: "#0f172a", // Slate 900
            secondary: "#64748b", // Slate 500
        },
        divider: "rgba(0,0,0,0.06)",
    },
    typography: {
        fontFamily: "'Inter', 'Roboto', sans-serif",
        h4: { fontWeight: 800, letterSpacing: "-0.5px" },
        h5: { fontWeight: 800, letterSpacing: "-0.3px" },
        h6: { fontWeight: 700 },
        subtitle1: { fontWeight: 600 },
        button: { fontWeight: 700, textTransform: "none" },
    },
    shape: {
        borderRadius: 12,
    },
    components: {
        MuiButton: {
            styleOverrides: {
                root: {
                    borderRadius: 10,
                    padding: '8px 20px',
                },
                containedPrimary: {
                    boxShadow: '0 4px 14px 0 rgba(99, 102, 241, 0.39)',
                }
            },
        },
        MuiCard: {
            styleOverrides: {
                root: {
                    boxShadow: '0 4px 20px rgba(0,0,0,0.03)',
                    border: '1px solid rgba(0,0,0,0.05)',
                },
            },
        },
        MuiPaper: {
            styleOverrides: {
                root: {
                    backgroundImage: 'none',
                }
            }
        }
    },
});

export default theme;
