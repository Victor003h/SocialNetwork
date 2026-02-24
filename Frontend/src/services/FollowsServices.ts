import { getAuthHeaders,getUser } from "../utils/utils";
import { User } from "../types/feed.types";
const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

export const followServices ={

    getFollowers: async (): Promise<User[]> => {
    
        const user = getUser()

        try {
            const res = await fetch(`${API_URL}/follows/followers/${user.id}`, {
                method: 'GET',
                headers: getAuthHeaders()
            });
            if (!res.ok) throw new Error('Error fetching followers');
            return res.json();
        } catch (e) {
            console.warn("User service warning:", e);
            return []; // Retornamos vacío para no romper la UI si falla este microservicio
        }
        },
        
    getFollowed: async (): Promise<User[]> => {
        
        const user= getUser()

        try {
            const res = await fetch(`${API_URL}/follows/followed/${user.id}`, {
                method: 'GET',
                headers: getAuthHeaders()
            });
            if (!res.ok) throw new Error('Error fetching followed');
            return res.json();
        } catch (e) {
            console.warn("User service warning:", e);
            return []; // Retornamos vacío para no romper la UI si falla este microservicio
        }
    },
    
    
    followUser: async (followed_id: number): Promise<void> => {

        const user= getUser()
        
        const body = {
            "follower_id": user.id,
            "followed_id": followed_id
        }
        
        const res = await fetch(`${API_URL}/follows`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(body)
        });
        if (!res.ok) throw new Error('No se pudo registrar el seguimiento en el nodo');
    },

    deletefollow: async (followed_id: number): Promise<void> => {

        const user= getUser()
        
        const body = {
            "follower_id": user.id,
            "followed_id": followed_id
        }
        
        const res = await fetch(`${API_URL}/follows`, {
            method: 'DELETE',
            headers: getAuthHeaders(),
            body: JSON.stringify(body)
        });
        if (!res.ok) throw new Error('No se pudo eliminar la relacion en el nodo');
    }
}
