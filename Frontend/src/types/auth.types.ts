// src/types/auth.types.ts

export interface LoginResponse {
        
    token: string;
    user: {
        id: string;
        username: string;
        password: string;
        dateCreated: string;
    }
}
export interface AuthResponse {
   userid?: string;
   state?: number;
}
export interface LoginCredentials {
    username: string;
    password: string;
}

export interface RegisterCredentials {
    username: string;
    password: string;
}