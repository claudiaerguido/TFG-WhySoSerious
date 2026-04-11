import { useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import {
    Box, Drawer, AppBar, Toolbar, Typography, List, ListItemButton,
    ListItemIcon, ListItemText, IconButton, Avatar, Divider, Chip, Tooltip, Card, CardContent
} from "@mui/material";
import DashboardIcon from "@mui/icons-material/Dashboard";
import GroupsIcon from "@mui/icons-material/Groups";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import AssignmentIcon from "@mui/icons-material/Assignment";
import LogoutIcon from "@mui/icons-material/LogoutOutlined";
import MenuIcon from "@mui/icons-material/Menu";
import { logoutUrl } from "../api/backend";
import { useMe } from "../context/AuthContext";

const DRAWER_WIDTH = 260;

const NAV_ITEMS = [
    { label: "Dashboard", icon: <DashboardIcon />, path: "/" },
    { label: "Equipos", icon: <GroupsIcon />, path: "/teams" },
    { label: "Proyectos", icon: <AssignmentIcon />, path: "/projects" },
    { label: "Mi Perfil", icon: <AccountCircleIcon />, path: "/profile" },
];

export default function AppShell() {
    const [mobileOpen, setMobileOpen] = useState(false);
    const navigate = useNavigate();
    const location = useLocation();
    const { user } = useMe();

    const drawerContent = (
        <Box sx={{ display: "flex", flexDirection: "column", height: "100%", bgcolor: "#fff" }}>
            {/* Logo Professional Redesign */}
            <Box sx={{ px: 3.5, py: 4.5, display: "flex", alignItems: "center", gap: 2 }}>
                <Box sx={{
                    position: 'relative',
                    width: 42, height: 42,
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 8px 16px rgba(99, 102, 241, 0.25), inset 0 -2px 5px rgba(0,0,0,0.1)',
                    '&:after': {
                        content: '""',
                        position: 'absolute',
                        top: '15%', left: '15%',
                        width: '30%', height: '30%',
                        borderRadius: '50%',
                        background: 'rgba(255,255,255,0.2)',
                        filter: 'blur(2px)'
                    }
                }}>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M3 13C3 13 4.5 13 5.5 11C6.5 9 7.5 4 8.5 4C9.5 4 11 18 12 18C13 18 14.5 14 15.5 14C16.5 14 18 16 19 16C20 16 21 15 21 15" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                </Box>
                <Box>
                    <Typography variant="h6" sx={{
                        fontWeight: 300,
                        color: "#0f172a",
                        letterSpacing: -1,
                        lineHeight: 1,
                        display: 'flex',
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
