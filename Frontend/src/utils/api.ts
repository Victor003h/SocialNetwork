// src/utils/api.ts
import { User } from "../types/user";

export const fetchUsers = async (): Promise<User[]> => {
  // Simulación de llamada distribuida
  return [
    { id: "1", name: "Ana", isActive: true },
    { id: "2", name: "Carlos", isActive: false },
    { id: "3", name: "Beatriz", isActive: true },
  ];
};

export const joinNetwork = async (userId: string): Promise<boolean> => {
  console.log(`Usuario ${userId} se ha unido a la red.`);
  return true;
};
