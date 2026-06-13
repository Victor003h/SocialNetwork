import React, { useEffect, useState } from "react";
import { User } from "../types/feed.types";
import { followServices } from "../services/FollowsServices";

interface FollowersListModalProps {
  onClose: () => void;
}

// Lista de usuarios que te siguen (solo lectura, sin acciones).
const FollowersListModal: React.FC<FollowersListModalProps> = ({ onClose }) => {
  const [followers, setFollowers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        setLoading(true);
        setError(false);
        const data = await followServices.getFollowers();
        if (active) setFollowers(data);
      } catch {
        if (active) setError(true);
      } finally {
        if (active) setLoading(false);
      }
    };
    load();
    return () => {
      active = false;
    };
  }, []);

  return (
    <div
      className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
      style={{ background: "rgba(0,0,0,0.6)", zIndex: 1060 }}
      onClick={onClose}
    >
      <div
        className="card bg-dark text-white border-secondary shadow-lg"
        style={{ width: "90%", maxWidth: "480px", maxHeight: "80vh" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="card-header d-flex justify-content-between align-items-center border-secondary">
          <span className="fw-bold">Me siguen</span>
          <button
            className="btn btn-sm btn-link text-light p-0"
            onClick={onClose}
          >
            <i className="bi bi-x-lg"></i>
          </button>
        </div>
        <div className="card-body overflow-auto">
          {loading && (
            <div className="text-center py-3">
              <div className="spinner-border spinner-border-sm text-primary"></div>
            </div>
          )}
          {!loading && error && (
            <p className="text-danger mb-0">
              No se pudieron cargar los seguidores.
            </p>
          )}
          {!loading && !error && followers.length === 0 && (
            <p className="text-muted mb-0">Aún no tienes seguidores.</p>
          )}
          {!loading &&
            !error &&
            followers.map((user) => (
              <div
                key={user.id}
                className="d-flex align-items-center gap-3 border-bottom border-secondary py-2"
              >
                <img
                  src={`https://ui-avatars.com/api/?name=${user.username}&background=random`}
                  className="rounded-circle"
                  width="36"
                  alt={user.username}
                />
                <span className="fw-bold">@{user.username}</span>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};

export default FollowersListModal;
