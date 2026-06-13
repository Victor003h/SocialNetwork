import React, { useEffect, useState } from "react";
import { User, Post } from "../types/feed.types";
import { postService } from "../services/PostServices";

interface LastPostModalProps {
  friend: User;
  onClose: () => void;
}

// Ventana emergente con el último post del usuario seleccionado (solo lectura).
const LastPostModal: React.FC<LastPostModalProps> = ({ friend, onClose }) => {
  const [lastPost, setLastPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        setLoading(true);
        setError(false);
        const posts = await postService.getUserPostsById(friend.id);
        if (!active) return;
        // El más reciente por created_at
        const sorted = [...posts].sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
        );
        setLastPost(sorted[0] ?? null);
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
  }, [friend.id]);

  return (
    <div
      className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
      style={{ background: "rgba(0,0,0,0.6)", zIndex: 1060 }}
      onClick={onClose}
    >
      <div
        className="card bg-dark text-white border-secondary shadow-lg"
        style={{ width: "90%", maxWidth: "420px" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="card-header d-flex justify-content-between align-items-center border-secondary">
          <span className="fw-bold">@{friend.username}</span>
          <button
            className="btn btn-sm btn-link text-light p-0"
            onClick={onClose}
          >
            <i className="bi bi-x-lg"></i>
          </button>
        </div>
        <div className="card-body">
          {loading && (
            <div className="text-center py-3">
              <div className="spinner-border spinner-border-sm text-primary"></div>
            </div>
          )}
          {!loading && error && (
            <p className="text-danger mb-0">No se pudo cargar el último post.</p>
          )}
          {!loading && !error && !lastPost && (
            <p className="text-muted mb-0">Este usuario aún no tiene posts.</p>
          )}
          {!loading && !error && lastPost && (
            <>
              <p className="text-light mb-2">{lastPost.content}</p>
              <small className="text-muted">
                {new Date(lastPost.created_at).toLocaleString()}
              </small>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default LastPostModal;
