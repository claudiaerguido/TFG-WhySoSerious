import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider, CssBaseline, Box, CircularProgress } from "@mui/material";
import theme from "./theme";
import { AuthProvider } from "./context/AuthContext";

import AppShell from "./components/AppShell";
import {
  LoginPage,
  DashboardPage,
  TeamsPage,
  ProjectDetailPage,
  ProfilePage,
  EmployeeProfilePage,
} from "./pages";
import { useMe } from "./context/AuthContext";

function RequireAuth({ children }) {
  const { user, isLoading } = useMe();

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!user?.authenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false, refetchOnWindowFocus: false },
  },
});

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route element={<RequireAuth><AppShell /></RequireAuth>}>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/teams" element={<TeamsPage />} />
                <Route path="/team/:id" element={<ProjectDetailPage />} />
                <Route path="/project/:id" element={<ProjectDetailPage />} />
                <Route path="/workspaces/:id" element={<ProjectDetailPage />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/employee/:email" element={<EmployeeProfilePage />} />
              </Route>
              {/* Redirección para rutas no encontradas y evitar pantallas blancas */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </ThemeProvider>
      </AuthProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
