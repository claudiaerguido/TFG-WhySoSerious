import { useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import {
    Box, Drawer, AppBar, Toolbar, Typography, List, ListItemButton,
    ListItemIcon, ListItemText, IconButton, Avatar, Divider, Chip, Tooltip, Card, CardContent
} from "@mui/material";
import DashboardIcon from "@mui/icons-material/Dashboard";
import GroupsIcon from "@mui/icons-material/Groups";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import LogoutIcon from "@mui/icons-material/LogoutOutlined";
import MenuIcon from "@mui/icons-material/Menu";
import { logoutUrl } from "../api/backend";
import { useMe } from "../context/AuthContext";

const DRAWER_WIDTH = 260;

const NAV_ITEMS = [
    { label: "Dashboard", icon: <DashboardIcon />, path: "/" },
    { label: "Equipos", icon: <GroupsIcon />, path: "/teams" },
    { label: "Mi Perfil", icon: <AccountCircleIcon />, path: "/profile" },
];

export default function AppShell() {
    const [mobileOpen, setMobileOpen] = useState(false);
    const navigate = useNavigate();
    const location = useLocation();
    const { user } = useMe();

    const drawerContent = (
        <Box sx={{ display: "flex", flexDirection: "column", height: "100%", bgcolor: "#fff" }}>
            {/* Logo */}
            <Box sx={{ px: 3, py: 4, display: "flex", alignItems: "center", gap: 1.5 }}>
                <Box sx={{
                    bgcolor: "primary.main",
                    width: 36, height: 36,
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 4px 12px rgba(99, 102, 241, 0.25)'
                }}>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M4 17L9 17L12 10L15 24L18 14L21 20L24 17L30 17" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                </Box>
                <Box>
                    <Typography variant="subtitle1" fontWeight={900} color="text.primary" sx={{ letterSpacing: -0.5, lineHeight: 1 }}>
                        WhySoSerious
                    </Typography>
                    <Typography variant="caption" sx={{ color: "primary.main", fontWeight: 800, fontSize: '11px', textTransform: 'uppercase', letterSpacing: 1 }}>
                        ORGANIZATIONAL HEALTH
                    </Typography>
                </Box>
            </Box>

            <List sx={{ px: 2, mt: 1, flexGrow: 1 }}>
                {NAV_ITEMS.map(({ label, icon, path }) => {
                    const active = location.pathname === path;
                    return (
                        <ListItemButton
                            key={path}
                            onClick={() => {
                                navigate(path);
                                setMobileOpen(false);
                            }}
                            selected={active}
                            sx={{
                                borderRadius: 3,
                                mb: 1,
                                py: 1.2,
                                "&.Mui-selected": {
                                    bgcolor: "primary.main",
                                    color: "#fff",
                                    "& .MuiListItemIcon-root": { color: "#fff" },
                                    "&:hover": { bgcolor: "primary.dark" },
                                },
                                "&:hover": { bgcolor: "rgba(99, 102, 241, 0.04)" },
                            }}
                        >
                            <ListItemIcon sx={{ minWidth: 38, color: active ? "#fff" : "text.secondary" }}>
                                {icon}
                            </ListItemIcon>
                            <ListItemText
                                primary={label}
                                primaryTypographyProps={{ fontSize: 14, fontWeight: active ? 700 : 600, letterSpacing: -0.2 }}
                            />
                        </ListItemButton>
                    );
                })}
            </List>

            <Divider sx={{ mx: 2, opacity: 0.5 }} />

            <Box sx={{ p: 2, mb: 2 }}>
                <Card sx={{ bgcolor: 'rgba(99, 102, 241, 0.03)', border: '1px dashed rgba(99, 102, 241, 0.2)', boxShadow: 'none' }}>
                    <CardContent sx={{ p: '16px !important' }}>
                        <Typography variant="caption" fontWeight={800} color="primary" sx={{ textTransform: 'uppercase', display: 'block', mb: 0.5 }}>
                            Modo Demo
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                            Datos analizados vía Microsoft Graph API
                        </Typography>
                    </CardContent>
                </Card>
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
                        bgcolor: "#fff",
                        borderRight: "1px solid rgba(0,0,0,0.05)",
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
                    "& .MuiDrawer-paper": { width: DRAWER_WIDTH, bgcolor: "#fff" },
                }}
            >
                {drawerContent}
            </Drawer>

            {/* Contenido principal */}
            <Box sx={{ flexGrow: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
                <AppBar
                    position="sticky"
                    elevation={0}
                    sx={{
                        bgcolor: "rgba(248, 250, 252, 0.8)",
                        backdropFilter: "blur(8px)",
                        borderBottom: "1px solid rgba(0,0,0,0.05)",
                        color: "text.primary",
                    }}
                >
                    <Toolbar sx={{ justifyContent: 'space-between' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <IconButton
                                edge="start"
                                sx={{ mr: 2, display: { sm: "none" } }}
                                onClick={() => setMobileOpen(true)}
                            >
                                <MenuIcon />
                            </IconButton>
                            <Typography variant="h6" sx={{ fontWeight: 800, letterSpacing: -0.5 }}>
                                {NAV_ITEMS.find((n) => n.path === location.pathname)?.label ?? "Panel de analítica"}
                            </Typography>
                        </Box>

                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <Box sx={{ display: { xs: 'none', md: 'flex' }, flexDirection: 'column', alignItems: 'flex-end' }}>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    {user?.role === "manager" && (
                                        <Chip label="Dirección" size="small" sx={{ height: 18, fontSize: 10, bgcolor: "warning.main", color: "#fff", fontWeight: 800, border: 'none' }} />
                                    )}
                                    <Typography variant="body2" sx={{ fontWeight: 700, color: "text.primary" }}>
                                        {user?.display_name || "Usuario"}
                                    </Typography>
                                </Box>
                                <Typography variant="caption" sx={{ color: "text.secondary", fontWeight: 500 }}>
                                    {user?.user_email || ""}
                                </Typography>
                            </Box>
                            <Tooltip title="Mi perfil">
                                <Avatar
                                    onClick={() => navigate('/profile')}
                                    sx={{ bgcolor: "primary.main", width: 38, height: 38, fontSize: 14, fontWeight: 700, boxShadow: '0 2px 8px rgba(99, 102, 241, 0.2)', cursor: 'pointer', '&:hover': { opacity: 0.85 } }}
                                >
                                    {user?.display_name ? user.display_name.substring(0, 2).toUpperCase() : "U"}
                                </Avatar>
                            </Tooltip>
                            <Tooltip title="Cerrar sesión">
                                <IconButton href={logoutUrl} sx={{ color: "text.secondary", ml: 0.5, bgcolor: 'rgba(0,0,0,0.02)' }}>
                                    <LogoutIcon fontSize="small" />
                                </IconButton>
                            </Tooltip>
                        </Box>
                    </Toolbar>
                </AppBar>

                <Box sx={{ p: { xs: 2, sm: 4, md: 6 } }}>
                    <Outlet />
                </Box>
            </Box>
        </Box >
    );
}
