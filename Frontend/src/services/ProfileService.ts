// src/services/dataService.ts (Agrega esto al final o dentro de userService)

import { UserProfile, ProfileUpdateData } from '../types/profile.types';
import { authService } from './AuthService';
import { followServices } from './FollowsServices';
import { postService } from './PostServices';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

export const profileService = {
    
    getMyProfile: async ():Promise<UserProfile> => {
        const user = authService.getCurrentUser();
        
        if (!user) throw new Error("No hay sesión activa");

        const token = localStorage.getItem('jwt_token');
        const res = await fetch(`${API_URL}/users/${user.id}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!res.ok) throw new Error('No se pudo recuperar el perfil del nodo');
        
        const followersPromise = followServices.getFollowers()
        const postsPromise = postService.getUserPost()

        const [posts, followers] = await Promise.all([
                postsPromise,
                followersPromise,
                res    
        ]);
        const data = await res.json()
        
        const UserProfile = {
            ...data,
            postCount: posts.length,
            followerCount: followers.length

        }
        return UserProfile


    },    
    // Actualizar perfil
    updateProfile: async (data: ProfileUpdateData): Promise<UserProfile> => {
        
        if (!data.id) throw new Error("No hay sesión activa");

        const token = localStorage.getItem('jwt_token');
        const res = await fetch(`${API_URL}/users/${data.id}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error('No se pudo actualizar el perfil del nodo');
        return res.json();
    }
};