<template>
  <div class="container">
    <div class="new-page">
      <h1>Mi agenda</h1>
      <div v-for="evento in sortedEventos" :key="evento.id" class="evento" @click="toggleDetails(evento.id)">
        <p class="container-p">{{ evento.description }}
        <div>
          <button class="edit-button" @click.stop="editEvent(evento)">✏️</button>
          <button class="delete-button" @click.stop="deleteEvent(evento.id)">🗑️</button>
        </div>
        </p>

        <div v-if="evento.showDetails">
          <p>Inicio: {{ evento.start_time }}</p>
          <p>Fin: {{ evento.end_time }}</p>
          <p>Estado: {{ evento.state }}</p>
        </div>
      </div>
    </div>
    <div class="create-event-container">
      <button class="toggle-button" @click="toggleCreateEvent">+</button>
      <div v-if="showCreateEvent" class="create-event">
        <h2 class="container-p">Crear Evento <button class="close-button" @click="closeForm">X</button></h2>

        <form @submit.prevent="createEvent">
          <div>
            <label for="description">Descripción:</label>
            <input type="text" id="description" v-model="newEvent.description" required>
          </div>
          <div>
            <label for="start_time">Inicio:</label>
            <input type="datetime-local" id="start_time" v-model="newEvent.start_time" required>
          </div>
          <div>
            <label for="end_time">Fin:</label>
            <input type="datetime-local" id="end_time" v-model="newEvent.end_time" required>
          </div>
          <div>
            <label for="state">Estado:</label>
            <select id="state" v-model="newEvent.state" required>
              <option value="pendiente">Pendiente</option>
              <option value="completado">Completado</option>
            </select>
          </div>
          <button type="submit">Crear</button>
        </form>
      </div>
      <div v-if="showEditEvent" class="edit-event">
        <h2 class="container-p">Editar Evento <button class="close-button" @click="closeForm">X</button></h2>

        <form @submit.prevent="updateEvent">
          <div>
            <label for="edit_description">Descripción:</label>
            <input type="text" id="edit_description" v-model="editEventDetails.description" required>
          </div>
          <div>
            <label for="edit_start_time">Inicio:</label>
            <input type="datetime-local" id="edit_start_time" v-model="editEventDetails.start_time" required>
          </div>
          <div>
            <label for="edit_end_time">Fin:</label>
            <input type="datetime-local" id="edit_end_time" v-model="editEventDetails.end_time" required>
          </div>
          <div>
            <label for="edit_state">Estado:</label>
            <select id="edit_state" v-model="editEventDetails.state" required>
              <option value="pendiente">Pendiente</option>
              <option value="completado">Completado</option>
            </select>
          </div>
          <button type="submit">Actualizar</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import { EVENTS_USER, EVENTS } from '~/public/config';

const route = useRoute();
const token = ref('');
const eventos = ref([]);
const newEvent = ref({
  description: '',
  start_time: '',
  end_time: '',
  state: 'pendiente'
});
const showCreateEvent = ref(false);
const showEditEvent = ref(false);
const editEventDetails = ref({
  id: '',
  description: '',
  start_time: '',
  end_time: '',
  state: 'pendiente'
});

const sortedEventos = computed(() => {
  return eventos.value.sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
});

const toggleDetails = (id) => {
  const evento = eventos.value.find(evento => evento.id === id);
  if (evento) {
    evento.showDetails = !evento.showDetails;
  }
};

const toggleCreateEvent = () => {
  showCreateEvent.value = !showCreateEvent.value;
};

const closeForm = () => {
  showCreateEvent.value = false;
  showEditEvent.value = false;
};

const createEvent = async () => {
  try {
    const response = await axios.post(EVENTS_USER, newEvent.value, {
      headers: {
        'Authorization': `Bearer ${token.value}`
      }
    });
    eventos.value.push({ ...response.data, showDetails: false });
    newEvent.value = {
      description: '',
      start_time: '',
      end_time: '',
      state: 'pendiente'
    };
    showCreateEvent.value = false;
  } catch (err) {
    console.log(err);
  }
};

const editEvent = (evento) => {
  editEventDetails.value = { ...evento };
  showEditEvent.value = true;
};

const updateEvent = async () => {
  try {
    const response = await axios.put(`${EVENTS}${editEventDetails.value.id}`, editEventDetails.value, {
      headers: {
        'Authorization': `Bearer ${token.value}`
      }
    });
    const index = eventos.value.findIndex(evento => evento.id === editEventDetails.value.id);
    if (index !== -1) {
      eventos.value[index] = { ...response.data, showDetails: eventos.value[index].showDetails };
    }
    showEditEvent.value = false;
  } catch (err) {
    console.log(err);
  }
};

const deleteEvent = async (id) => {
  try {
    await axios.delete(`${EVENTS}${id}`, {
      headers: {
        'Authorization': `Bearer ${token.value}`
      }
    });
    eventos.value = eventos.value.filter(evento => evento.id !== id);
  } catch (err) {
    console.log(err);
  }
};

onMounted(async () => {
  if (route.query.token) {
    token.value = route.query.token;

    try {
      const response = await axios.get(EVENTS_USER, {
        headers: {
          'Authorization': `Bearer ${token.value}`
        }
      });
      eventos.value = response.data.map(evento => ({ ...evento, showDetails: false }));
    } catch (err) {
      console.log(err);
    }
  }
});
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.new-page {
  width: 97%;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.create-event-container {
  width: 100%;
}

.toggle-button {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background-color: #007BFF;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 25px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: fixed;
  bottom: 20px;
  right: 20px;
}

.create-event,
.edit-event {
  width: 97%;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  font-family: Arial, sans-serif;
}

h1,
h2 {
  text-align: center;
  margin-bottom: 20px;
}

.evento {
  padding: 10px;
  margin-bottom: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: pointer;
  background-color: #f9f9f9;
}

.evento p {
  margin: 5px 0;
}

form div {
  margin-bottom: 10px;
}

label {
  display: block;
  margin-bottom: 5px;
}

input,
select {
  width: 100%;
  padding: 8px;
  box-sizing: border-box;
}

.edit-button {
  background: none;
  border: none;
  cursor: cell;
}

.container-p {
  display: flex;
  justify-content: space-between;
}

.close-button {
  background: none;
  border: none;
  font-size: 15px;
  cursor: pointer;
}

.delete-button {
  background: none;
  border: none;
  font-size: 15px;
  cursor: pointer;
}
</style>

<style>
body {
  font-family: Arial, sans-serif;
}
</style>