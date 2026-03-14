import { Box, Button, Typography, Paper } from "@mui/material";
import { loginUrl } from "../../api/backend";
import "./LoginPage.css";

export default function LoginPage() {
    return (
        <Box
            className="login-container"
            sx={{
                bgcolor: "background.default",
            }}
        >
            <Paper
                elevation={0}
                className="login-paper"
                sx={{
                    bgcolor: "background.paper",
                }}
            >
                {/* Logo Professional Redesign */}
                <Box sx={{ mb: 3, display: "flex", justifyContent: "center" }}>
                    <Box sx={{
                        position: 'relative',
                        width: 72, height: 72,
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        boxShadow: '0 12px 24px rgba(99, 102, 241, 0.3)',
                    }}>
                        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M3 13C3 13 4.5 13 5.5 11C6.5 9 7.5 4 8.5 4C9.5 4 11 18 12 18C13 18 14.5 14 15.5 14C16.5 14 18 16 19 16C20 16 21 15 21 15" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </Box>
                </Box>

                <Typography variant="h3" sx={{
                    fontWeight: 300,
                    color: "text.primary",
                    letterSpacing: -2,
                    mb: 1,
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'baseline'
                }}>
                    WhySo
                    <Box component="span" sx={{
                        fontWeight: 900,
                        background: 'linear-gradient(90deg, #4f46e5, #818cf8)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                    }}>
                        Serious
                    </Box>
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 4, fontWeight: 500 }}>
                    Employee Well-being Insights Platform
                </Typography>
                <Typography variant="body2" color="text.secondary" mb={4}>
                    Inicia sesión con tu cuenta de Microsoft para acceder al panel de tu equipo.
                </Typography>

                {/* Botón login */}
                <Button
                    variant="contained"
                    size="large"
                    fullWidth
                    href={loginUrl}
                    className="login-button"
                    sx={{
                        bgcolor: "primary.main",
                        "&:hover": { bgcolor: "primary.dark" },
                    }}
                >
                    Conectar con Microsoft
                </Button>

                {/* Nota privacidad */}
                <Box className="login-privacy-note">
                    🔒 No se almacenan mensajes ni contenido personal. Solo métricas numéricas agregadas por equipo.
                </Box>
            </Paper>
        </Box>
    );
}

