<template>
    <div class="notifications-panel" :class="{ visible: isVisible, hidden: !isVisible }">
        <div class="header">
            <h2>Notificaciones</h2>
            <button class="close-button" @click="$emit('close')">❌</button>
        </div>
        <ul>
            <li v-for="notification in notifications" :key="notification.id" class="notification-item">

                <div>
                    <p>{{ notification.event_description }} </p>
                </div>
                <div class="actions">
                    <button class="accept-button" @click="acceptNotification(notification)">Aceptar</button>
                    <button class="reject-button"
                        @click="respondToNotification(notification.id, notification.event_id, 'Cancelled')">Rechazar</button>
                </div>
            </li>
        </ul>
        <ul>
            <li v-for="group in groupsInvitations" :key="group.id" class="notification-item">
                <div>
                    <p>
                        {{ group.name }}
                    </p>
                    <div class="actions">
                        <button class="accept-button" @click="acceptGroup(group.id)">Aceptar</button>
                        <button class="reject-button"
                            @click="removeUserFromGroup(group.id)">Rechazar</button>

                    </div>
                </div>
            </li>
        </ul>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { MEETINGS, MEETING, GROUPS_INVITATIONS, GROUPS } from '~/public/config';

const notifications = ref([]);
const groupsInvitations = ref([]);
const isVisible = ref(true);
const route = useRoute();
const email = ref('');

const props = defineProps({
    token: {
        type: String,
        required: true
    }
});

const emit = defineEmits(['close', 'notification-accepted']);

// Obtiene las notificaciones pendientes
onMounted(async () => {
    email.value = route.query.email;
    console.log(email.value);

    try {
        const response = await axios.get(MEETINGS, {
            headers: {
                'Authorization': `Bearer ${props.token}`
            }
        });
        console.log(response.data)
        notifications.value = response.data.filter(meeting => meeting.state === 'pending' || meeting.state === 'Pending');
    } catch (err) {
        console.error(err);
    }

    try {
        const response = await axios.get(GROUPS_INVITATIONS, {
            headers: {
                'Authorization': `Bearer ${props.token}`
            }
        });
        console.log(response.data);
        groupsInvitations.value = response.data;
    }
    catch (err) {
        console.error(err);
    }
});

// Responde a una notificación (Aceptar o Rechazar)
const respondToNotification = async (notificationId, event_id, responseState) => {
    try {

        await axios.post(MEETING + notificationId,
            {
                event_id: event_id,
                state: responseState,
            },
            {
                headers: {
                    'Authorization': `Bearer ${props.token}`
                }
            }
        );


        notifications.value = notifications.value.filter(notification => notification.id !== notificationId);
        alert(`Notificación ${responseState === 'Confirmed' ? 'aceptada' : 'rechazada'} exitosamente.`);
    } catch (err) {
        console.error("Error al responder la notificación:", err);
        alert("Hubo un error al procesar tu respuesta.");
    }
};

// Acepta una notificación y la emite al componente principal
const acceptNotification = async (notification) => {
    try {
        await respondToNotification(notification.id, notification.event_id, 'Confirmed');
        const event = {
            id: notification.event_id,
            description: notification.event_description,
            start_time: notification.start_time,
            end_time: notification.end_time,
            state: 'Pending',
            visibility: 'Público',
            showDetails: false
        };
        emit('notification-accepted', event);
    } catch (err) {
        console.error("Error al aceptar la notificación:", err);
    }
};

const acceptGroup = async(groupId) => {
    try {
        const response = await axios.put(GROUPS + groupId + '/users/me', {
            headers: {
                'Authorization': `Bearer ${props.token}`
            }
        });
        groupsInvitations.value = groupsInvitations.value.filter(x => x.id != groupId);
        alert("Se aceptó el grupo con éxito");
        
    } catch (err) {
        alert("Ocurrió un error");
        console.error(err);
    }
}

const removeUserFromGroup = async(groupId) => {
    try {
        const response = await axios.delete(GROUPS + groupId + '/users/' + email.value, {
            headers: {
                'Authorization': `Bearer ${props.token}`
            }
        });
        alert("Se eliminó del grupo con éxito");
        
    } catch (err) {
        alert("Ocurrió un error");
        console.error(err);
    }
}
</script>

<style scoped>
/* Panel de Notificaciones */
.notifications-panel {
    width: 650px;
    max-height: 900px;
    border: 1px solid #ccc;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    padding: 2px;
    overflow-y: auto;
    background-color: #fff;
}

.close-button {
    background: none;
    border: none;
    font-size: 15px;
    cursor: pointer;
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.notification-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-radius: 10px;
    padding: 5px;
    border: 2px solid #ccccccad;
}

.actions {
    display: flex;
    gap: 4px;
}

.accept-button {
    padding: 5px 10px;
    border: none;
    background-color: #28a745;
    color: white;
    border-radius: 10px;
    cursor: pointer;
}

.reject-button {
    padding: 5px 10px;
    border: none;
    background-color: #dc3545;
    color: white;
    border-radius: 10px;
    cursor: pointer;
}
</style>