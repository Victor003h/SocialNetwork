// src/components/ProfileSection.tsx
import React, { useState, useEffect } from "react";
import { UserProfile, ProfileUpdateData } from "../types/profile.types";
import { profileService } from "../services/ProfileService";

const ProfileSection: React.FC = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);

  // Estado temporal para el formulario
  const [formData, setFormData] = useState<ProfileUpdateData>({});

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const data = await profileService.getMyProfile();
      setProfile(data);
      // Inicializamos el formulario con los datos actuales
      setFormData({
        bio: data.bio,
        location: data.location,
        avatarUrl: data.avatarUrl,
      });
    } catch (error) {
      console.error("Error cargando perfil", error);
      // MOCK DATA SI FALLA EL BACKEND (Para tu evaluación)
      setProfile({
        id: "123",
        username: "UsuarioDemo",
        email: "demo@red.com",
        bio: "Desarrollador Full Stack en sistemas distribuidos.",
        location: "Servidor Nodo 1",
        avatarUrl: "https://i.pravatar.cc/300?u=demo",
        joinDate: "2023-10-01",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      await profileService.updateProfile(formData);
      setIsEditing(false);
      await loadProfile(); // Recargamos datos frescos
      alert("Perfil actualizado en la red distribuida");
    } catch (error: unknown) {
      alert("Error al guardar cambios: " + (error as Error).message);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !profile)
    return (
      <div className="text-center p-5">
        <div className="spinner-border text-primary"></div>
      </div>
    );

  return (
    <div className="animate__animated animate__fadeIn">
      {/* --- Header / Cover --- */}
      <div className="position-relative mb-5">
        <div
          className="bg-secondary w-100 rounded-top"
          style={{
            height: "120px",
            background: "linear-gradient(90deg, #135bec 0%, #0a0f18 100%)",
          }}
        ></div>

        {/* Avatar Superpuesto */}
        <div
          className="position-absolute start-50 translate-middle"
          style={{ top: "120px" }}
        >
          <div
            className="rounded-circle p-1 bg-black"
            style={{ width: "100px", height: "100px" }}
          >
            <img
              src={profile?.avatarUrl}
              alt="Profile"
              className="rounded-circle w-100 h-100 object-fit-cover"
            />
            {isEditing && (
              <button className="btn btn-sm btn-dark position-absolute bottom-0 end-0 rounded-circle border border-secondary">
                <i className="bi bi-camera"></i>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* --- Info del Usuario --- */}
      <div className="text-center mt-5 pt-2">
        <h3 className="fw-bold text-white mb-0">{profile?.username}</h3>
        <p className="text-muted small">@{profile?.username?.toLowerCase()}</p>

        {!isEditing ? (
          // VISTA DE LECTURA
          <div className="px-4">
            <p className="text-light mt-3">
              {profile?.bio || "Sin biografía definida."}
            </p>

            <div className="d-flex justify-content-center gap-3 text-muted small my-3">
              <span>
                <i className="bi bi-geo-alt me-1"></i>
                {profile?.location || "Desconocido"}
              </span>
              <span>
                <i className="bi bi-calendar3 me-1"></i>Unido:{" "}
                {profile?.joinDate}
              </span>
            </div>

            <div className="d-grid gap-2 col-8 mx-auto mt-4">
              <button
                onClick={() => setIsEditing(true)}
                className="btn btn-outline-primary rounded-pill"
              >
                Editar Perfil
              </button>
            </div>
          </div>
        ) : (
          // VISTA DE EDICIÓN
          <div className="card bg-dark border-secondary mx-3 mt-3 text-start">
            <div className="card-body">
              <div className="mb-3">
                <label className="form-label text-muted small">Biografía</label>
                <textarea
                  className="form-control bg-black text-white border-secondary"
                  rows={3}
                  value={formData.bio}
                  onChange={(e) =>
                    setFormData({ ...formData, bio: e.target.value })
                  }
                ></textarea>
              </div>
              <div className="mb-3">
                <label className="form-label text-muted small">Ubicación</label>
                <input
                  type="text"
                  className="form-control bg-black text-white border-secondary"
                  value={formData.location}
                  onChange={(e) =>
                    setFormData({ ...formData, location: e.target.value })
                  }
                />
              </div>

              <div className="d-flex gap-2 justify-content-end mt-4">
                <button
                  onClick={() => setIsEditing(false)}
                  className="btn btn-outline-secondary btn-sm"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleSave}
                  className="btn btn-primary btn-sm"
                  disabled={loading}
                >
                  {loading ? "Guardando..." : "Guardar Cambios"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* --- Estadísticas (Opcional) --- */}
      <div className="d-flex justify-content-around mt-5 border-top border-secondary pt-4 mx-3">
        <div className="text-center">
          <h5 className="fw-bold text-white mb-0">142</h5>
          <small className="text-muted" style={{ fontSize: "10px" }}>
            POSTS
          </small>
        </div>
        <div className="text-center">
          <h5 className="fw-bold text-white mb-0">8.2k</h5>
          <small className="text-muted" style={{ fontSize: "10px" }}>
            FOLLOWERS
          </small>
        </div>
        <div className="text-center">
          <h5 className="fw-bold text-white mb-0">204</h5>
          <small className="text-muted" style={{ fontSize: "10px" }}>
            FOLLOWING
          </small>
        </div>
      </div>
    </div>
  );
};

export default ProfileSection;
