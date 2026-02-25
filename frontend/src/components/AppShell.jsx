import { useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import {
    Box, Drawer, AppBar, Toolbar, Typography, List, ListItemButton,
    ListItemIcon, ListItemText, IconButton, Avatar, Divider, Chip, Tooltip,
} from "@mui/material";
import DashboardIcon from "@mui/icons-material/Dashboard";
import GroupsIcon from "@mui/icons-material/Groups";
import AssessmentIcon from "@mui/icons-material/Assessment";
import MonitorHeartIcon from "@mui/icons-material/MonitorHeart";
import LogoutIcon from "@mui/icons-material/LogoutOutlined";
import MenuIcon from "@mui/icons-material/Menu";
import { logoutUrl } from "../api/backend";
import { useMe } from "../context/AuthContext";

const DRAWER_WIDTH = 240;

const NAV_ITEMS = [
    { label: "Dashboard", icon: <DashboardIcon />, path: "/" },
    { label: "Riesgo de Equipo", icon: <MonitorHeartIcon />, path: "/team-risk" },
    { label: "Mis Equipos", icon: <GroupsIcon />, path: "/teams" },
    { label: "Reportes", icon: <AssessmentIcon />, path: "/reports" },
];
export default function AppShell() {
    const [mobileOpen, setMobileOpen] = useState(false);
    const navigate = useNavigate();
    const location = useLocation();
    const { user } = useMe();

    const drawerContent = (
        <Box sx={{ display: "flex", flexDirection: "column", height: "100%" }}>
            {/* Logo */}
            <Box sx={{ px: 3, py: 3, display: "flex", alignItems: "center", gap: 1.5 }}>
                <Box sx={{ fontSize: 28 }}>🧠</Box>
                <Box>
                    <Typography variant="subtitle1" fontWeight={800} color="primary.light" lineHeight={1.1}>
                        WhySoSerious
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                        Observatorio Laboral
                    </Typography>
                </Box>
            </Box>

            <Divider sx={{ borderColor: "rgba(255,255,255,0.07)" }} />

            {/* Navegación */}
            <List sx={{ px: 1, pt: 2, flexGrow: 1 }}>
                {NAV_ITEMS.map(({ label, icon, path }) => {
                    const active = location.pathname === path;
                    return (
                        <ListItemButton
                            key={path}
                            onClick={() => navigate(path)}
                            selected={active}
                            sx={{
                                borderRadius: 2,
                                mb: 0.5,
                                "&.Mui-selected": {
                                    bgcolor: "primary.dark",
                                    color: "primary.light",
                                    "& .MuiListItemIcon-root": { color: "primary.light" },
                                },
                                "&:hover": { bgcolor: "rgba(255,255,255,0.06)" },
                            }}
                        >
                            <ListItemIcon sx={{ minWidth: 38, color: active ? "primary.light" : "text.secondary" }}>
                                {icon}
                            </ListItemIcon>
                            <ListItemText
                                primary={label}
                                primaryTypographyProps={{ fontSize: 14, fontWeight: active ? 700 : 500 }}
                            />
                        </ListItemButton>
                    );
                })}
            </List>

            <Divider sx={{ borderColor: "rgba(255,255,255,0.07)" }} />

            {/* Footer del drawer */}
            <Box sx={{ px: 2, py: 2 }}>
                <Chip
                    label="Sprint 4 · MVP"
                    size="small"
                    sx={{ bgcolor: "primary.dark", color: "primary.light", fontWeight: 600, fontSize: 11 }}
                />
            </Box>
        </Box>
    );

    return (
        <Box sx={{ display: "flex", minHeight: "100vh", bgcolor: "background.default" }}>
            {/* Sidebar escritorio */}
            <Drawer
                variant="permanent"
                sx={{
                    display: { xs: "none", sm: "block" },
                    width: DRAWER_WIDTH,
                    flexShrink: 0,
                    "& .MuiDrawer-paper": {
                        width: DRAWER_WIDTH,
                        boxSizing: "border-box",
                        bgcolor: "background.paper",
                        borderRight: "1px solid rgba(255,255,255,0.07)",
                    },
                }}
            >
                {drawerContent}
            </Drawer>

            {/* Sidebar móvil */}
            <Drawer
                variant="temporary"
                open={mobileOpen}
                onClose={() => setMobileOpen(false)}
                sx={{
                    display: { xs: "block", sm: "none" },
                    "& .MuiDrawer-paper": { width: DRAWER_WIDTH, bgcolor: "background.paper" },
                }}
            >
                {drawerContent}
            </Drawer>

            {/* Contenido principal */}
            <Box sx={{ flexGrow: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
                {/* TopBar */}
                <AppBar
                    position="static"
                    elevation={0}
                    sx={{
                        bgcolor: "background.paper",
                        borderBottom: "1px solid rgba(255,255,255,0.07)",
                    }}
                >
                    <Toolbar>
                        <IconButton
                            edge="start"
                            sx={{ mr: 1, display: { sm: "none" } }}
                            onClick={() => setMobileOpen(true)}
                        >
                            <MenuIcon />
                        </IconButton>
                        <Typography variant="h6" sx={{ flexGrow: 1, color: "text.primary", fontWeight: 700 }}>
                            {NAV_ITEMS.find((n) => n.path === location.pathname)?.label ?? "Panel de control"}
                        </Typography>
                        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', mr: 2 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                {user?.role === "manager" && (
                                    <Chip label="Dirección" size="small" sx={{ height: 18, fontSize: 10, bgcolor: "warning.dark", color: "warning.contrastText", fontWeight: 700 }} />
                                )}
                                <Typography variant="body2" sx={{ fontWeight: 600, color: "text.primary", lineHeight: 1.2 }}>
                                    {user?.display_name || "Usuario"}
                                </Typography>
                            </Box>
                            <Typography variant="caption" sx={{ color: "text.secondary", lineHeight: 1.2 }}>
                                {user?.user_email || ""}
                            </Typography>
                        </Box>
                        <Avatar sx={{ bgcolor: "primary.main", width: 36, height: 36, fontSize: 14 }}>
                            {user?.display_name ? user.display_name.substring(0, 2).toUpperCase() : "U"}
                        </Avatar>
                        <Tooltip title="Cerrar sesión">
                            <IconButton href={logoutUrl} sx={{ color: "text.secondary", ml: 1 }}>
                                <LogoutIcon fontSize="small" />
                            </IconButton>
                        </Tooltip>
                    </Toolbar>
                </AppBar>

                {/* Página activa */}
                <Box sx={{ flexGrow: 1, p: { xs: 2, sm: 3 }, overflow: "auto" }}>
                    <Outlet />
                </Box>
            </Box>
        </Box >
    );
}
