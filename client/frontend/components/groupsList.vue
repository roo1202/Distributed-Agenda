<template>
    <h3>Eventos de los usuarios del grupo: </h3>
    <template v-for="event in events">
        <div style="display: flex; justify-content:space-between; align-items:center;">
            <p style="width: 220px;">Description: {{ event.description }}</p>
            <p style="width: 220px;">Inicio: {{ event.start_time }}</p>
            <p style="width: 220px;">Fin: {{ event.end_time }}</p>
        </div>
    </template>

    <button style="margin-left: 40%;" @click="createEvent()">Crear un metting de grupo</button>
    <div style="display: flex; justify-content:space-around; align-items:center; margin-bottom:10px;margin-top:10px;">
        <label>Seleccionar usuarios:</label>
        <!-- Multiselect corregido (necesitas importar el componente) -->
        <select v-model="selectedUsers" multiple style="width:100px; height:20px;">
            <option v-for="user in users" :key="user" :value="user">
              {{ user}}
            </option>
          </select>
          <small>Mantén presionado Ctrl (Windows) para seleccionar múltiples opciones</small>
    </div>

    <div style="display: flex; justify-content:space-around; align-items:center;">
        <label>Seleccionar evento:</label>
        <!-- Select nativo corregido -->
        <select v-model="selectedEvent">
            <option 
                v-for="event in groupEvents" 
                :key="event.id" 
                :value="event"
            >
                {{ event.name || event.description }}
            </option>
        </select>
    </div>
   
    <div style="display: flex; justify-content:space-around; align-items:center;" >
        <h5>Evento seleccionado: </h5>
        {{ selectedEvent? selectedEvent.description : ''}} 
    </div>

    <div style="display: flex;justify-content:space-around; align-items:center;">
        <h5>Usuario seleccionado</h5>
        {{ selectedUsers }}
    </div>

</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { EVENTS, GROUPS } from '~/public/config';

const props = defineProps({
    group: {
        type: Object,
        required: true
    }
});

const route = useRoute();
const token = ref('');
const name = ref('')
const events = ref([])
const groupEvents = ref([])
const users = ref([])
const selectedEvent = ref();
const selectedUsers = ref([]);

onMounted(async () => {
    token.value = route.query.token;
    name.value = route.query.name;

    try {
        const response = await axios.get(GROUPS + props.group.id + '/events', {
            headers: {
                'Authorization': `Bearer ${token.value}`
            }
        });
        events.value = response.data;
    } catch (err) {
        console.error(err);
    }

    users.value = await getUsuarios(props.group.id);
    users.value = users.value.filter(x => x != route.query.email)
    groupEvents.value = await getEventsFromUser();
});

const getUsuarios = async (idGrupo) => {
    try {
        const response = await axios.get(GROUPS + idGrupo + '/users', {
            headers: { 'Authorization': `Bearer ${token.value}` },
        });
        return response.data;
    } catch (err) {
        console.error(err);
        return [];
    }
}

const getEventsFromUser = async() => {
    try {
        const response = await axios.get(EVENTS + 'user/', {
            headers: {
                'Authorization': `Bearer ${token.value}`
            }
        });
        return response.data;
    } catch (err) {
        console.error(err);
        return [];
    }
}

const createEvent = async() => {
    try {
        if(!selectedEvent.value || !selectedUsers.value){
            
            alert('Seleccione un eventos y al menos un usuario')
            return;
        }
        const data = {users_email: selectedUsers.value, event_id: selectedEvent.value.id, state: selectedEvent.value.state};
        const response = await axios.post(GROUPS + props.group.id  + '/meetings/user/', data, {
            headers: {
                'Authorization': `Bearer ${token.value}`
            }
        });
        alert('Se ha creado el meeting')
        return response.data;
    } catch (err) {
        console.error(err);
        alert('Ha ocurrido un error')
        return [];
    }
}
</script>

<!-- Necesitas importar el CSS de multiselect -->
<style></style>
<style scoped></style>