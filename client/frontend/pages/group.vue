<template>
    <div class="logged-user">
        <span>Bienvenido, {{ name }}</span>
    </div>
    <div class="group-page">
        <h2>Mis grupos</h2>
        <div class="grupos">
            <div v-for="group in groups" :key="group.id" class="grupo-card">
                <div class="grupo-header">
                    <h3>{{ group.name }}</h3>
                    <div class="grupo-actions">
                        <button @click="toggleMembers(group.id)" class="btn">Ver integrantes</button>
                        <button @click="deleteGroup(group.id)" class="btn btn-danger">Eliminar grupo</button>
                    </div>
                </div>

                <div v-if="activeGroup === group.id" class="grupo-details">
                    <h4>Integrantes:</h4>
                    <ul>
                        <li v-for="member in usuarios" :key="member.id" class="member-item">
                            {{ member }}
                            <button @click="removeUser(group.id, member.id)"
                                class="btn btn-sm btn-danger">Eliminar</button>
                        </li>
                    </ul>
                    <form @submit.prevent="addUser(group.id)" class="add-user-form">
                        <input type="text" v-model="newUserEmail" placeholder="Email del usuario" required
                            class="input" />
                        <template v-if="group.hierarchy">
                            <input type="number" v-model="newUserHierarchy" placeholder="Heraquia del usuario" required
                                min="0" class="input" />
                        </template>
                        <button type="submit" class="btn btn-sm">Agregar usuario</button>
                    </form>
                </div>
            </div>
        </div>

        <button @click="showForm = true" class="btn btn-primary">Crear un nuevo grupo</button>

        <form v-if="showForm" class="create-group-form" @submit.prevent="createGroup">
            <h1>Crear Grupo</h1>
            <div class="entrada">
                <label for="name">Nombre del Grupo:</label>
                <input type="text" id="name" v-model="group.name" required class="input" />
            </div>
            <div class="entrada">
                <label for="hierarchy">¿Tiene Jerarquía?</label>
                <input type="checkbox" id="hierarchy" v-model="hasHierarchy" />
            </div>
            <div v-if="hasHierarchy">
                <div class="entrada">
                    <label for="creatorNumber">Número del Creador:</label>
                    <input type="number" id="creatorNumber" v-model="group.hierarchy" min="0" required class="input" />
                </div>
            </div>
            <div class="form-actions">
                <button type="submit" class="btn btn-primary">Crear</button>
                <button type="button" @click="quitarForm" class="btn btn-secondary">Cancelar</button>
            </div>
        </form>

    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { GROUPS, USERS_ENDPOINT } from '~/public/config';

const token = ref('');
const name = ref('');
const groups = ref([]);
const activeGroup = ref(null); // Para controlar el grupo activo
const newUserEmail = ref(''); // Para almacenar el nombre del nuevo usuario
const newUserHierarchy = ref('');
const route = useRoute();
const router = useRouter();
const usuarios = ref([]);

const group = ref({
    name: '',
    hierarchy: 0,
});

const hasHierarchy = ref(false);
const showForm = ref(false);

const toggleMembers = async (groupId) => {
    activeGroup.value = activeGroup.value === groupId ? null : groupId;
    usuarios.value = await getUsuarios(groupId);
};

const addUser = async (groupId) => {
    if (!newUserEmail.value.trim()) return;

    try {
        const response = await axios.post(`${GROUPS}${groupId}/users/${newUserEmail.value}/level/${newUserHierarchy.value}`, {
            headers: { 'Authorization': `Bearer ${token.value}` },
        });

        newUserEmail.value = '';
        newUserHierarchy.value = '';
        alert('Usuario agregado con exito')
        console.log(response);
    } catch (err) {
        console.error(err);
    }
};

const removeUser = async (groupId, userEmail, hierarchy) => {
    try {
        await axios.delete(`${GROUPS}/${groupId}/user/${userEmail}/level/${hierarchy}`, {
            headers: { 'Authorization': `Bearer ${token.value}` },
        });
        const group = groups.value.find(g => g.id === groupId);
        group.members = group.members.filter(member => member.id !== userEmail);
    } catch (err) {
        console.error(err);
    }
};

const deleteGroup = async (groupId) => {
    try {
        await axios.delete(GROUPS + 'group_id/' + groupId, {
            headers: { 'Authorization': `Bearer ${token.value}` },
        });
        groups.value = groups.value.filter(group => group.id !== groupId);
    } catch (err) {
        console.error(err);
    }
};

const getUsuarios = async (idGrupo) => {
    try {
        const response = await axios.get(GROUPS + idGrupo + '/users', {
            headers: { 'Authorization': `Bearer ${token.value}` },
        });
        return response.data;
    }
    catch (err) {
        console.error(err);
    }
    return [];
}

const createGroup = async () => {
    try {
        const response = await axios.post(GROUPS + 'hierarchy/' + group.value.hierarchy, {
            name: group.value.name,
            hierarchy: (group.value.name !== 0)
        }, {
            headers: { 'Authorization': `Bearer ${token.value}` },
        });
        groups.value.push(response.data);
        quitarForm();
    } catch (err) {
        console.error(err);
    }
};

const quitarForm = () => {
    showForm.value = false;
    group.value.name = '';
    group.value.hierarchy = 0;
    hasHierarchy.value = false;
};

onMounted(async () => {
    token.value = route.query.token;

    name.value = route.query.name;

    try {
        const response = await axios.get(GROUPS + 'users', {
            headers: { 'Authorization': `Bearer ${token.value}` },
        });

        groups.value = response.data;

    } catch (err) {
        console.error(err);
    }
});
</script>

<style scoped>
.group-page {
    width: 90%;
    padding: 5%;
    border: 1px solid #ccc;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

h1,
h2,
h3,
h4 {
    text-align: center;
}

.grupo-card {
    border: 1px solid #ddd;
    padding: 5%;
    margin-bottom: 10px;
    border-radius: 10px;
    background-color: #f9f9f9;
}

.grupo-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.grupo-actions {
    display: flex;
    gap: 10px;
}

.grupo-details {
    margin-top: 10px;
}

.member-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 5px 0;
}

.add-user-form {
    display: flex;
    gap: 10px;
    margin-top: 10px;
}

.logged-user {
    position: absolute;
    top: 10px;
    right: 10px;
    background-color: #f0f0f0;
    padding: 8px 12px;
    border-radius: 5px;
    font-size: 14px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.entrada {
    display: flex;
    flex-direction: column;
    margin-bottom: 10px;
}

.input {
    width: 100%;
    padding: 10px;
    margin-top: 5px;
    border: 1px solid #ddd;
    border-radius: 5px;
}

button {
    padding: 10px 15px;
    border: none;
    border-radius: 5px;
    cursor: pointer;
}

.btn {
    background-color: #007bff;
    color: white;
}

.btn-sm {
    padding: 5px 10px;
    font-size: 0.9em;
}

.btn-danger {
    background-color: #dc3545;
    color: white;
}

.btn-primary {
    background-color: #007bff;
    color: white;
}

.btn-secondary {
    background-color: #6c757d;
    color: white;
}

button:disabled {
    background-color: #aaa;
    cursor: not-allowed;
}

.create-group-form {
    border: 1px solid #ddd;
    padding: 20px;
    border-radius: 10px;
    margin-top: 20px;
}

.form-actions {
    display: flex;
    justify-content: space-between;
    gap: 10px;
}
</style>