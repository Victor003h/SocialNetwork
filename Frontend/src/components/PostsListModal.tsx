import React, { useEffect, useState } from "react";
import { Post } from "../types/feed.types";
import { postService } from "../services/PostServices";

interface PostsListModalProps {
  userId: number;
  onClose: () => void;
}

// Lista de posts del usuario (solo lectura).
const PostsListModal: React.FC<PostsListModalProps> = ({ userId, onClose }) => {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        setLoading(true);
        setError(false);
        const data = await postService.getUserPostsById(userId);
        if (active) setPosts(data);
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
  }, [userId]);

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
          <span className="fw-bold">Mis posts</span>
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
            <p className="text-danger mb-0">No se pudieron cargar los posts.</p>
          )}
          {!loading && !error && posts.length === 0 && (
            <p className="text-muted mb-0">Sin posts todavía.</p>
          )}
          {!loading &&
            !error &&
            posts.map((post) => (
              <div
                key={post.id}
                className="border-bottom border-secondary py-2"
              >
                <p className="text-light mb-1">{post.content}</p>
                <small className="text-muted">
                  {new Date(post.created_at).toLocaleString()}
                </small>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};

export default PostsListModal;
