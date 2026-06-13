import React from "react";
import { Post } from "../types/feed.types";

interface PostCardProps {
  post: Post;
  isOwner: boolean;
  onDelete: (postId: number) => void;
  onRepost: (content: string) => void;
}

const formatDate = (iso: string) => {
  const d = new Date(iso);
  return isNaN(d.getTime()) ? "" : d.toLocaleString();
};

const PostCard: React.FC<PostCardProps> = ({
  post,
  isOwner,
  onDelete,
  onRepost,
}) => {
  const displayName = post.UserName || `user_${post.user_id}`;
  const handle = displayName.split(" ")[0].toLowerCase();

  return (
    <article className="card bg-black border-secondary mb-3">
      <div className="card-body">
        <div className="d-flex justify-content-between align-items-start">
          <div>
            <span className="fw-bold me-2">{displayName}</span>
            <span className="text-muted small">@{handle}</span>
            <span className="text-muted small mx-1">·</span>
            <span className="text-muted small">
              {formatDate(post.created_at)}
            </span>
          </div>
        </div>

        <p className="mt-2 text-light">{post.content}</p>

        {/* Barra de acciones: repostear posts ajenos / eliminar los propios */}
        <div className="d-flex justify-content-end gap-2 pt-2 border-top border-secondary">
          {isOwner ? (
            <button
              className="btn btn-sm btn-outline-danger rounded-pill px-3"
              onClick={() => onDelete(post.id)}
            >
              <i className="bi bi-trash me-1"></i>Eliminar
            </button>
          ) : (
            <button
              className="btn btn-sm btn-outline-primary rounded-pill px-3"
              onClick={() => onRepost(post.content)}
            >
              <i className="bi bi-arrow-repeat me-1"></i>Repostear
            </button>
          )}
        </div>
      </div>
    </article>
  );
};

export default PostCard;
