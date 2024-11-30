<template>
  <div class="register-page">
    <h1>Registrarse</h1>
    <form @submit.prevent="register">
      <div>
        <label for="name">Nombre:</label>
        <input
          id="name"
          v-model="name"
          type="text"
          placeholder="Ingresa tu nombre"
          required
        />
      </div>
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
        {{ loading ? "Cargando..." : "Registrarse" }}
      </button>
      <p v-if="error" class="error">{{ error }}</p>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { USERS_ENDPOINT, LOGIN_PAGE } from '~/public/config';

const name = ref('');
const email = ref('');
const password = ref('');
const loading = ref(false);
const error = ref(null);
const router = useRouter();

const register = async () => {
  loading.value = true;
  error.value = null;

  try {
    const response = await axios.post(USERS_ENDPOINT, {
      name: name.value,
      email: email.value,
      password: password.value,
    });

    if (response.status !== 200) {
      throw new Error('Network response was not ok');
    }

    await router.push(LOGIN_PAGE);
  } catch (err) {
    error.value = 'Registration failed. Please try again.';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.register-page {
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