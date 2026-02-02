// src/types/profile.types.ts

export interface UserProfile {
    id: string;
    username: string;
    email: string;
    bio: string;
    location: string;
    avatarUrl: string;
    bannerUrl?: string; // Opcional: fondo de perfil
    joinDate: string;
}

// Datos que permitimos editar (no dejamos editar ID ni email por seguridad usualmente)
export interface ProfileUpdateData {
    bio?: string;
    location?: string;
    avatarUrl?: string;
}