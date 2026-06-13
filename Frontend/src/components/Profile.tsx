import React, { useState, useEffect } from "react";
import { profileService } from "../services/ProfileService";
import { UserProfile, ProfileUpdateData } from "../types/profile.types";
import PostsListModal from "./PostsListModal";
import FollowersListModal from "./FollowersListModal";

interface ProfileSectionProps {
  onLogout: () => void;
}

const ProfileSection: React.FC<ProfileSectionProps> = ({ onLogout }) => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showPosts, setShowPosts] = useState(false);
  const [showFollowers, setShowFollowers] = useState(false);

  // Estado para el formulario de edición
  const [editData, setEditData] = useState({
    username: "",
    password: "", // Se deja vacío por seguridad
  });

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const data = await profileService.getMyProfile();
      setProfile(data);
      console.log(data);

      setEditData({ username: data.username, password: "" });
    } catch (error) {
      console.error("Error cargando perfil distribuido:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!profile) return;
    try {
      setLoading(true);
      // Solo enviamos el password si el usuario escribió algo
      const payload: ProfileUpdateData = {
        id: profile.id, // Aseguramos enviar el ID para identificar el nodo
        username: editData.username,
        password: String(editData.password),
      };
      if (editData.password) payload.password = editData.password;

      await profileService.updateProfile(payload);

      setIsEditing(false);
      await loadProfile(); // Recargamos para ver cambios reflejados por el clúster
      alert("Perfil actualizado correctamente en todos los nodos.");
    } catch (error: unknown) {
      if (error instanceof Error) {
        alert("Error: " + error.message);
      } else {
        alert("Error desconocido");
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading && !profile)
    return <div className="text-white">Sincronizando con el clúster...</div>;

  return (
    <div className="card bg-dark text-white p-4 border-secondary">
      <div className="d-flex align-items-center gap-4 mb-4">
        <img
          src={`https://ui-avatars.com/api/?name=${profile?.username}&background=random`}
          className="rounded-circle border border-primary"
          width="80"
          alt="Avatar"
        />
        <div>
          <h3 className="mb-0">@{profile?.username}</h3>
          <small className="text-muted">ID de Nodo: {profile?.id}</small>
        </div>
      </div>

      <hr className="border-secondary" />

      {isEditing ? (
        <div className="edit-form">
          <div className="mb-3">
            <label className="form-label">Nuevo Username</label>
            <input
              type="text"
              className="form-control bg-secondary text-white border-0"
              value={editData.username}
              onChange={(e) =>
                setEditData({ ...editData, username: e.target.value })
              }
            />
          </div>
          <div className="mb-3">
            <label className="form-label">
              Nueva Contraseña (dejar en blanco para no cambiar)
            </label>
            <input
              type="password"
              className="form-control bg-secondary text-white border-0"
              value={editData.password}
              onChange={(e) =>
                setEditData({ ...editData, password: e.target.value })
              }
            />
          </div>
          <div className="d-flex gap-2">
            <button
              className="btn btn-primary"
              onClick={handleSave}
              disabled={loading}
            >
              {loading ? "Sincronizando..." : "Confirmar Cambios"}
            </button>
            <button
              className="btn btn-outline-light"
              onClick={() => setIsEditing(false)}
            >
              Cancelar
            </button>
          </div>
        </div>
      ) : (
        <div className="view-mode">
          <div className="stats-row d-flex justify-content-around py-3 bg-black rounded mb-4">
            <button
              className="text-center btn btn-link text-white text-decoration-none"
              onClick={() => setShowPosts(true)}
            >
              <h4 className="fw-bold mb-0">{profile?.postCount}</h4>
              <small className="text-muted">POSTS</small>
            </button>
            <button
              className="text-center btn btn-link text-white text-decoration-none"
              onClick={() => setShowFollowers(true)}
            >
              <h4 className="fw-bold mb-0">{profile?.followerCount}</h4>
              <small className="text-muted">SEGUIDORES</small>
            </button>
          </div>
          <button
            className="btn btn-outline-primary w-100 mb-2"
            onClick={() => setIsEditing(true)}
          >
            Configuración de Cuenta
          </button>
          <button className="btn btn-outline-danger w-100" onClick={onLogout}>
            <i className="bi bi-box-arrow-right me-2"></i>Cerrar sesión
          </button>
        </div>
      )}

      {showPosts && profile && (
        <PostsListModal
          userId={profile.id}
          onClose={() => setShowPosts(false)}
        />
      )}
      {showFollowers && (
        <FollowersListModal onClose={() => setShowFollowers(false)} />
      )}
    </div>
  );
};

export default ProfileSection;
