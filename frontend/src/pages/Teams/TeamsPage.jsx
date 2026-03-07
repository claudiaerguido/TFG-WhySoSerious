import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
    Box, Typography, Table, TableBody, TableCell, TableContainer,
    TableHead, TableRow, Paper, Chip, Button, Skeleton, Alert,
} from "@mui/material";
import VisibilityIcon from "@mui/icons-material/Visibility";
import LockIcon from "@mui/icons-material/Lock";
import StarIcon from "@mui/icons-material/Star";
import { fetchMyWorkspaces } from "../../api/backend";
import { useMe } from "../../context/AuthContext";
import { RISK_COLOR, fmtPct } from "../../utils/risk";
import "./TeamsPage.css";

const TYPE_LABEL = { team: "Equipo Organizativo", project: "Proyecto Asignado" };
const TYPE_COLOR = { team: "primary", project: "secondary" };

function WorkspaceRow({ ws, isOwner }) {
    const navigate = useNavigate();
    return (
        <TableRow hover>
            <TableCell>
                <Typography className="workspace-row-name">{ws.name}</Typography>
            </TableCell>
            <TableCell>
                <Chip
                    label={TYPE_LABEL[ws.type] ?? ws.type}
                    size="small"
                    variant="outlined"
                    color={TYPE_COLOR[ws.type] ?? "default"}
                    className="workspace-type-chip"
                />
            </TableCell>
            <TableCell>
                {isOwner && (
                    <Chip
                        icon={<StarIcon className="workspace-owner-icon" />}
                        label="Responsable"
                        size="small"
                        color="warning"
                        variant="outlined"
                        className="workspace-owner-chip"
                        sx={{ borderColor: "warning.main", color: "warning.main" }}
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
        <Box className="workspace-table-container">
            <Typography variant="subtitle1" className="workspace-table-title" color="text.primary">
                {title} ({data.length})
            </Typography>
            <TableContainer component={Paper} className="workspace-table-paper">
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell className="workspace-table-header-cell">Nombre</TableCell>
                            <TableCell className="workspace-table-header-cell">Tipo</TableCell>
                            <TableCell className="workspace-table-header-cell">Propietario / Responsable</TableCell>
                            <TableCell className="workspace-table-header-cell">Acción</TableCell>
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
        <Box className="teams-page-container">
            <Box className="teams-header-container">
                <Box>
                    <Typography variant="h5" className="teams-title">Mis Equipos / Proyectos</Typography>
                    <Typography variant="body2" color="text.secondary" className="teams-subtitle">
                        {user?.role === "manager"
                            ? "Visualizando como: Dirección (Mánager). Acceso total a las estructuras de la empresa."
                            : "Vista limitada a los equipos y proyectos en los que tienes asignación vigente."
                        }
                    </Typography>
                </Box>
            </Box>

            {isError && (
                <Alert severity="error" className="teams-alert-error">
                    No se pudieron cargar los workspaces. Comprueba la conexión con el backend.
                </Alert>
            )}

            {!isLoading && !isError && workspaces.length === 0 && role && (
                <Alert severity="info" icon={<LockIcon />} className="teams-alert-info">
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
                <TableContainer component={Paper} className="teams-skeleton-paper">
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
