// src/types/user.ts
export interface User {
  id: string;
  name: string;
  isActive: boolean;
  isConnected?: boolean;
}
