import React, { useCallback, useEffect, useState } from "react";
import { postService } from "../services/PostServices";
import { followServices } from "../services/FollowsServices";
import { presenceService } from "../services/PresenceService";
import { getUser } from "../utils/utils";
import { Post, User } from "../types/feed.types";
import FriendsBubbles from "./FriendsBubbles";
import PostCard from "./PostCard";
import LastPostModal from "./LastPostModal";

const PRESENCE_REFRESH_MS = 15000;

const Feed: React.FC = () => {
  const [posts, setPosts] = useState<Post[]>([]);
  const [friends, setFriends] = useState<User[]>([]);
  const [onlineIds, setOnlineIds] = useState<number[]>([]);
  const [newPostContent, setNewPostContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [publishing, setPublishing] = useState(false);
  const [selectedFriend, setSelectedFriend] = useState<User | null>(null);

  const currentUserId = Number(getUser().id);

  // Carga del feed + seguidos (reutilizable tras publicar/eliminar).
  const fetchFeed = useCallback(async () => {
    try {
      const [fetchedPosts, fetchedFriends] = await Promise.all([
        postService.getFeed().catch(() => []),
        followServices.getFollowed().catch(() => []),
      ]);
      setPosts(fetchedPosts);
      setFriends(fetchedFriends);
    } catch (error) {
      console.error("Error en la red overlay:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Presencia: refresco periódico para pintar el estado de los seguidos.
  const refreshPresence = useCallback(async () => {
    const ids = await presenceService.getOnline();
    setOnlineIds(ids);
  }, []);

  useEffect(() => {
    fetchFeed();
  }, [fetchFeed]);

  useEffect(() => {
    refreshPresence();
    const interval = setInterval(refreshPresence, PRESENCE_REFRESH_MS);
    return () => clearInterval(interval);
  }, [refreshPresence]);

  const handlePublish = async () => {
    if (!newPostContent.trim()) return;
    try {
      setPublishing(true);
      await postService.createPost(newPostContent);
      setNewPostContent("");
      await fetchFeed(); // Refresco inmediato: el post aparece sin recargar
    } catch (error: unknown) {
      alert("Error publicando: " + (error as Error).message);
    } finally {
      setPublishing(false);
    }
  };

  const handleDelete = async (postId: number) => {
    if (!confirm("¿Eliminar este post?")) return;
    try {
      await postService.deletePost(postId);
      await fetchFeed();
    } catch (error: unknown) {
      alert("Error eliminando: " + (error as Error).message);
    }
  };

  // Repostear: solo se ofrece sobre posts de OTROS usuarios (ver PostCard).
  // Crea un nuevo post con el mismo contenido a nombre del usuario actual.
  const handleRepost = async (content: string) => {
    try {
      await postService.createPost(content);
      await fetchFeed();
    } catch (error: unknown) {
      alert("Error reposteando: " + (error as Error).message);
    }
  };

  return (
    <div className="bg-dark text-white min-vh-100 pb-5">
      <main className="container py-3" style={{ maxWidth: "600px" }}>
        <FriendsBubbles
          friends={friends}
          onlineIds={onlineIds}
          onSelect={setSelectedFriend}
        />

        {/* --- Crear Post --- */}
        <div className="card bg-black border-secondary mb-4">
          <div className="card-body">
            <textarea
              className="form-control bg-transparent border-0 text-white shadow-none"
              placeholder="¿Qué está pasando en la red?"
              rows={2}
              value={newPostContent}
              onChange={(e) => setNewPostContent(e.target.value)}
            ></textarea>
            <div className="d-flex justify-content-end mt-3 pt-2 border-top border-secondary">
              <button
                className="btn btn-primary rounded-pill px-4 fw-bold"
                onClick={handlePublish}
                disabled={publishing || !newPostContent.trim()}
              >
                {publishing ? "Publicando..." : "Post"}
              </button>
            </div>
          </div>
        </div>

        {/* --- Stream del Feed --- */}
        {loading ? (
          <div className="text-center py-5">
            <div className="spinner-border text-primary"></div>
          </div>
        ) : posts.length === 0 ? (
          <div className="text-center text-muted py-5">
            Aún no hay posts. ¡Publica el primero!
          </div>
        ) : (
          <div className="d-flex flex-column gap-3">
            {posts.map((post) => (
              <PostCard
                key={post.id}
                post={post}
                isOwner={Number(post.user_id) === currentUserId}
                onDelete={handleDelete}
                onRepost={handleRepost}
              />
            ))}
          </div>
        )}
      </main>

      {selectedFriend && (
        <LastPostModal
          friend={selectedFriend}
          onClose={() => setSelectedFriend(null)}
        />
      )}
    </div>
  );
};

export default Feed;
