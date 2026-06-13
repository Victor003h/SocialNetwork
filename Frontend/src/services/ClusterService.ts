import { getAuthHeaders } from "../utils/utils";

const API_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:7000";

// Forma flexible: el gateway reenvía el cluster.to_dict() del subleader.
export interface ClusterNode {
  node_id?: string | number;
  address?: string;
  ip?: string;
  role?: string; // leader | subleader | follower | unknown
  alive?: boolean;
  status?: string;
}

export interface ClusterStatus {
  // Aceptamos tanto una lista plana de nodos como el dict del cluster.
  nodes?: ClusterNode[];
  peers?: ClusterNode[];
  local_node?: ClusterNode;
  subleader_id?: string | number;
  epoch?: number;
  last_applied_lsn?: number;
  read_only?: boolean;
  [key: string]: unknown;
}

export const clusterService = {
  getStatus: async (): Promise<ClusterStatus> => {
    const res = await fetch(`${API_URL}/cluster/status`, {
      method: "GET",
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("No se pudo obtener el estado del clúster");
    return res.json();
  },
};
