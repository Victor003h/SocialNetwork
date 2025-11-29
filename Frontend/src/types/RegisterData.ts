export interface RegisterData {
  firstName: string;
  lastName: string;
  username: string;
  password: string;
  email: string;
  phone: string;
}

export interface ApiResponse {
  ok: boolean;          // true si todo salió bien
  message: string;      // descripción       // datos que devuelva el backend
}