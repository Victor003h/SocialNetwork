// src/services/UserService.ts

import { RegisterData, ApiResponse } from "../../types/RegisterData";

export default class HandleRegister {
  private static BASE_URL = "http://localhost:3000"// cambia esto a tu backend

  static async registerUser(userData: RegisterData): Promise<ApiResponse> {
    try {
      const response = await fetch(`${this.BASE_URL}/users/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(userData),
      });

      // Caso: usuario ya existe
      if (response.status === 409) {
        return {
          ok: false,
          message: "El usuario ya existe en la base de datos.",
        };
      }

      // Caso: error del servidor
      if (!response.ok) {
        return {
          ok: false,
          message: `Error del servidor: ${response.status}`,
        };
      }

      return {
        ok: true,
        message: "Usuario registrado correctamente.",
      };

    } catch (error) {
      return {
        ok: false,
        message: error instanceof Error ? error.message : "Error desconocido",
      };
    }
  }
}
