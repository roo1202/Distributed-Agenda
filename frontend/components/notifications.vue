<template>
    <div class="notifications-panel" :class="{ visible: isVisible, hidden: !isVisible }">
        <div class="header">
            <h2>Notificaciones</h2>
            <button class="close-button" @click="$emit('close')">❌</button>
        </div>
        <ul>
            <li v-for="notification in notifications" :key="notification.id">
                {{ notification.message }}
            </li>
        </ul>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { MEETINGS } from '~/public/config';

const notifications = ref([]);
const isVisible = ref(true); // Controla la visibilidad

const props = defineProps({
    token : {
        type: String,
        required: true
    }
});

onMounted(async () => {
    try {
        const response = await axios.get(MEETINGS,{
            headers: {
                'Authorization': `Bearer ${props.token}`
            }
        });
        notifications.value = response.data;
    } catch (err) {
        console.log(err);
    }
});
</script>

<style scoped>
/* Panel de Notificaciones */
.notifications-panel {
    width: 150px;
    height: 100%;
    border: 1px solid #ccc;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    padding: 5px;
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
</style>
