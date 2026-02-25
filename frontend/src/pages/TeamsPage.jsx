import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
    Box, Typography, Table, TableBody, TableCell, TableContainer,
    TableHead, TableRow, Paper, Chip, Button, Skeleton, Alert,
} from "@mui/material";
import VisibilityIcon from "@mui/icons-material/Visibility";
import LockIcon from "@mui/icons-material/Lock";
import StarIcon from "@mui/icons-material/Star";
import { fetchMyWorkspaces } from "../api/backend";
import { useMe } from "../context/AuthContext";
import { RISK_COLOR, fmtPct } from "../utils/risk";

const TYPE_LABEL = { team: "Equipo Organizativo", project: "Proyecto Asignado" };
const TYPE_COLOR = { team: "primary", project: "secondary" };

function WorkspaceRow({ ws, isOwner }) {
    const navigate = useNavigate();
    return (
        <TableRow hover>
            <TableCell>
                <Typography fontWeight={600}>{ws.name}</Typography>
            </TableCell>
            <TableCell>
                <Chip
                    label={TYPE_LABEL[ws.type] ?? ws.type}
                    size="small"
                    variant="outlined"
                    color={TYPE_COLOR[ws.type] ?? "default"}
                    sx={{ fontSize: 11, fontWeight: 600 }}
                />
            </TableCell>
            <TableCell>
                {isOwner && (
                    <Chip
                        icon={<StarIcon sx={{ fontSize: 14 }} />}
                        label="Responsable"
                        size="small"
                        color="warning"
                        variant="outlined"
                        sx={{ fontSize: 10, fontWeight: 700, mr: 1, borderColor: "warning.main", color: "warning.main" }}
                    />
                )}
                {ws.owner_email ?? "—"}
            </TableCell>
            <TableCell>
                <Button
                    size="small"
                    variant="outlined"
                    startIcon={<VisibilityIcon />}
                    onClick={() => navigate(`/workspaces/${ws.id}`)}
                >
                    Detalle
                </Button>
            </TableCell>
        </TableRow>
    );
}

// Subcomponente de tabla para reutilizar
function WorkspaceTable({ title, data, currentUser }) {
    if (data.length === 0) return null;
    return (
        <Box mb={4}>
            <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 1.5, color: "text.primary" }}>
                {title} ({data.length})
            </Typography>
            <TableContainer component={Paper} sx={{ bgcolor: "background.paper", borderRadius: 3, border: "1px solid rgba(255,255,255,0.05)" }}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell sx={{ fontWeight: 700, color: "text.secondary" }}>Nombre</TableCell>
                            <TableCell sx={{ fontWeight: 700, color: "text.secondary" }}>Tipo</TableCell>
                            <TableCell sx={{ fontWeight: 700, color: "text.secondary" }}>Propietario / Responsable</TableCell>
                            <TableCell sx={{ fontWeight: 700, color: "text.secondary" }}>Acción</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {data.map((ws) => (
                            <WorkspaceRow key={ws.id} ws={ws} isOwner={ws.owner_email === currentUser?.user_email} />
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </Box>
    );
}

export default function TeamsPage() {
    const { user } = useMe();
    const { data, isLoading, isError } = useQuery({
        queryKey: ["myWorkspaces"],
        queryFn: fetchMyWorkspaces,
        staleTime: 60_000,
    });

    const workspaces = data?.workspaces ?? [];
    const role = data?.role;

    if (import.meta.env.DEV && data) {
        console.log("[TeamsPage] workspaces payload:", data);
    }

    const teams = workspaces.filter(w => w.type === "team");
    const projects = workspaces.filter(w => w.type === "project");
    const unclassified = workspaces.filter(w => w.type !== "team" && w.type !== "project");

    return (
        <Box>
            <Box mb={4} display="flex" alignItems="flex-start" justifyContent="space-between" flexWrap="wrap" gap={2}>
                <Box>
                    <Typography variant="h5" fontWeight={800}>Mis Equipos / Proyectos</Typography>
                    <Typography variant="body2" color="text.secondary" mt={0.5}>
                        {user?.role === "manager"
                            ? "Visualizando como: Dirección (Mánager). Acceso total a las estructuras de la empresa."
                            : "Vista limitada a los equipos y proyectos en los que tienes asignación vigente."
                        }
                    </Typography>
                </Box>
            </Box>

            {isError && (
                <Alert severity="error" sx={{ mb: 3 }}>
                    No se pudieron cargar los workspaces. Comprueba la conexión con el backend.
                </Alert>
            )}

            {!isLoading && !isError && workspaces.length === 0 && role && (
                <Alert severity="info" icon={<LockIcon />} sx={{ mb: 3 }}>
                    No tienes workspaces asignados en este momento. Contacta con tu responsable o administrador de Entra ID.
                </Alert>
            )}

            {!isLoading && workspaces.length > 0 && (
                <Box>
                    <WorkspaceTable title="🏢 Equipos Organizativos" data={teams} currentUser={user} />
                    <WorkspaceTable title="🚀 Proyectos Especiales" data={projects} currentUser={user} />
                    <WorkspaceTable title="Agrupaciones Genéricas" data={unclassified} currentUser={user} />
                </Box>
            )}

            {isLoading && (
                <TableContainer component={Paper} sx={{ bgcolor: "background.paper", borderRadius: 3 }}>
                    <Table>
                        <TableBody>
                            {Array.from({ length: 3 }).map((_, i) => (
                                <TableRow key={i}>
                                    {Array.from({ length: 4 }).map((_, j) => (
                                        <TableCell key={j}><Skeleton /></TableCell>
                                    ))}
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            )}
        </Box>
    );
}
