<template>
    <div class="new-page">
      <h1>Nueva Página</h1>
      <p>Token: {{ token }}</p>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue';
  import { useRoute } from 'vue-router';
  
  const route = useRoute();
  const token = ref('');
  
  onMounted(() => {
    if (route.query.token) {
      token.value = route.query.token;
    }
  });
  </script>
  
  <style scoped>
  .new-page {
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
  
  p {
    text-align: center;
  }
  </style>