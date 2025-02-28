import { defineStore } from 'pinia';
import { authService } from '../services/auth'

export const useAuthStore = defineStore('auth', () => {
    const state = {
        user: null,
        token: null,
    };
    
    const login = async() => {
        const response = await authService.login();

        if(!response.ok){
            return { status: 'error', message: `Error al login: ${response.data}` };
        }

        state.user = response.user;
        state.token = response.token;
    }

    return {
        state,
        login,
    }
});
