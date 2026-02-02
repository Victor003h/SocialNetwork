// src/types/feed.types.ts

export interface User {
    id: string;
    username: string;
    avatarUrl?: string; // URL de la foto
    status?: 'online' | 'offline';
}

export interface Post {
    id: string;
    userId: string;
    authorName: string; // En un sistema real, a veces esto viene "populado" o se busca aparte
    authorAvatar?: string;
    content: string;
    imageUrl?: string;
    timestamp: string;
    likes: number;
    comments: number;
}

export interface NewPostData {
    content: string;
    imageUrl?: string;
}