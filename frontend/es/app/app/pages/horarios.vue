<template>
  <section class="horarios-section">
    <h4 class="title">Horarios de Domicilios</h4>

    <div style="padding: 2rem 1rem;">
<div class="horarios-card">
      <!-- LOADING -->
      <div v-if="pending" class="info-row info-row--loading">
        <Icon name="mdi:clock-outline" class="info-row__icon" />
        <span>Cargando horarios...</span>
      </div>

      <!-- ERROR -->
      <div v-else-if="error" class="info-row info-row--error">
        <Icon name="mdi:alert-circle-outline" class="info-row__icon" />
        <span>Hubo un problema al cargar los horarios. Intenta de nuevo más tarde.</span>
      </div>

      <!-- SIN DATOS -->
      <div v-else-if="!horario || horario.length === 0" class="info-row info-row--empty">
        <Icon name="mdi:calendar-remove-outline" class="info-row__icon" />
        <span>No hay horarios configurados por el momento.</span>
      </div>

      <!-- TABLA -->
      <div v-else class="table-wrapper">
        <table class="schedule-table">
          <thead>
            <tr>
              <th>Día</th>
              <th>
                <span class="th-icon">
                  <Icon name="mdi:door-open" class="th-icon__icon" />
                  Apertura
                </span>
              </th>
              <th>
                <span class="th-icon">
                  <Icon name="mdi:door-closed" class="th-icon__icon" />
                  Cierre
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in horario" :key="item.id">
              <td class="col-dia">
                {{ dias[item.day_of_week - 1] }}
              </td>
              <td>{{ formatearHora(item.opening_time) }}</td>
              <td>{{ formatearHora(item.closing_time) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    </div>

    <!-- <Index></Index> -->
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { URI } from '@/service/conection'

const dias = [
  'Domingo',
  'Lunes',
  'Martes',
  'Miércoles',
  'Jueves',
  'Viernes',
  'Sábado'
]

// Pedimos los horarios con useFetch (Nuxt nativo)
const {
  data: horarioRaw,
  pending,
  error
} = await useFetch(`${URI}/site-schedule/31/`)

const horario = computed(() => horarioRaw.value || [])

// Recibe un string "HH:MM:SS" o "HH:MM" y lo pasa a formato 12h
function formatearHora(horaStr) {
  if (!horaStr || typeof horaStr !== 'string') return horaStr

  const [horaStrNum, minStr] = horaStr.split(':')
  let hora = Number(horaStrNum)
  const minutos = Number(minStr || 0)

  if (Number.isNaN(hora) || Number.isNaN(minutos)) return horaStr

  const ampm = hora >= 12 ? 'PM' : 'AM'
  hora = hora % 12
  hora = hora || 12

  return `${hora}:${minutos.toString().padStart(2, '0')} ${ampm}`
}
</script>

<style scoped>
.horarios-section {
  /* padding: 3rem 1rem 4rem; */
}

.title {
  margin: 0;
  /* font-family: 'Luckiest Guy', cursive; */
  letter-spacing: 0.1cap;
  width: 100%;
  font-weight: bold;
  text-align: center;
  margin: 2rem 0;
  margin-bottom: 0;
  font-size: 2rem;
  color: var(--primary-color);
  transition: transform 0.3s ease, text-shadow 0.3s ease;
}



.title--secondary {
  margin-top: 3rem;
  font-size: 1.8rem;
}

.horarios-card {
  max-width: 500px;
  margin: 1rem auto;
  padding: 1rem 1.25rem 1.5rem;
  border-radius: 1.25rem;
  background: #ffffff;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.15);
  border: 1px solid rgba(148, 163, 184, 0.4);
}

/* Mensajes de info / error / vacío */
.info-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.9rem;
  padding: 0.7rem 0.8rem;
  border-radius: 0.75rem;
}

.info-row__icon {
  font-size: 1.4rem;
}

.info-row--loading {
  background-color: #e0f2fe;
  color: #0c4a6e;
}

.info-row--loading .info-row__icon {
  color: #0284c7;
}

.info-row--error {
  background-color: #fee2e2;
  color: #991b1b;
}

.info-row--error .info-row__icon {
  color: #ef4444;
}

.info-row--empty {
  background-color: #f3f4f6;
  color: #4b5563;
}

.info-row--empty .info-row__icon {
  color: #9ca3af;
}

/* Tabla */
.table-wrapper {
  overflow-x: auto;
  margin-top: 0.5rem;
}

.schedule-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.schedule-table thead {
  background: linear-gradient(135deg, #fef2f2, #fee2e2);
}

.schedule-table th,
.schedule-table td {
  padding: 0.6rem 0.75rem;
  text-align: left;
  white-space: nowrap;
}

.schedule-table th {
  font-weight: 600;
  font-size: 0.85rem;
  color: #7f1d1d;
  border-bottom: 1px solid rgba(248, 113, 113, 0.4);
}

.schedule-table td {
  color: #111827;
  border-bottom: 1px solid #e5e7eb;
}

.schedule-table tbody tr:nth-child(odd) {
  background-color: #f9fafb;
}

.schedule-table tbody tr:hover {
  background-color: #fee2e2;
  transition: background-color 0.15s ease;
}

/* Día */
.col-dia {
  font-weight: 600;
}

/* Cabezal con icono */
.th-icon {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.th-icon__icon {
  font-size: 1.1rem;
}

/* Responsive */
@media (max-width: 600px) {
  .title {
    font-size: 1.6rem;
  }

  .title--secondary {
    font-size: 1.4rem;
  }

  .horarios-card {
    padding: 0.9rem 1rem 1.3rem;
    border-radius: 1rem;
  }

  .schedule-table th,
  .schedule-table td {
    padding: 0.5rem 0.6rem;
  }
}
</style>
