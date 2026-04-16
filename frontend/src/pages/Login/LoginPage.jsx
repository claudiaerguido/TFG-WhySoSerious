import { Box, Button, Typography, Paper, Grid } from "@mui/material";
import { loginUrl } from "../../api/backend";
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import VerifiedUserOutlinedIcon from '@mui/icons-material/VerifiedUserOutlined';
import SecurityOutlinedIcon from '@mui/icons-material/SecurityOutlined';
import VisibilityOffOutlinedIcon from '@mui/icons-material/VisibilityOffOutlined';
import "./LoginPage.css";

export default function LoginPage() {
    return (
        <Box className="login-container">
            <div className="login-glow"></div>

            <Box className="login-layout">
                {/* Lateral Izquierdo: Valor y Marca */}
                <Box className="login-info-side">
                    <Box className="login-brand-header">
                        <Typography variant="h2" className="login-main-title">
                            Analiza el bienestar de tus equipos <br />
                            <Box component="span" sx={{
                                background: 'linear-gradient(90deg, #818cf8, #c084fc)',
                                WebkitBackgroundClip: 'text',
                                WebkitTextFillColor: 'transparent',
                            }}>
                                con privacidad.
                            </Box>
                        </Typography>
                        <Typography variant="h6" className="login-subtitle">
                            La plataforma que transforma la comunicación en métricas
                            accionables de riesgo psicosocial sin comprometer el anonimato.
                        </Typography>
                    </Box>

                    <Box className="login-benefits-list">
                        <BenefitItem
                            text="Supervisa el bienestar organizacional en tiempo real."
                        />
                        <BenefitItem
                            text="Identifica señales de agotamiento (burnout) por proyecto."
                        />
                        <BenefitItem
                            text="Garantiza el anonimato mediante agregación de datos."
                        />
                    </Box>
                </Box>

                {/* Lateral Derecho: Card de Login */}
                <Box className="login-card-side">
                    <Paper elevation={0} className="login-paper-v2">
                        <Box className="login-card-logo">
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M3 13C3 13 4.5 13 5.5 11C6.5 9 7.5 4 8.5 4C9.5 4 11 18 12 18C13 18 14.5 14 15.5 14C16.5 14 18 16 19 16C20 16 21 15 21 15" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                        </Box>

                        <Typography variant="h5" fontWeight={800} color="white" gutterBottom>
                            Accede a tu panel
                        </Typography>
                        <Typography variant="body2" sx={{ color: "#94a3b8", mb: 4 }}>
                            Inicia sesión para visualizar las tendencias <br /> de riesgo de tu organización.
                        </Typography>

                        <Button
                            variant="contained"
                            fullWidth
                            href={loginUrl}
                            className="login-button-ms"
                            startIcon={<MicrosoftIcon />}
                        >
                            Continuar con Microsoft
                        </Button>

                        <Box className="login-trust-footer">
                            <TrustItem icon={<VisibilityOffOutlinedIcon fontSize="small" />} text="No leemos mensajes individuales" />
                            <TrustItem icon={<VerifiedUserOutlinedIcon fontSize="small" />} text="Análisis basado en métricas agregadas" />
                            <TrustItem icon={<SecurityOutlinedIcon fontSize="small" />} text="Acceso seguro vía Microsoft 365" />
                        </Box>
                    </Paper>
                </Box>
            </Box>
        </Box>
    );
}

function BenefitItem({ text }) {
    return (
        <Box className="login-benefit-item">
            <CheckCircleOutlineIcon className="benefit-icon" />
            <Typography variant="body1" fontWeight={500}>{text}</Typography>
        </Box>
    );
}

function TrustItem({ icon, text }) {
    return (
        <Box className="trust-item">
            {icon}
            <Typography variant="caption" fontWeight={600}>{text}</Typography>
        </Box>
    );
}

function MicrosoftIcon() {
    return (
        <svg width="20" height="20" viewBox="0 0 23 23" style={{ marginRight: 8 }}>
            <path fill="#f3f3f3" d="M0 0h23v23H0z" />
            <path fill="#f25022" d="M1 1h10v10H1z" />
            <path fill="#7fba00" d="M12 1h10v10H12z" />
            <path fill="#00a4ef" d="M1 12h10v10H1z" />
            <path fill="#ffb900" d="M12 12h10v10H12z" />
        </svg>
    );
}
