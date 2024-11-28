<template>
    <div class="dashboard">
      <h1>Mis Agendas</h1>
  
      <!-- Sección de fechas más cercanas -->
      <section>
        <h2>Fechas Próximas</h2>
        <ul v-if="upcomingDates.length > 0">
          <li v-for="date in upcomingDates" :key="date.id">
            <strong>{{ date.title }}</strong>: {{ formatDate(date.date) }}
          </li>
        </ul>
        <p v-else>No hay eventos próximos.</p>
      </section>
  
      <!-- Sección de agendas -->
      <section>
        <h2>Agendas</h2>
        <ul>
          <li v-for="agenda in agendas" :key="agenda.id">
            <strong>{{ agenda.name }}</strong>
            <button @click="viewAgenda(agenda.id)">Ver Detalles</button>
          </li>
        </ul>
      </section>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue';
  import { useRouter } from '#imports';
  
  // Estado para las agendas y las fechas próximas
  const agendas = ref([]);
  const upcomingDates = ref([]);
  const router = useRouter();
  
  // Función para obtener las agendas y eventos cercanos del backend
  const fetchAgendas = async () => {
    try {
      // Solicita las agendas del usuario desde el backend
      agendas.value = await $fetch('/agendas');
  
      // Solicita las fechas próximas
      upcomingDates.value = await $fetch('/agendas/upcoming');
    } catch (err) {
      console.error('Error al obtener las agendas:', err);
    }
  };
  
  // Formatea las fechas para mostrarlas de forma legible
  const formatDate = (dateString) => {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };
  
  // Redirige a la página de detalles de una agenda
  const viewAgenda = (agendaId) => {
    router.push(`/agendas/${agendaId}`);
  };
  
  // Llama a la función para cargar los datos al montar el componente
  onMounted(fetchAgendas);
  </script>
  
  <style scoped>
  .dashboard {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
  }
  
  h1, h2 {
    color: #333;
  }
  
  ul {
    list-style-type: none;
    padding: 0;
  }
  
  li {
    margin: 10px 0;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
  }
  
  button {
    margin-top: 5px;
    padding: 5px 10px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  button:hover {
    background-color: #0056b3;
  }
  </style>
  

