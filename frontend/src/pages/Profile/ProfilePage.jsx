import { useState } from "react";
import { Box, Typography, Avatar, Chip, Divider, Card, CardContent, Grid, Select, MenuItem, Button, LinearProgress, Snackbar, Alert } from "@mui/material";
import BadgeIcon from "@mui/icons-material/Badge";
import EmailIcon from "@mui/icons-material/Email";
import AdminPanelSettingsIcon from "@mui/icons-material/AdminPanelSettings";
import ShieldOutlinedIcon from "@mui/icons-material/ShieldOutlined";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import { useMe } from "../../context/authState";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchAdminSettings, updateAdminSettings } from "../../api/api";
import "./ProfilePage.css";

const ROLE_CONFIG = {
    admin: {
        label: "Administrador Global",
        color: "#f43f5e",
        description: "Acceso completo a todos los workspaces y métricas de la organización.",
    },
    manager: {
        label: "Mánager / Dirección",
        color: "#6366f1",
        description: "Visión global de todos los equipos y proyectos asignados.",
    },
    employee: {
        label: "Colaborador",
        color: "#6366f1",
        description: "Acceso a tu perfil personal y a tus métricas de riesgo individual.",
    },
};

const AdminSettingsSection = () => {
    const queryClient = useQueryClient();
    const [snackbar, setSnackbar] = useState({ open: false, message: "", severity: "success" });

    const { data: settings, isLoading } = useQuery({
        queryKey: ["adminSettings"],
        queryFn: fetchAdminSettings,
    });

    const mutation = useMutation({
        mutationFn: updateAdminSettings,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["adminSettings"] });
            setSnackbar({ open: true, message: "Configuración actualizada correctamente.", severity: "success" });
        },
        onError: (err) => {
            setSnackbar({ open: true, message: "Error al actualizar: " + err.message, severity: "error" });
        }
    });

    if (isLoading) return <LinearProgress sx={{ mt: 2, borderRadius: 2 }} />;

    const handleClose = () => setSnackbar(s => ({ ...s, open: false }));

    const handleSave = (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        mutation.mutate({
            fiscal_year_start_month: parseInt(formData.get("month")),
        });
    };

    return (
        <Box sx={{ mt: 5 }}>
            <Typography variant="h5" fontWeight={800} sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <AdminPanelSettingsIcon sx={{ color: 'primary.main' }} />
                Configuración de la Organización
            </Typography>

            <Card sx={{ borderRadius: 4, border: '1px solid rgba(99,102,241,0.12)', bgcolor: 'rgba(99,102,241,0.02)' }}>
                <CardContent sx={{ p: 4 }}>
                    <form onSubmit={handleSave}>
                        <Grid container spacing={4} alignItems="flex-end">
                            <Grid item xs={12} md={6}>
                                <Typography variant="caption" fontWeight={700} color="text.secondary" sx={{ mb: 1, display: 'block', textTransform: 'uppercase' }}>
                                    Mes de Inicio Año Fiscal
                                </Typography>
                                <Select
                                    name="month"
                                    defaultValue={settings?.fiscal_year_start_month || 1}
                                    fullWidth
                                    size="small"
                                    sx={{ bgcolor: 'white', borderRadius: 2 }}
                                >
                                    <MenuItem value={1}>Enero</MenuItem>
                                    <MenuItem value={2}>Febrero</MenuItem>
                                    <MenuItem value={3}>Marzo</MenuItem>
                                    <MenuItem value={4}>Abril</MenuItem>
                                    <MenuItem value={5}>Mayo</MenuItem>
                                    <MenuItem value={6}>Junio</MenuItem>
                                    <MenuItem value={7}>Julio</MenuItem>
                                    <MenuItem value={8}>Agosto</MenuItem>
                                    <MenuItem value={9}>Septiembre</MenuItem>
                                    <MenuItem value={10}>Octubre</MenuItem>
                                    <MenuItem value={11}>Noviembre</MenuItem>
                                    <MenuItem value={12}>Diciembre</MenuItem>
                                </Select>
                            </Grid>

                            <Grid item xs={12} md={6}>
                                <Button
                                    type="submit"
                                    variant="contained"
                                    fullWidth
                                    disabled={mutation.isPending}
                                    sx={{
                                        height: 40,
                                        borderRadius: 2,
                                        boxShadow: '0 4px 12px rgba(99,102,241,0.2)',
                                        textTransform: 'none',
                                        fontWeight: 700
                                    }}
                                >
                                    {mutation.isPending ? "Guardando..." : "Guardar Cambios"}
                                </Button>
                            </Grid>

                            {settings?.fy_start_date && (
                                <Grid item xs={12}>
                                    <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                                        Ciclo fiscal actual (calculado automáticamente): del <strong>{settings.fy_start_date}</strong> al <strong>{settings.fy_end_date}</strong> (FY {settings.current_fiscal_year}).
                                    </Typography>
                                </Grid>
                            )}
                        </Grid>
                    </form>
                </CardContent>
            </Card>

            <Snackbar open={snackbar.open} autoHideDuration={4000} onClose={handleClose} anchorOrigin={{ vertical: "bottom", horizontal: "center" }}>
                <Alert onClose={handleClose} severity={snackbar.severity} sx={{ width: "100%" }}>
                    {snackbar.message}
                </Alert>
            </Snackbar>
        </Box>
    );
};

export default function ProfilePage() {
    const { user } = useMe();
    const role = user?.role || "employee";
    const cfg = ROLE_CONFIG[role] || ROLE_CONFIG.employee;

    const initials = user?.display_name
        ? user.display_name.split(" ").map(n => n[0]).join("").toUpperCase().substring(0, 2)
        : "??";

    return (
        <Box className="profile-container">
            <Box sx={{ mb: 4 }}>
                <Typography variant="h4" fontWeight={800} sx={{ letterSpacing: -0.5, mb: 0.5 }}>
                    Ajustes de Perfil
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    Gestiona la información de tu cuenta corporativa y tus preferencias de visualización.
                </Typography>
            </Box>

            <Card sx={{ borderRadius: 4, border: '1px solid rgba(0,0,0,0.06)', boxShadow: '0 4px 20px rgba(0,0,0,0.03)' }}>
                <CardContent sx={{ p: '40px !important' }}>
                    {/* Fila de Avatar y Nombre */}
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, mb: 4 }}>
                        <Avatar sx={{
                            width: 88, height: 88,
                            bgcolor: 'primary.main', fontSize: 28, fontWeight: 800,
                            boxShadow: '0 4px 20px rgba(99,102,241,0.2)'
                        }}>
                            {initials}
                        </Avatar>
                        <Box>
                            <Typography variant="h5" fontWeight={800} sx={{ letterSpacing: -0.3, mb: 1 }}>
                                {user?.display_name ?? "—"}
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                <Chip
                                    icon={<CheckCircleIcon sx={{ fontSize: '14px !important', color: '#16a34a !important' }} />}
                                    label="Cuenta Verificada"
                                    size="small"
                                    sx={{ bgcolor: '#dcfce7', color: '#16a34a', fontWeight: 700, fontSize: 11, border: 'none' }}
                                />
                                <Chip
                                    label={cfg.label}
                                    size="small"
                                    sx={{ bgcolor: `${cfg.color}15`, color: cfg.color, fontWeight: 700, fontSize: 11, border: 'none' }}
                                />
                            </Box>
                        </Box>
                    </Box>

                    <Divider sx={{ mb: 4, opacity: 0.6 }} />

                    <Grid container spacing={5}>
                        <Grid item xs={12} md={7}>
                            <Typography variant="overline" color="text.disabled" fontWeight={700} sx={{ letterSpacing: 1.5, display: 'block', mb: 3 }}>
                                Información Personal
                            </Typography>

                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                                <Box sx={{ display: 'flex', gap: 2 }}>
                                    <Box sx={{ width: 40, height: 40, borderRadius: 2, bgcolor: 'rgba(0,0,0,0.03)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'text.secondary', flexShrink: 0 }}>
                                        <EmailIcon />
                                    </Box>
                                    <Box>
                                        <Typography variant="caption" color="text.disabled" sx={{ fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, fontSize: '10px' }}>
                                            Correo Electrónico
                                        </Typography>
                                        <Typography variant="body1" fontWeight={600}>
                                            {user?.user_email ?? "—"}
                                        </Typography>
                                    </Box>
                                </Box>

                                <Box sx={{ display: 'flex', gap: 2 }}>
                                    <Box sx={{ width: 40, height: 40, borderRadius: 2, bgcolor: 'rgba(0,0,0,0.03)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'text.secondary', flexShrink: 0 }}>
                                        <BadgeIcon />
                                    </Box>
                                    <Box>
                                        <Typography variant="caption" color="text.disabled" sx={{ fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, fontSize: '10px' }}>
                                            Nombre Completo
                                        </Typography>
                                        <Typography variant="body1" fontWeight={600}>
                                            {user?.display_name ?? "—"}
                                        </Typography>
                                    </Box>
                                </Box>

                                <Box sx={{ display: 'flex', gap: 2 }}>
                                    <Box sx={{ width: 40, height: 40, borderRadius: 2, bgcolor: 'rgba(0,0,0,0.03)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'text.secondary', flexShrink: 0 }}>
                                        <AdminPanelSettingsIcon />
                                    </Box>
                                    <Box>
                                        <Typography variant="caption" color="text.disabled" sx={{ fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, fontSize: '10px' }}>
                                            Rol de Sistema
                                        </Typography>
                                        <Typography variant="body1" fontWeight={600} sx={{ color: cfg.color }}>
                                            {cfg.label}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.3, maxWidth: 300 }}>
                                            {cfg.description}
                                        </Typography>
                                    </Box>
                                </Box>
                            </Box>
                        </Grid>

                        <Grid item xs={12} md={5}>
                            <Box sx={{ p: 3.5, borderRadius: 3, bgcolor: 'rgba(15,23,42,0.02)', border: '1px solid rgba(0,0,0,0.04)', height: '100%' }}>
                                <ShieldOutlinedIcon sx={{ fontSize: 36, color: 'primary.main', mb: 2 }} />
                                <Typography variant="subtitle1" fontWeight={800} sx={{ mb: 1.5, letterSpacing: -0.3 }}>
                                    Seguridad y Privacidad
                                </Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.7, mb: 2 }}>
                                    Tu cuenta está vinculada a Microsoft Graph API. No almacenamos tus credenciales ni mensajes privados. La monitorización es agregada y anónima.
                                </Typography>
                                <Divider sx={{ borderStyle: 'dashed', mb: 1.5 }} />
                                <Typography variant="caption" color="primary" sx={{ fontWeight: 700, cursor: 'pointer', '&:hover': { textDecoration: 'underline' } }}>
                                    Ver política de privacidad →
                                </Typography>
                            </Box>
                        </Grid>
                    </Grid>
                </CardContent>
            </Card>

            {role === 'admin' && <AdminSettingsSection />}
        </Box>
    );
}
