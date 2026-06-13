import { getAuthHeaders } from "../utils/utils";

const API_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:7000";

export const presenceService = {
  // Heartbeat: marca al usuario actual como conectado a la web.
  ping: async (): Promise<void> => {
    try {
      await fetch(`${API_URL}/presence/ping`, {
        method: "POST",
        headers: getAuthHeaders(),
      });
    } catch (e) {
      // La presencia es best-effort: no rompemos la UI si falla un ping.
      console.warn("Presence ping warning:", e);
    }
  },

  // Lista de user_id conectados actualmente.
  getOnline: async (): Promise<number[]> => {
    try {
      const res = await fetch(`${API_URL}/presence/online`, {
        method: "GET",
        headers: getAuthHeaders(),
      });
      if (!res.ok) throw new Error("Error obteniendo presencia");
      const data = await res.json();
      // Aceptamos {online: [...]} o directamente [...]
      const ids = Array.isArray(data) ? data : data.online;
      return Array.isArray(ids) ? ids.map((id: unknown) => Number(id)) : [];
    } catch (e) {
      console.warn("Presence online warning:", e);
      return [];
    }
  },
};
