import { Box, Typography, Avatar, Chip, Divider, Card, CardContent } from "@mui/material";
import BadgeIcon from "@mui/icons-material/Badge";
import EmailIcon from "@mui/icons-material/Email";
import AdminPanelSettingsIcon from "@mui/icons-material/AdminPanelSettings";
import EngineeringIcon from "@mui/icons-material/Engineering";
import PersonIcon from "@mui/icons-material/Person";
import { useMe } from "../../context/AuthContext";

const ROLE_CONFIG = {
    admin: {
        label: "Administrador",
        color: "#f43f5e",
        icon: <AdminPanelSettingsIcon fontSize="small" />,
        description: "Acceso completo a todos los workspaces y métricas de la organización.",
    },
    manager: {
        label: "Dirección / Manager",
        color: "#f59e0b",
        icon: <EngineeringIcon fontSize="small" />,
        description: "Visión global de todos los equipos y proyectos asignados.",
    },
    employee: {
        label: "Empleado",
        color: "#6366f1",
        icon: <PersonIcon fontSize="small" />,
        description: "Acceso a los workspaces donde eres responsable.",
    },
};

export default function ProfilePage() {
    const { user } = useMe();

    const role = user?.role ?? "employee";
    const cfg = ROLE_CONFIG[role] ?? ROLE_CONFIG.employee;
    const initials = user?.display_name
        ? user.display_name.substring(0, 2).toUpperCase()
        : "??";

    return (
        <Box sx={{ maxWidth: 600, mx: "auto", py: 4, px: { xs: 2, sm: 0 } }}>
            {/* Encabezado */}
            <Typography variant="h5" fontWeight={700} sx={{ mb: 1 }}>
                Mi Perfil
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
                Información de tu cuenta de Microsoft conectada.
            </Typography>

            {/* Card principal */}
            <Card sx={{
                bgcolor: "rgba(255,255,255,0.02)",
                border: "1px solid rgba(255,255,255,0.06)",
                borderRadius: 3,
                boxShadow: "none",
            }}>
                <CardContent sx={{ p: 4, "&:last-child": { pb: 4 } }}>

                    {/* Avatar + nombre */}
                    <Box sx={{ display: "flex", alignItems: "center", gap: 3, mb: 4 }}>
                        <Avatar sx={{
                            width: 64, height: 64,
                            bgcolor: "primary.main",
                            fontSize: 24, fontWeight: 700,
                        }}>
                            {initials}
                        </Avatar>
                        <Box>
                            <Typography variant="h6" fontWeight={700}>
                                {user?.display_name ?? "—"}
                            </Typography>
                            <Chip
                                icon={cfg.icon}
                                label={cfg.label}
                                size="small"
                                sx={{
                                    mt: 0.5,
                                    bgcolor: `${cfg.color}15`,
                                    color: cfg.color,
                                    fontWeight: 600,
                                    border: "none",
                                    "& .MuiChip-icon": { color: cfg.color },
                                }}
                            />
                        </Box>
                    </Box>

                    <Divider sx={{ borderColor: "rgba(255,255,255,0.06)", mb: 3 }} />

                    {/* Detalles */}
                    <Box sx={{ display: "flex", flexDirection: "column", gap: 2.5 }}>

                        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                            <EmailIcon sx={{ fontSize: 18, color: "text.disabled" }} />
                            <Box>
                                <Typography variant="caption" color="text.disabled" display="block">
                                    Correo corporativo
                                </Typography>
                                <Typography variant="body2" fontWeight={500}>
                                    {user?.user_email ?? "—"}
                                </Typography>
                            </Box>
                        </Box>

                        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                            <BadgeIcon sx={{ fontSize: 18, color: "text.disabled" }} />
                            <Box>
                                <Typography variant="caption" color="text.disabled" display="block">
                                    Nombre completo
                                </Typography>
                                <Typography variant="body2" fontWeight={500}>
                                    {user?.display_name ?? "—"}
                                </Typography>
                            </Box>
                        </Box>

                        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                            <AdminPanelSettingsIcon sx={{ fontSize: 18, color: "text.disabled" }} />
                            <Box>
                                <Typography variant="caption" color="text.disabled" display="block">
                                    Rol en la plataforma
                                </Typography>
                                <Typography variant="body2" fontWeight={500} sx={{ color: cfg.color }}>
                                    {cfg.label}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                    {cfg.description}
                                </Typography>
                            </Box>
                        </Box>

                    </Box>
                </CardContent>
            </Card>

            {/* Nota de privacidad */}
            <Typography variant="caption" color="text.disabled" sx={{ display: "block", mt: 3, textAlign: "center" }}>
                🔒 Estos datos provienen de tu cuenta Microsoft 365 y no se almacenan localmente.
            </Typography>
        </Box>
    );
}
