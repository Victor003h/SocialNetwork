// src/types/feed.types.ts

export interface User {
    id: number
    username: string;
    followers: number; // Número de seguidores
    posts: number; // Número de posts
    status?: 'online' | 'offline';
    avatarUrl: string
}

export interface Post {
    id: number;
    user_id: number;
    UserName?: string; // El gateway lo "popula" en GET /posts; en /posts/user/:id puede no venir
    content: string;
    created_at: string;
}

export interface NewPostData {
    content: string;
    imageUrl?: string;
}