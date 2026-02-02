// src/services/dataService.ts (Agrega esto al final o dentro de userService)

import { UserProfile, ProfileUpdateData } from '../types/profile.types';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

export const profileService = {
    // Obtener mi perfil
    getMyProfile: async (): Promise<UserProfile> => {
        const token = localStorage.getItem('jwt_token');
        const res = await fetch(`${API_URL}/users/me`, { // Asumiendo ruta /me
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        if (!res.ok) throw new Error('Error cargando perfil');
        return res.json();
    },

    // Actualizar perfil
    updateProfile: async (data: ProfileUpdateData): Promise<UserProfile> => {
        const token = localStorage.getItem('jwt_token');
        const res = await fetch(`${API_URL}/users/me`, {
            method: 'PUT', // O PATCH
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error('Error actualizando perfil');
        return res.json();
    }
};