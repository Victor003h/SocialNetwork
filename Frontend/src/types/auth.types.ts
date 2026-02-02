// src/types/auth.types.ts

export interface AuthResponse {
    token: string;
    user?: {
        id: string;
        username: string;
    };
    error?: string;
}

export interface LoginCredentials {
    username: string;
    password: string;
}

export interface RegisterCredentials {
    username: string;
    email: string;
    password: string;
}