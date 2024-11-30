<template>
  <div class="login-page">
    <h1>Iniciar sesión</h1>
    <form @submit.prevent="handleLogin">
      <div>
        <label for="email">Correo electrónico:</label>
        <input
          id="email"
          v-model="email"
          type="email"
          placeholder="Ingresa tu correo"
          required
        />
      </div>
      <div>
        <label for="password">Contraseña:</label>
        <input
          id="password"
          v-model="password"
          type="password"
          placeholder="Ingresa tu contraseña"
          required
        />
      </div>
      <button type="submit" :disabled="loading">
        {{ loading ? "Cargando..." : "Iniciar sesión" }}
      </button>
      <button type="button" @click="goToRegister">
        Registrarse
      </button>
      <p v-if="error" class="error">{{ error }}</p>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useCookie, useRouter } from '#imports';
import { REGISTER_PAGE } from '~/public/config';

// Estado local para el formulario y la carga
const email = ref('');
const password = ref('');
const loading = ref(false);
const error = ref(null);

// Router para redirigir después de iniciar sesión
const router = useRouter();

const handleLogin = async () => {
  loading.value = true;
  error.value = null;

  try {
    // Realizar la solicitud al backend
    const response = await $fetch('/auth/login', {
      method: 'POST',
      body: { email: email.value, password: password.value },
    });

    // Guardar el token en una cookie
    const authToken = useCookie('auth_token');
    authToken.value = response.token;

    // Redirigir a la nueva página con el token como parámetro de consulta
    await router.push({ path: '/new-page', query: { token: response.token } });
  } catch (err) {
    // Manejar errores
    error.value = err?.data?.message || 'Error al iniciar sesión';
  } finally {
    loading.value = false;
  }
};

const goToRegister = () => {
  router.push(REGISTER_PAGE);
};
</script>

<style scoped>
.login-page {
  max-width: 400px;
  margin: 0 auto;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

h1 {
  text-align: center;
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 5px;
}

input {
  width: 100%;
  padding: 8px;
  margin-bottom: 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

button {
  width: 100%;
  padding: 10px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 10px;
}

button:disabled {
  background-color: #aaa;
  cursor: not-allowed;
}

.error {
  color: red;
  text-align: center;
  margin-top: 10px;
}
</style>