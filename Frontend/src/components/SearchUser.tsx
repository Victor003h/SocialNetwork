import React, { useState, useEffect, useCallback, useMemo } from "react";
import { followServices } from "../services/FollowsServices";
import { userService } from "../services/UserServices";
import { User } from "../types/feed.types";

const SearchUser: React.FC = () => {
  const [allUsers, setAllUsers] = useState<User[]>([]);
  const [followedUsers, setFollowedUsers] = useState<User[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);

  // Carga coordinada desde el Clúster
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      // Ejecución concurrente para optimizar latencia de red
      const [usersData, followedData] = await Promise.all([
        userService.getAllUsers(),
        followServices.getFollowed(),
      ]);

      setAllUsers(usersData);
      setFollowedUsers(followedData);
    } catch (error) {
      console.error("Error en la sincronización con los nodos:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Lógica de filtrado y partición de conjuntos
  const { following, notFollowing } = useMemo(() => {
    const followedIds = new Set(followedUsers.map((u) => u.id));

    const filtered = allUsers.filter((u) =>
      u.username.toLowerCase().includes(searchTerm.toLowerCase()),
    );

    return {
      following: filtered.filter((u) => followedIds.has(u.id)),
      notFollowing: filtered.filter((u) => !followedIds.has(u.id)),
    };
  }, [allUsers, followedUsers, searchTerm]);

  // Handlers de mutación
  const handleFollow = async (user_id: number) => {
    try {
      await followServices.followUser(user_id);
      await loadData(); // Re-sincronización tras mutación
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
    } catch (error) {
      alert("Fallo en el consenso del nodo al seguir.");
    }
  };

  const handleUnfollow = async (user_id: number) => {
    try {
      await followServices.deletefollow(user_id);
      await loadData(); // Re-sincronización tras mutación
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
    } catch (error) {
      alert("Error al eliminar la relación en el clúster.");
    }
  };

  const renderUserItem = (user: User, isFollowed: boolean) => (
    <div
      key={user.id}
      className="d-flex align-items-center justify-content-between p-3 border-bottom border-secondary"
    >
      <div className="d-flex align-items-center gap-3">
        <img
          src={`https://ui-avatars.com/api/?name=${user.username}&background=random`}
          className="rounded-circle"
          width="40"
          alt="Avatar"
        />
        <div>
          <div className="fw-bold">@{user.username}</div>
          <small className="text-muted" style={{ fontSize: "0.75rem" }}>
            NODE_ID: {user.id}
          </small>
        </div>
      </div>
      {isFollowed ? (
        <button
          className="btn btn-sm btn-danger rounded-pill px-3"
          onClick={() => handleUnfollow(user.id)}
        >
          Unfollow
        </button>
      ) : (
        <button
          className="btn btn-sm btn-primary rounded-pill px-3"
          onClick={() => handleFollow(user.id)}
        >
          Follow
        </button>
      )}
    </div>
  );

  return (
    <div className="search-container bg-dark text-white rounded shadow-lg">
      <header className="p-3 border-bottom border-secondary bg-black d-flex gap-2">
        <input
          type="text"
          className="form-control bg-dark text-white border-secondary rounded-pill"
          placeholder="Buscar en el clúster..."
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <button
          className="btn btn-outline-secondary"
          onClick={loadData}
          disabled={loading}
        >
          {loading ? "..." : "↺"}
        </button>
      </header>

      <div className="overflow-auto" style={{ maxHeight: "500px" }}>
        {/* Sección: Siguiendo */}
        {following.length > 0 && (
          <div className="p-2 bg-black text-uppercase small text-muted">
            Siguiendo
          </div>
        )}
        {following.map((u) => renderUserItem(u, true))}

        {/* Sección: Sugeridos / No seguidos */}
        {notFollowing.length > 0 && (
          <div className="p-2 bg-black text-uppercase small text-muted mt-2">
            Sugeridos para ti
          </div>
        )}
        {notFollowing.map((u) => renderUserItem(u, false))}

        {!loading && allUsers.length === 0 && (
          <div className="p-5 text-center text-muted">
            Sin nodos detectados.
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchUser;
