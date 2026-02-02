// src/services/authService.ts
import { AuthResponse, LoginCredentials, RegisterCredentials } from '../types/auth.types';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

async function authRequest(endpoint: string, data: object): Promise<AuthResponse> {
    try {
        const response = await fetch(`${API_URL}/auth/${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });

        const result: AuthResponse = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Error en el servidor');
        }

        return result;
    } catch (error: unknown) {
        console.error("Auth Error:", error);
        throw new Error((error as Error).message || 'Error de conexión con el Gateway');
    }
}

export const authService = {
    login: async (creds: LoginCredentials) => {
        const data = await authRequest('login', creds);
        if (data.token) {
            localStorage.setItem('jwt_token', data.token);
        }
        return data;
    },

    register: async (creds: RegisterCredentials) => {
        return await authRequest('register', creds);
    },

    logout: () => {
        localStorage.removeItem('jwt_token');
    },

    isAuthenticated: (): boolean => {
        return !!localStorage.getItem('jwt_token');
    }
};