import { useState, useEffect } from "react";
import { fetchMe } from "../api/api";
import { AuthContext } from "./authState";

/**
 * Provee { user, role, isLoading } a toda la app.
 * user = { authenticated, user_email, display_name, role } | null
 * Si no hay sesión, user es null.
 */
export function AuthProvider({ children }) {
    const [user, setUser] = useState(undefined);   // undefined = cargando
    const [isLoading, setLoading] = useState(true);

    useEffect(() => {
        fetchMe()
            .then((data) => {
                setUser(data?.authenticated ? data : null);
            })
            .catch(() => setUser(null))
            .finally(() => setLoading(false));
    }, []);

    const role = user?.role ?? null;

    return (
        <AuthContext.Provider value={{ user, role, isLoading }}>
            {children}
        </AuthContext.Provider>
    );
}
