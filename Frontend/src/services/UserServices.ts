// src/services/dataService.ts
import { User } from '../types/feed.types';
import { getAuthHeaders, getUser } from '../utils/utils';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

export const userService = {
    // Obtener amigos activos (GET /users/friends)
    
    getAllUsers: async (): Promise<User[]> => {
        const user= getUser()
        const res = await fetch(`${API_URL}/users`, {
            method: 'GET',
            headers: getAuthHeaders()
        });
        if (!res.ok) throw new Error('Error al listar usuarios del clúster');
        const allUsers: User[] = await res.json();
   
        return allUsers.filter(u => u.id !== user.id); 
    },

    getUser: async (user_id:number): Promise<User[]> => {

        const res = await fetch(`${API_URL}/users/${user_id}`, {
            method: 'GET',
            headers: getAuthHeaders()
        });
        if (!res.ok) throw new Error('Error al listar usuarios del clúster');
        return res.json();
    },
   
};