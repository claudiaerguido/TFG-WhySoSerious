import { createContext, useContext } from "react";

export const AuthContext = createContext(null);

/** Hook para consumir el contexto de autenticacion. */
export function useMe() {
    return useContext(AuthContext);
}
