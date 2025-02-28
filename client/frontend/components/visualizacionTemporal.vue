<template>
    <div class="timeline-container">
      <h2>Visualización de Intervalos de Eventos y Espacios Vacíos</h2>
  
      <!-- Sección para mostrar la línea de tiempo visual mejorada -->
      <div class="timeline-wrapper">
        <div class="timeline-header">
          <div v-for="hour in 25" :key="hour" class="timeline-hour">
            {{ formatTime(hour - 1) }}
          </div>
        </div>
        <div class="timeline">
          <div
            v-for="(interval, index) in processedIntervals"
            :key="index"
            :class="['interval', interval.type]"
            :style="{ width: interval.width + '%' }"
          >
            <span v-if="interval.type === 'event'" class="event-label">{{ interval.event.name }}</span>
            <span v-if="interval.type === 'empty'" class="empty-label">Intervalo vacío</span>
          </div>
        </div>
      </div>
  
      <!-- Sección para mostrar los detalles de los eventos -->
      <div class="event-details">
        <h3>Detalles de los Eventos</h3>
        <ul>
          <li v-for="event in events" :key="event.name" class="event-item">
            <strong>{{ event.name }}</strong>: {{ formatTime(event.start) }} - {{ formatTime(event.end) }}
          </li>
        </ul>
      </div>
  
      <!-- Sección para mostrar los intervalos vacíos -->
      <div class="empty-intervals">
        <h3>Intervalos Vacíos</h3>
        <ul>
          <li v-for="(interval, index) in emptyIntervals" :key="index" class="interval-item">
            {{ formatTime(interval.start) }} - {{ formatTime(interval.end) }}
          </li>
        </ul>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, computed } from 'vue';
  
  // Lista de eventos: Cada evento tiene un nombre, inicio y final (horas del día).
  const events = ref([
    { name: 'Evento 1', start: 9, end: 11 },
    { name: 'Evento 2', start: 13, end: 14 },
    { name: 'Evento 3', start: 16, end: 18 },
  ]);
  
  // Calcular los intervalos vacíos entre los eventos.
  const emptyIntervals = computed(() => {
    const intervals = [];
    let currentTime = 0;
  
    events.value.forEach(event => {
      if (event.start > currentTime) {
        intervals.push({
          start: currentTime,
          end: event.start,
        });
      }
      currentTime = event.end;
    });
  
    if (currentTime < 24) {
      intervals.push({
        start: currentTime,
        end: 24,
      });
    }
  
    return intervals;
  });
  
  // Procesar los intervalos y generar las secciones ocupadas y vacías.
  const processedIntervals = computed(() => {
    const intervals = [];
    let currentTime = 0;
  
    events.value.forEach(event => {
      if (event.start > currentTime) {
        intervals.push({
          type: 'empty',
          width: (event.start - currentTime) * (100 / 24),
        });
      }
  
      intervals.push({
        type: 'event',
        width: (event.end - event.start) * (100 / 24),
        event,
      });
  
      currentTime = event.end;
    });
  
    if (currentTime < 24) {
      intervals.push({
        type: 'empty',
        width: (24 - currentTime) * (100 / 24),
      });
    }
  
    return intervals;
  });
  
  // Función para formatear la hora.
  const formatTime = (hour) => {
    return hour < 10 ? `0${hour}:00` : `${hour}:00`;
  };
  </script>
  
  <style scoped>
  .timeline-container {
    width: 90%;
    margin: 0 auto;
    padding: 30px;
    border-radius: 20px;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
    background: linear-gradient(135deg, #f0f4ff, #e8f7f3);
    transition: all 0.3s ease-in-out;
  }
  
  h2, h3 {
    text-align: center;
    font-family: 'Roboto', sans-serif;
    color: #333;
  }
  
  .event-details, .empty-intervals {
    margin-top: 30px;
    background-color: #fff;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  }
  
  .event-item, .interval-item {
    margin-bottom: 10px;
    font-size: 1.1rem;
    color: #4a4a4a;
  }
  
  ul {
    list-style-type: none;
    padding-left: 0;
  }
  
  .interval-item {
    color: #ff6f61;
  }
  
  /* Línea de tiempo visual mejorada */
  .timeline-wrapper {
    margin-top: 25px;
  }
  
  .timeline-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
    padding: 0 5px;
  }
  
  .timeline-hour {
    flex: 1;
    text-align: center;
    font-size: 0.8rem;
    color: #666;
  }
  
  .timeline {
    display: flex;
    width: 100%;
    height: 80px;
    border-radius: 15px;
    overflow: hidden;
    margin-top: 10px;
    box-shadow: 0 6px 15px rgba(0, 0, 0, 0.1);
    background-color: #f3f3f3;
    position: relative;
  }
  
  .interval {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    text-align: center;
    padding: 10px;
    font-family: 'Roboto', sans-serif;
    font-weight: bold;
    box-sizing: border-box;
    transition: background-color 0.3s ease, color 0.3s ease;
    position: relative;
  }
  
  .interval.event {
    background: linear-gradient(135deg, #007bff, #0a58ca);
    color: #fff;
    border-right: 2px solid rgba(255, 255, 255, 0.5);
  }
  
  .interval.event:hover {
    background: linear-gradient(135deg, #0056b3, #004494);
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
  }
  
  .interval.empty {
    background: linear-gradient(135deg, #e0e0e0, #c8c8c8);
    color: #666;
  }
  
  .event-label {
    font-size: 1rem;
    padding: 5px;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
  }
  
  .empty-label {
    font-size: 0.9rem;
    color: #444;
  }
  
  /* Indicadores de Tiempo */
  .timeline-hour {
    border-right: 1px solid #ddd;
    padding-right: 5px;
  }
  
  .timeline-hour:last-child {
    border-right: none;
  }
  </style>
  