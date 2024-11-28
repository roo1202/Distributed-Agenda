export default defineNuxtRouteMiddleware((to, from) => {
    const token = useCookie('auth_token').value;
    if (!token) {
      return navigateTo('/auth/login');
    }
  });
  