// src/services/AuthService.ts
import { LoginData, AuthResponse } from "../../types/LoginData";


export default class handleLogin {
  private static BASE_URL = "http://localhost:3000"; // editar a tu backend REAL

  static async login(userData: LoginData): Promise<AuthResponse> {
    try {
      const response = await fetch(`${this.BASE_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(userData),
      });

      // Usuario no encontrado
      if (response.status === 404) {
        return {
          ok: false,
          message: "El usuario no está registrado.",
        };
      }

      // Contraseña incorrecta
      if (response.status === 401) {
        return {
          ok: false,
          message: "La contraseña es incorrecta.",
        };
      }

      // Error del servidor
      if (!response.ok) {
        return {
          ok: false,
          message: `Error del servidor: ${response.status}`,
        };
      }

      const data = await response.json();

      return {
        ok: true,
        message: "Inicio de sesión exitoso.",
        token: data.token,   // si el backend devuelve token
      };

    } catch (error) {
      return {
        ok: false,
        message: error instanceof Error ? error.message : "Error desconocido",
      };
    }
  }
}
