// src/pages/AuthPage.tsx
import React, { useState } from "react";
import { authService } from "../services/AuthService";

const AuthPage: React.FC<{ onAuthChange: () => void }> = ({ onAuthChange }) => {
  const [activeTab, setActiveTab] = useState<"login" | "register">("login");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>("");

  // Estado único para ambos formularios
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      if (activeTab === "login") {
        await authService.login({
          username: formData.username,
          password: formData.password,
        });
        alert("¡Conexión exitosa al Gateway!");
        onAuthChange();
        // Aquí harías: window.location.href = '/feed';
      } else {
        const registerResult = await authService.register(formData);
        if (registerResult == 200) {
          alert(
            "Usuario registrado en el sistema distribuido. Ahora inicia sesión.",
          );
          setActiveTab("login");
        } else {
          setError(
            "Error al registrar el usuario servidor respondió con código: " +
              registerResult,
          );
        }
      }
    } catch (err: unknown) {
      setError((err as Error).message || "Error desconocido");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container d-flex flex-col justify-content-center align-items-center min-vh-100 bg-light">
      {/* --- Header decorativo --- */}
      <div className="text-center mb-4">
        <h1 className="h3 mb-3 fw-normal">Auth Gateway</h1>
        <div className="badge bg-success text-wrap p-2">Docker Mesh Active</div>
      </div>

      <div
        className="card shadow-lg"
        style={{ width: "100%", maxWidth: "400px", borderRadius: "15px" }}
      >
        {}
        <div
          className="card-img-top bg-dark text-white p-4 text-center"
          style={{
            borderTopLeftRadius: "15px",
            borderTopRightRadius: "15px",
            background: "linear-gradient(45deg, #135bec, #0a0f18)",
          }}
        >
          <i
            className="bi bi-shield-lock-fill"
            style={{ fontSize: "2rem" }}
          ></i>
          <div className="small mt-2 font-monospace">JWT_AUTH_PROTOCOL_V2</div>
        </div>

        <div className="card-body p-4">
          {/* --- Tabs de Bootstrap --- */}
          <ul
            className="nav nav-pills nav-fill mb-4"
            id="pills-tab"
            role="tablist"
          >
            <li className="nav-item" role="presentation">
              <button
                className={`nav-link ${activeTab === "login" ? "active" : ""}`}
                onClick={() => setActiveTab("login")}
              >
                Login
              </button>
            </li>
            <li className="nav-item" role="presentation">
              <button
                className={`nav-link ${activeTab === "register" ? "active" : ""}`}
                onClick={() => setActiveTab("register")}
              >
                Register
              </button>
            </li>
          </ul>

          {/* --- Alerta de Error --- */}
          {error && (
            <div className="alert alert-danger text-center" role="alert">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {/* Campo Username (Común para ambos) */}
            <div className="mb-3">
              <label className="form-label fw-bold small text-muted">
                USERNAME
              </label>
              <input
                type="text"
                name="username"
                className="form-control form-control-lg"
                placeholder="Ej. usuario_nodo1"
                value={formData.username}
                onChange={handleChange}
                required
              />
            </div>

            {/* Campo Password (Común) */}
            <div className="mb-4">
              <label className="form-label fw-bold small text-muted">
                PASSWORD
              </label>
              <input
                type="password"
                name="password"
                className="form-control form-control-lg"
                placeholder="••••••••"
                value={formData.password}
                onChange={handleChange}
                required
              />
            </div>

            {/* Botón Submit */}
            <div className="d-grid gap-2">
              <button
                type="submit"
                className="btn btn-primary btn-lg fw-bold"
                disabled={isLoading}
              >
                {isLoading ? (
                  <span>
                    <span className="spinner-border spinner-border-sm me-2"></span>
                    Conectando...
                  </span>
                ) : activeTab === "login" ? (
                  "Connect to Network"
                ) : (
                  "Register Identity"
                )}
              </button>
            </div>
          </form>

          <div className="mt-4 text-center">
            <small className="text-muted" style={{ fontSize: "0.75rem" }}>
              Secure REST API calls routed via Docker Overlay
            </small>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
