import React, { useEffect, useState } from "react";
import { postService } from "../services/PostServices";
import { Post, User } from "../types/feed.types";
import { followServices } from "../services/FollowsServices";
const Feed: React.FC = () => {
  const [posts, setPosts] = useState<Post[]>([]);
  const [friends, setFriends] = useState<User[]>([]);
  const [newPostContent, setNewPostContent] = useState("");
  const [loading, setLoading] = useState(true);

  // Carga inicial de datos
  useEffect(() => {
    const loadData = async () => {
      try {
        // En sistemas distribuidos, hacemos las cargas en paralelo para ganar velocidad
        const [fetchedPosts, fetchedFriends] = await Promise.all([
          // Nota: Si el backend no responde aún, puedes comentar estas líneas y usar datos falsos para probar la UI
          postService.getFeed().catch(() => []),
          followServices.getFollowed().catch(() => []),
        ]);

        // --- MOCK DATA TEMPORAL (Para que veas la UI mientras configuras el backend) ---
        // Si fetchedPosts viene vacío, usamos estos datos de prueba basados en tu imagen:
        if (fetchedPosts.length === 0) {
          setPosts([
            {
              id: "1",
              userId: "u1",
              UserName: "Satoshi Nakamoto",
              content:
                "The block synchronization latency between Tokyo and London has dropped significantly.",
              created: "2015/05/12",
              //comments: 12,
            },
            {
              id: "2",
              userId: "u2",
              UserName: "Elena Wright",
              content:
                "Testing out the new geographic scalability protocols. Shard hopping is working perfectly!",
              created: "2015/05/12",
              //likes: 88,
              //comments: 4,
            },
          ]);
          setFriends([
            {
              id: 1,
              username: "Satoshi",
              followers: 100,
              posts: 6,
              avatarUrl: "https://i.pravatar.cc/150?u=satoshi",
            },
            {
              id: 3,
              username: "Elena",
              followers: 100,
              posts: 6,
              avatarUrl: "https://i.pravatar.cc/150?u=elena",
            },
            {
              id: 5,
              username: "Marco",
              followers: 100,
              posts: 6,
              avatarUrl: "https://i.pravatar.cc/150?u=marco",
            },
          ]);
        } else {
          setPosts(fetchedPosts);
          setFriends(fetchedFriends);
        }
        // -------------------------------------------------------------------------------
      } catch (error) {
        console.error("Error en la red overlay:", error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const handlePublish = async () => {
    console.log("entro");
    if (!newPostContent.trim()) return;
    try {
      console.log(newPostContent);
      // Optimistic UI: Agregamos el post localmente antes de confirmar (opcional)

      await postService.createPost(newPostContent);
      alert("Post enviado a la cola de replicación");
      setNewPostContent("");
      // Recargar feed...
    } catch (error: unknown) {
      alert("Error publicando: " + (error as Error).message);
    }
  };

  const handleReply = async (content: string) => {
    try {
      // Optimistic UI: Agregamos el post localmente antes de confirmar (opcional)

      await postService.createPost(content);
      alert("Post enviado a la cola de replicación");
      setNewPostContent("");
      // Recargar feed...
    } catch (error: unknown) {
      alert("Error publicando: " + (error as Error).message);
    }
  };

  return (
    <div className="bg-dark text-white min-vh-100 pb-5">
      {/* --- Top Header (Search) --- */}

      <main className="container py-3" style={{ maxWidth: "600px" }}>
        {/* --- Connected Friends (Horizontal Scroll) --- */}
        <section className="mb-4">
          <div className="d-flex justify-content-between align-items-center mb-2">
            <small className="text-muted fw-bold">CONNECTED NODES</small>
            <small
              className="text-primary fw-bold"
              style={{ cursor: "pointer" }}
            >
              View All
            </small>
          </div>
          <div
            className="d-flex gap-3 overflow-auto pb-2"
            style={{ scrollbarWidth: "none" }}
          >
            {/* Botón "Find" */}
            <div className="text-center">
              <div
                className="btn btn-outline-secondary rounded-circle d-flex align-items-center justify-content-center mx-auto"
                style={{ width: 50, height: 50 }}
              >
                <i className="bi bi-plus-lg"></i>
              </div>
              <small
                className="d-block mt-1 text-muted"
                style={{ fontSize: "10px" }}
              >
                Find
              </small>
            </div>
            {/* Lista de Amigos */}
            {friends.map((friend) => (
              <div key={friend.username} className="text-center">
                <div
                  className="rounded-circle p-1 border border-primary mx-auto"
                  style={{ width: 54, height: 54 }}
                >
                  <img
                    src={friend.avatarUrl}
                    className="rounded-circle w-100 h-100"
                    alt={friend.username}
                  />
                </div>
                <small
                  className="d-block mt-1 text-white"
                  style={{ fontSize: "10px" }}
                >
                  {friend.username}
                </small>
              </div>
            ))}
          </div>
        </section>

        {/* --- Create Post Widget --- */}
        <div className="card bg-black border-secondary mb-4">
          <div className="card-body">
            <div className="d-flex gap-3">
              <div
                className="rounded-circle bg-secondary flex-shrink-0"
                style={{
                  width: 40,
                  height: 40,
                  backgroundImage: "url(https://i.pravatar.cc/300)",
                  backgroundSize: "cover",
                }}
              ></div>
              <div className="w-100">
                <textarea
                  className="form-control bg-transparent border-0 text-white shadow-none"
                  placeholder="What's happening on the network?"
                  rows={2}
                  value={newPostContent}
                  onChange={(e) => setNewPostContent(e.target.value)}
                ></textarea>
              </div>
            </div>
            <div className="d-flex justify-content-between align-items-center mt-3 pt-2 border-top border-secondary">
              <div className="text-primary h5 mb-0">
                <i className="bi bi-image me-3" role="button"></i>
                <i className="bi bi-filetype-gif me-3" role="button"></i>
                <i className="bi bi-emoji-smile" role="button"></i>
              </div>
              <button
                className="btn btn-primary rounded-pill px-4 fw-bold"
                onClick={handlePublish}
              >
                Post
              </button>
            </div>
          </div>
        </div>

        {/* --- Feed Stream --- */}
        {loading ? (
          <div className="text-center py-5">
            <div className="spinner-border text-primary"></div>
          </div>
        ) : (
          <div className="d-flex flex-col gap-3">
            {posts.map((post) => (
              <article
                key={post.id}
                className="card bg-black border-secondary mb-3"
              >
                <div className="card-body d-flex gap-3">
                  <div className="w-100">
                    <div className="d-flex justify-content-between align-items-start">
                      <div>
                        <span className="fw-bold me-2">{post.UserName}</span>
                        <span className="text-muted small">
                          @{post.UserName.split(" ")[0].toLowerCase()}
                        </span>
                        <span className="text-muted small mx-1">·</span>
                        <span className="text-muted small">{post.created}</span>
                      </div>
                      <i className="bi bi-three-dots text-muted"></i>
                    </div>
                    <p className="mt-2 text-light">{post.content}</p>

                    {/* Action Bar */}
                    <div
                      className="d-flex justify-content-between mt-3 text-muted"
                      style={{ maxWidth: "300px" }}
                    >
                      <button
                        className="btn btn-primary rounded-pill px-4 fw-bold"
                        onClick={() => handleReply(post.content)}
                      >
                        Reply
                      </button>
                      <span className="d-flex align-items-center gap-1">
                        <i className="bi bi-heart"></i> <small>{100}</small>
                      </span>
                      <i className="bi bi-share"></i>
                    </div>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default Feed;
