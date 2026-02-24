export const getAuthHeaders = () => {
    const token = localStorage.getItem('jwt_token');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}` // <--- CLAVE PARA TU GATEWAY
    };
};

export const getUser= () => {
    
    const userJson = localStorage.getItem('user_info');
    const user = userJson ? JSON.parse(userJson) : null;

    if (!user || !user.id) {
            throw new Error('No se encontró información del usuario en la sesión.');
        }

    return user
}