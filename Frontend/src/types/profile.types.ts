// src/types/profile.types.ts

export interface UserProfile {
    id: number;
    username: string;
    createdAt: Date;
    postCount: number;
    followerCount: number;
    
}

// Datos que permitimos editar (no dejamos editar ID ni email por seguridad usualmente)
export interface ProfileUpdateData {
    
    id?: number; // Opcional, se puede usar para identificar el nodo
    username: string;
    password?: string;
    
    
}