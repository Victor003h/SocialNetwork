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

        // Si la respuesta no es 2xx (por ejemplo 503)
        if (!response.ok) {
            let errorMessage = `Error ${response.status}`;
            try {
                // Intentamos leer el JSON de error que enviamos desde Flask
                const errorData = await response.json();
                // Si Flask mandó {"error": "...", "details": "..."}, lo usamos
                errorMessage = errorData.details || errorData.error || errorMessage;
            } catch (e ) {
                // Si no es un JSON, usamos el texto plano
                const textError = await response.text();
                errorMessage = textError || errorMessage;
            }
            throw new Error(errorMessage);
        }

        return await response.json();

    } catch (error: unknown) {
        console.error("Auth Error:", error);
        // Re-lanzamos el error para que el componente UI lo capture
        if (error instanceof Error) throw error;
        throw new Error('Error de conexión con el servidor');
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