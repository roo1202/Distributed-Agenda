<template>
    <div>
      <h1>Register</h1>
      <form @submit.prevent="register">
        <div>
          <label for="email">Email:</label>
          <input type="email" v-model="email" required />
        </div>
        <div>
          <label for="password">Password:</label>
          <input type="password" v-model="password" required />
        </div>
        <div>
          <button type="submit" :disabled="loading">Register</button>
        </div>
        <div v-if="error">{{ error }}</div>
      </form>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue';
  import { useRouter } from 'vue-router';
  import axios from 'axios';
  
  const email = ref('');
  const password = ref('');
  const loading = ref(false);
  const error = ref(null);
  const router = useRouter();
  
  const register = async () => {
    loading.value = true;
    error.value = null;
  
    try {
      const response = await axios.post('http://127.0.0.1:8000/api/v1/users/', {
        name: email.value,
        email: email.value,
        password: password.value,
      });
  
      if (response.status !== 200) {
        throw new Error('Network response was not ok');
      }
  
      await router.push('/login');
    } catch (err) {
      error.value = 'Registration failed. Please try again.';
    } finally {
      loading.value = false;
    }
  };
  </script>