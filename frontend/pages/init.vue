<template>
    <div class="main-container">
        <notifications v-if="showNotificationsPanel" @close="toggleNotificationsPanel" :token="token"
            @notification-accepted="addAcceptedEvent" />

        <div class="container">
            <div class="new-page">
                <div class="header">
                    <h1>Mi agenda</h1>
                    <button class="notification-button" @click="toggleNotificationsPanel">🔔</button>
                </div>

                <div v-for="evento in enhancedEventos" :key="evento.id"
                    :class="['evento', getEventStateClass(evento.start_time, evento.end_time)]"
                    @click="toggleDetails(evento.id)">

                    <div class="container-p">
                        <p>{{ evento.description }}
                        </p>
                        <div>
                            <button class="edit-button" @click.stop="editEvent(evento)">✏️</button>
                            <button class="delete-button" @click.stop="deleteEvent(evento.id)">🗑️</button>
                            <button class="add-user-button" @click.stop="openEmailInput(evento.id)">👤+</button>
                        </div>
                    </div>

                    <div v-if="evento.showDetails">
                        <p>Inicio: {{ new Date(evento.start_time) }}</p>
                        <p>Fin: {{ new Date(evento.end_time) }}</p>
                        <p>Estado: {{ getEventState(evento.start_time, evento.end_time) }}</p>
                    </div>


                    <div v-if="selectedEventId === evento.id && showEmailInput" class="email-input-container"
                        @click.stop>
                        <div class="email-header">
                            <h3>Agregar correos para el evento</h3>
                            <button class="close-email-button" @click.stop="closeEmailInput">❌</button>
                        </div>
                        <div class="email-input">
                            <input type="email" v-model="newEmail" placeholder="Escribe un correo y presiona Enter"
                                @keyup.enter.stop="addEmail" />
                            <ul>
                                <li v-for="(email, index) in emailList" :key="index" class="li-sep">
                                    {{ email }} <button @click.stop="removeEmail(index)" class="close-email-button"
                                        style="font-size: 10px;">❌</button>
                                </li>
                            </ul>
                            <button @click.stop="sendNotifications(evento.id)" class="send-button">Enviar
                                notificaciones</button>
                        </div>
                    </div>

                </div>
            </div>
            <div class="create-event-container">
                <button class="toggle-button" @click="toggleCreateEvent">+</button>
                <div v-if="showCreateEvent" class="create-event">
                    <div class="container-p">
                        <h2>Crear Evento</h2>
                        <button class="close-button" @click="closeForm">❌</button>
                    </div>

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
                        <p v-if="dateError" class="error-message">La fecha de inicio debe ser menor o igual que la fecha
                            de fin.</p>
                        <button type="submit" :disabled="dateError">Crear</button>
                    </form>
                </div>
                <div v-if="showEditEvent" class="edit-event">
                    <h2 class="container-p">Editar Evento <button class="close-button" @click="closeForm">❌</button>
                    </h2>

                    <form @submit.prevent="updateEvent">
                        <div>
                            <label for="edit_description">Descripción:</label>
                            <input type="text" id="edit_description" v-model="editEventDetails.description" required>
                        </div>
                        <div>
                            <label for="edit_start_time">Inicio:</label>
                            <input type="datetime-local" id="edit_start_time" v-model="editEventDetails.start_time"
                                required>
                        </div>
                        <div>
                            <label for="edit_end_time">Fin:</label>
                            <input type="datetime-local" id="edit_end_time" v-model="editEventDetails.end_time"
                                required>
                        </div>
                        
                        <p v-if="dateErrorEdit" class="error-message">La fecha de inicio debe ser menor o igual que la
                            fecha de fin.</p>
                        <button type="submit" :disabled="dateErrorEdit">Actualizar</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import { EVENTS_USER, EVENTS, MEETINGS } from '~/public/config';

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

const dateError = computed(() => {
    const start = new Date(newEvent.value.start_time);
    const end = new Date(newEvent.value.end_time);
    return start > end; // Devuelve true si la fecha de inicio es mayor que la de fin
});

const dateErrorEdit = computed(() => {
    const start = new Date(editEventDetails.value.start_time);
    const end = new Date(editEventDetails.value.end_time);
    return start > end; // Devuelve true si la fecha de inicio es mayor que la de fin
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
    if (dateError.value) {
        alert("Corrige las fechas antes de crear el evento.");
        return;
    }
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
    if (dateErrorEdit.value) {
        alert("Corrige las fechas antes de editar el evento.");
        return;
    }
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

const showNotificationsPanel = ref(false);
const toggleNotificationsPanel = () => {
    showNotificationsPanel.value = !showNotificationsPanel.value;
};

const selectedEventId = ref(null);
const showEmailInput = ref(false);
const emailList = ref([]);
const newEmail = ref("");

// Abre la caja para ingresar correos
const openEmailInput = (eventId) => {
    selectedEventId.value = eventId;
    showEmailInput.value = true;
};

// Añade un correo a la lista
const addEmail = () => {
    if (newEmail.value && !emailList.value.includes(newEmail.value)) {
        emailList.value.push(newEmail.value);
        newEmail.value = ""; // Limpia el campo de entrada
    }
};

// Elimina un correo de la lista
const removeEmail = (index) => {
    emailList.value.splice(index, 1);
};

// Envía notificaciones a los correos ingresados
const sendNotifications = async (eventId) => {
    if (emailList.value.length === 0) {
        alert("Por favor, agrega al menos un correo.");
        return;
    }

    try {
        await axios.post(MEETINGS, {
            event_id: eventId,
            users_email: emailList.value,
            state: 'pending'
        },
            {
                headers: {
                    'Authorization': `Bearer ${token.value}`
                }
            }
        );
        alert("Notificaciones enviadas exitosamente.");
        // Limpia el estado
        emailList.value = [];
        selectedEventId.value = null;
        showEmailInput.value = false;
    } catch (error) {
        console.error(error);
        alert("Hubo un error al enviar las notificaciones.");
    }
};

// Cierra la caja de correos
const closeEmailInput = () => {
    selectedEventId.value = null;
    showEmailInput.value = false;
};

const getEventState = (startTime, endTime) => {
    const now = new Date();
    const start = new Date(startTime);
    const end = new Date(endTime);

    if (now < start) {
        return "Pendiente";
    } else if (now >= start && now <= end) {
        return "En Progreso";
    } else {
        return "Completado";
    }
};

const enhancedEventos = computed(() => {
    return eventos.value.map(evento => ({
        ...evento,
        state: getEventState(evento.start_time, evento.end_time)
    }));
});

const getEventStateClass = (startTime, endTime) => {
    const state = getEventState(startTime, endTime);
    if (state === "Pendiente") return "evento-pendiente";
    if (state === "En Progreso") return "evento-progreso";
    if (state === "Completado") return "evento-completado";
};

const addAcceptedEvent = async (event) => {
    eventos.value.push(event);

    try {
        const response = await axios.post(EVENTS_USER, event, {
            headers: {
                'Authorization': `Bearer ${token.value}`
            }
        });
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
    margin-left: 10px;
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

/* Estilo base para los eventos */
.evento {
    padding: 10px;
    margin-bottom: 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
    cursor: pointer;
    background-color: #f9f9f9;
    transition: background-color 0.3s ease, border 0.3s ease;
}

/* Estilo para eventos pendientes */
.evento-pendiente {
    border-color: #ffc107;
    background-color: #fff9e6;
}

/* Estilo para eventos en progreso */
.evento-progreso {
    border-color: #007bff;
    background-color: #e6f3ff;
}

/* Estilo para eventos completados */
.evento-completado {
    border-color: #28a745;
    background-color: #e6ffe6;
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

.header {
    display: flex;
    justify-content: space-between;
}

.notification-button {
    background: none;
    border: none;
    font-size: 25px;
    cursor: pointer;
}

.main-container {
    display: flex;
    width: 100%;
    height: 100%;
    /* Altura total de la ventana */
}

.add-user-button {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 15px;
}

.li-sep {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.email-input-container {
    margin-top: 10px;
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 8px;
    background-color: #f9f9f9;
}

.email-input {
    display: flex;
    flex-direction: column;
}

.email-input input {
    margin-bottom: 10px;
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
}

.email-input ul {
    list-style-type: none;
    padding: 0;
}

.email-input ul li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 5px;
}

.send-button {
    padding: 8px 12px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

.email-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.close-email-button {
    background: none;
    border: none;
    font-size: 18px;
    cursor: pointer;
    color: red;
}

.error-message {
    color: red;
    font-size: 14px;
    margin-top: 5px;
}
</style>

<style>
body {
    font-family: Arial, sans-serif;
}
</style>