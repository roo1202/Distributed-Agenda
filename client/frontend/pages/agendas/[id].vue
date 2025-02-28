<template>
    <div>
      <h1>Detalles de la Agenda</h1>
      <p v-if="loading">Cargando...</p>
      <div v-else>
        <h2>{{ agenda.name }}</h2>
        <ul>
          <li v-for="event in agenda.events" :key="event.id">
            {{ event.title }} - {{ formatDate(event.date) }}
          </li>
        </ul>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue';
  import { useRoute } from '#imports';
  
  const route = useRoute();
  const agenda = ref(null);
  const loading = ref(true);
  
  const fetchAgendaDetails = async () => {
    try {
      const id = route.params.id;
      agenda.value = await $fetch(`/agendas/${id}`);
    } catch (err) {
      console.error('Error al cargar la agenda:', err);
    } finally {
      loading.value = false;
    }
  };
  
  const formatDate = (dateString) => {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };
  
  onMounted(fetchAgendaDetails);
  </script>
  