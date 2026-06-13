// src/services/dataService.ts
import { Post } from '../types/feed.types';
import { getAuthHeaders, getUser } from '../utils/utils';
const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';


export const postService = {
    // Obtener el feed (GET /posts/)
    getFeed: async (): Promise<Post[]> => {
        // Gateway (/posts/...) -> Post Service (/posts)
        
        const res = await fetch(`${API_URL}/posts`, {
            method: 'GET',
            headers: getAuthHeaders()
        });
        if (!res.ok) throw new Error('Error al obtener el feed distribuido');
        
        return res.json();
    },

    getUserPost: async (): Promise<Post[]> => {

        const user = getUser()
        return postService.getUserPostsById(user.id);
    },

    // Posts de un usuario concreto (GET /posts/user/:id) — para popover y listas
    getUserPostsById: async (user_id: number): Promise<Post[]> => {
        const res = await fetch(`${API_URL}/posts/user/${user_id}`, {
            method: 'GET',
            headers: getAuthHeaders()
        });
        if (!res.ok) throw new Error('Error al obtener los posts del usuario');

        return res.json();
    },

    
    createPost: async (content: string): Promise<Post> => {
        // Recuperamos la información del usuario guardada en el localStorage
        
        console.log(content);
        

        const user = getUser()

        const payload = {
            content: content,
            user_id: user.id 
        };

        const res = await fetch(`${API_URL}/posts`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error('Error al enviar el post al clúster');
        return res.json();
    },

    deletePost: async (post_id: number): Promise<Post> => {
        // Recuperamos la información del usuario guardada en el localStorage

        const res = await fetch(`${API_URL}/posts/${post_id}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });

        if (!res.ok) throw new Error('Error al elimnar el post en el clúster');
        return res.json();
    }
};