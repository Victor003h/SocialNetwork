// src/services/dataService.ts
import { Post, NewPostData, User } from '../types/feed.types';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

// Función auxiliar para obtener headers con Token
const getAuthHeaders = () => {
    const token = localStorage.getItem('jwt_token');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}` // <--- CLAVE PARA TU GATEWAY
    };
};

export const postService = {
    // Obtener el feed (GET /posts/)
    getFeed: async (): Promise<Post[]> => {
        const res = await fetch(`${API_URL}/posts/feed`, { // Asumo que tu microservicio tiene ruta /feed o /
            method: 'GET',
            headers: getAuthHeaders()
        });
        if (!res.ok) throw new Error('Error cargando el feed distribuido');
        return res.json();
    },

    // Crear post (POST /posts/)
    createPost: async (data: NewPostData): Promise<Post> => {
        const res = await fetch(`${API_URL}/posts/create`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error('No se pudo replicar el post');
        return res.json();
    }
};

export const userService = {
    // Obtener amigos activos (GET /users/friends)
    getFriends: async (): Promise<User[]> => {
        // Si tu backend aun no tiene esta ruta, retornará 404/500
        try {
            const res = await fetch(`${API_URL}/users/friends`, {
                method: 'GET',
                headers: getAuthHeaders()
            });
            if (!res.ok) throw new Error('Error fetching users');
            return res.json();
        } catch (e) {
            console.warn("User service warning:", e);
            return []; // Retornamos vacío para no romper la UI si falla este microservicio
        }
    }
};