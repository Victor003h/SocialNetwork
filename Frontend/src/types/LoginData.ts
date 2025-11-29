export interface LoginData {
  username: string;
  password: string;
}

export interface AuthResponse {
  ok: boolean;       // true si pudo iniciar sesión
  message: string;   // texto descriptivo
  token?: string;    // si usas JWT
        // info del usuario (opcional)
}