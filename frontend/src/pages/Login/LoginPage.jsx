import { Box, Button, Typography, Paper } from "@mui/material";
import MicrosoftIcon from "@mui/icons-material/Apple"; // placeholder
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
                {/* Logo */}
                <Box className="login-logo">🧠</Box>

                <Typography variant="h4" fontWeight={800} color="text.primary" gutterBottom>
                    WhySoSerious
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
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

