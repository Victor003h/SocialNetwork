import React, { useCallback, useEffect, useState } from "react";
import {
  clusterService,
  ClusterNode,
  ClusterStatus,
} from "../services/ClusterService";

const STATUS_REFRESH_MS = 3000;

const roleBadge = (role?: string) => {
  switch (role) {
    case "leader":
      return "bg-warning text-dark";
    case "subleader":
      return "bg-info text-dark";
    case "follower":
      return "bg-secondary";
    default:
      return "bg-dark border border-secondary";
  }
};

const collectNodes = (status: ClusterStatus): ClusterNode[] => {
  if (Array.isArray(status.nodes)) return status.nodes;
  const nodes: ClusterNode[] = [];
  if (status.local_node) nodes.push(status.local_node);
  if (Array.isArray(status.peers)) nodes.push(...status.peers);
  return nodes;
};

const AdminPanel: React.FC = () => {
  const [status, setStatus] = useState<ClusterStatus | null>(null);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(true);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await clusterService.getStatus();
      setStatus(data);
      setError("");
    } catch (e) {
      setError((e as Error).message || "Clúster no disponible");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, STATUS_REFRESH_MS);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const nodes = status ? collectNodes(status) : [];

  return (
    <div className="bg-dark text-white min-vh-100">
      <main className="container py-4" style={{ maxWidth: "720px" }}>
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h4 className="mb-0">
            <i className="bi bi-hdd-stack me-2"></i>Estado del Clúster
          </h4>
          <span className="badge bg-success">
            <span className="spinner-grow spinner-grow-sm me-1"></span>en vivo
          </span>
        </div>

        {loading && !status && (
          <div className="text-center py-5">
            <div className="spinner-border text-primary"></div>
          </div>
        )}

        {error && (
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
        )}

        {status && (
          <>
            <div className="row g-2 mb-4">
              <div className="col">
                <div className="card bg-black border-secondary text-center p-2">
                  <small className="text-muted">SUBLEADER</small>
                  <span className="fw-bold">
                    {String(status.subleader_id ?? "—")}
                  </span>
                </div>
              </div>
              <div className="col">
                <div className="card bg-black border-secondary text-center p-2">
                  <small className="text-muted">EPOCH</small>
                  <span className="fw-bold">
                    {String((status.epoch as number) ?? "—")}
                  </span>
                </div>
              </div>
              <div className="col">
                <div className="card bg-black border-secondary text-center p-2">
                  <small className="text-muted">READ ONLY</small>
                  <span className="fw-bold">
                    {status.read_only ? "Sí" : "No"}
                  </span>
                </div>
              </div>
            </div>

            <table className="table table-dark table-bordered align-middle">
              <thead>
                <tr>
                  <th>Nodo</th>
                  <th>Rol</th>
                  <th>Estado</th>
                  <th>Dirección</th>
                </tr>
              </thead>
              <tbody>
                {nodes.map((node, idx) => {
                  const alive = (node as { alive?: boolean }).alive;
                  return (
                    <tr key={`${node.node_id}-${idx}`}>
                      <td className="fw-bold">{String(node.node_id ?? "?")}</td>
                      <td>
                        <span className={`badge ${roleBadge(node.role)}`}>
                          {node.role ?? "unknown"}
                        </span>
                      </td>
                      <td>
                        <span
                          className={`badge ${
                            alive === false ? "bg-danger" : "bg-success"
                          }`}
                        >
                          {alive === false ? "DOWN" : "UP"}
                        </span>
                      </td>
                      <td className="small text-muted">
                        {node.address || node.ip || "—"}
                      </td>
                    </tr>
                  );
                })}
                {nodes.length === 0 && (
                  <tr>
                    <td colSpan={4} className="text-center text-muted">
                      Sin nodos reportados.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>

            <p className="text-muted small">
              Corre <code>make kill-node N=2</code> o{" "}
              <code>make add-node</code> en la terminal y observa cómo cambia
              esta tabla (failover y re-elección de subleader).
            </p>
          </>
        )}
      </main>
    </div>
  );
};

export default AdminPanel;
