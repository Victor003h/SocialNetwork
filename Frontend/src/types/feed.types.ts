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
    id: string;
    userId: string;
    UserName: string; // En un sistema real, a veces esto viene "populado" o se busca aparte
    content: string;
    created: string;
    //likes: number;
    //comments: number;
}

export interface NewPostData {
    content: string;
    imageUrl?: string;
}