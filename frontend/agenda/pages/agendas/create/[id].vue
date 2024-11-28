<template>
  <div class="create-cita">
    <h1>Crear Cita</h1>
    <form @submit.prevent="handleCreateCita">
      <div>
        <label for="title">Título de la cita:</label>
        <input
          id="title"
          v-model="form.title"
          type="text"
          placeholder="Título"
          required
        />
      </div>
      <div>
        <label for="date">Fecha:</label>
        <input
          id="date"
          v-model="form.date"
          type="date"
          required
        />
      </div>
      <div>
        <label for="time">Hora:</label>
        <input
          id="time"
          v-model="form.time"
          type="time"
          required
        />
      </div>
      <div>
        <label for="description">Descripción:</label>
        <textarea
          id="description"
          v-model="form.description"
          placeholder="Detalles de la cita"
        ></textarea>
      </div>
      <button type="submit" :disabled="loading">
        {{ loading ? "Creando..." : "Crear Cita" }}
      </button>
      <p v-if="error" class="error">{{ error }}</p>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRoute, useRouter } from '#imports';

// Estado local del formulario
const form = ref({
  title: '',
  date: '',
  time: '',
  description: '',
});

const loading = ref(false);
const error = ref(null);

// Acceso a la ruta y el router
const route = useRoute();
const router = useRouter();

const handleCreateCita = async () => {
  loading.value = true;
  error.value = null;

  try {
    // Obtener el ID de la agenda desde la URL
    const agendaId = route.params.id;

    // Enviar datos al backend
    await $fetch(`/agendas/${agendaId}/citas`, {
      method: 'POST',
      body: {
        title: form.value.title,
        date: form.value.date,
        time: form.value.time,
        description: form.value.description,
      },
    });

    // Redirigir a los detalles de la agenda
    await router.push(`/agendas/${agendaId}`);
  } catch (err) {
    // Manejar errores
    error.value = err?.data?.message || 'Error al crear la cita';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.create-cita {
  max-width: 600px;
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

input,
textarea {
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
