// src/services/authService.ts
import { AuthResponse,LoginResponse, LoginCredentials, RegisterCredentials } from '../types/auth.types';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'https://localhost:5001';

async function authRequest(endpoint: string, data: object) {
    try {
        const response = await fetch(`${API_URL}/${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        
        if (!response.ok) {
            throw new Error('Error en el servidor');
        }
        
        const result = await response.json();
        
        return result;
   

        
    } catch (error: unknown) {
        console.error("Auth Error:", error);
        throw new Error((error as Error).message || 'Error de conexión con el Gateway');
    }
}

export const authService = {
    login: async (creds: LoginCredentials) => {
        const data:LoginResponse= await authRequest('login', creds);
        if (data.token) {
            localStorage.setItem('jwt_token', data.token);
        }
        return data;
    },

    register: async (creds: RegisterCredentials) => {
        const data:AuthResponse = await authRequest('register', creds);
        
        return data.state;
    },

    logout: () => {
        localStorage.removeItem('jwt_token');
    },

    isAuthenticated: (): boolean => {
        return !!localStorage.getItem('jwt_token');
    }
};