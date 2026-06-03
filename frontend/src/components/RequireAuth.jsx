import { Navigate } from "react-router-dom";
import { Box, CircularProgress } from "@mui/material";
import { useMe } from "../context/authState";

export default function RequireAuth({ children }) {
  const { user, isLoading } = useMe();

  if (isLoading) {
    return (
      <Box sx={{ display: "flex", height: "100vh", justifyContent: "center", alignItems: "center" }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!user?.authenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
