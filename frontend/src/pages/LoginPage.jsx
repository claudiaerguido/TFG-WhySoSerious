import { Box, Button, Typography, Paper } from "@mui/material";
import MicrosoftIcon from "@mui/icons-material/Apple"; // placeholder
import { loginUrl } from "../api/backend";

export default function LoginPage() {
    return (
        <Box
            sx={{
                minHeight: "100vh",
                bgcolor: "background.default",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                background: "radial-gradient(ellipse at 60% 40%, #1e1b4b 0%, #0f172a 70%)",
            }}
        >
            <Paper
                elevation={0}
                sx={{
                    p: 6,
                    borderRadius: 4,
                    textAlign: "center",
                    maxWidth: 440,
                    width: "100%",
                    bgcolor: "background.paper",
                    border: "1px solid rgba(255,255,255,0.08)",
                    backdropFilter: "blur(10px)",
                }}
            >
                {/* Logo */}
                <Box sx={{ fontSize: 64, mb: 2 }}>🧠</Box>

                <Typography variant="h4" fontWeight={800} color="text.primary" gutterBottom>
                    WhySoSerious
                </Typography>
                <Typography variant="body1" color="text.secondary" mb={1}>
                    Observatorio de Salud Mental Laboral
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
                    sx={{
                        py: 1.5,
                        fontSize: 16,
                        fontWeight: 700,
                        bgcolor: "primary.main",
                        "&:hover": { bgcolor: "primary.dark" },
                        borderRadius: 2,
                    }}
                >
                    Conectar con Microsoft
                </Button>

                {/* Nota privacidad */}
                <Box
                    sx={{
                        mt: 4,
                        p: 2,
                        borderRadius: 2,
                        bgcolor: "rgba(255,255,255,0.04)",
                        color: "text.secondary",
                        fontSize: 12,
                    }}
                >
                    🔒 No se almacenan mensajes ni contenido personal. Solo métricas numéricas agregadas por equipo.
                </Box>
            </Paper>
        </Box>
    );
}
