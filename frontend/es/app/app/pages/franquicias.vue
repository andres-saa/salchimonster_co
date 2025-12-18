<template>
  <div>
    <div v-if="visibleDialog" class="dialog-backdrop">
      <div class="dialog-container mx-4">
        <div class="dialog-content">
          <h4>Hemos recibido tu solicitud y ha quedado registrada con el ID:</h4>
          <p class="dialog-id">{{ lastId }}</p>
          <h4>Pronto te contactaremos</h4>

          <NuxtLink to="/">
            <button class="btn-close-dialog">Listo</button>
          </NuxtLink>
        </div>
      </div>
    </div>

    <!-- Contenedor principal -->
    <div class="franchise-main">
      <!-- Fondo desenfocado -->
      <div class="bg-blur">
        <img src="https://backend.salchimonster.com/read-product-image/600/site-9" alt="" />
      </div>

      <div class="franchise-inner">
        <!-- Sección imágenes (izquierda) -->
        <div class="sedes">
          <img v-for="i in [29, 3, 9, 1]" :key="`left-sede-${i}`" class="sede-img"
            :src="`https://backend.salchimonster.com/read-product-image/600/site-${i}`" alt="Sede Izquierda" />
        </div>

        <!-- Formulario -->
        <div class="form-container">
          <h3><b>Formulario de Pre-Inscripción - Salchimonster Somos Todos</b></h3>
          <br />

          <div class="intro-text">
            <p>
              Salchimonster es una Empresa que nace en el año 2017 a partir de
              una vitrina, siendo este el claro ejemplo que con Disciplina y
              perseverancia los sueños se cumplen. Actualmente contamos con 11
              Imperios, Valle, Bogotá y Medellín, contamos con un Centro de
              distribución para garantizar la estandarización y calidad de los
              productos.
            </p>
            <p>
              Estamos comprometidos con los buenos valores donde nuestros
              mounstruos (empleados) que cada día le meten a Fuego y salen a todo
              por el todo. Hemos logrado reconocimiento Nacional como los
              fundadores de las Salchipapas dejando el nombre de Cali en Alto.
            </p>
            <p>
              Construimos una cadena de restaurantes atractiva, rentable y
              sostenible para inversionistas con el fin de proyectarnos como la
              mejor salchipaperia del país.
            </p>
            <br />
            <p><b>¡¡¡AQUÍ EL MOUNSTRUO SOS VOS!!!</b></p>
            <br />
            <p><b>PAPIII NO ES POR VENDERTE PERO DONDE LLEGAMOS ROMPEMOS</b></p>
          </div>

          <form @submit.prevent="enviarFormulario" class="form-grid">
            <p class="my-2">Nombre Completo:</p>
            <input class="select" type="text" v-model="formulario.nombre" placeholder="Ingrese su nombre completo" />

            <p class="my-2">Teléfono:</p>
            <input class="select" type="tel" v-model="formulario.telefono"
              placeholder="Ingrese su número de teléfono" />

            <p class="my-2">Correo electrónico:</p>
            <input class="select" type="email" v-model="formulario.email" placeholder="Correo electrónico" />

            <p class="my-2">
              ¿Por qué quieres una franquicia de Salchimonster?
            </p>
            <textarea rows="5" class="textarea-razon" v-model="formulario.razon" placeholder="Cuéntanos..."></textarea>

            <p class="my-2">Capacidad de Inversión:</p>
            <select class="select" v-model="formulario.inversion">
              <option disabled value="">Seleccione un rango</option>
              <option v-for="op in opcionesInversion" :key="op.value" :value="op.value">
                {{ op.label }}
              </option>
            </select>

            <p class="my-2">Zona de Interés:</p>
            <select class="select" v-model="formulario.zona">
              <option disabled value="">Seleccione una zona</option>
              <option v-for="zona in zonas" :key="zona.value" :value="zona.value">
                {{ zona.label }}
              </option>
            </select>

            <p class="my-2">¿En qué ciudad se ubicará la franquicia?</p>
            <input class="select" type="text" v-model="formulario.ciudad" placeholder="Ciudad" />

            <p class="my-2">
              ¿Haces parte del sector gastronómico?
            </p>
            <select class="select" v-model="formulario.sectorGastronomico">
              <option disabled value="">Seleccione una opción</option>
              <option v-for="op in opcionesBooleanas" :key="op.value" :value="op.value">
                {{ op.label }}
              </option>
            </select>

            <p class="my-2">
              ¿Participarás en la operación de la franquicia?
            </p>
            <select class="select" v-model="formulario.operacionFranquicia">
              <option disabled value="">Seleccione una opción</option>
              <option v-for="op in opcionesBooleanas" :key="op.value" :value="op.value">
                {{ op.label }}
              </option>
            </select>

            <p class="my-2">Confirma la fuente de tus ingresos:</p>
            <select class="select" v-model="formulario.fuenteIngresos">
              <option disabled value="">Seleccione una opción</option>
              <option v-for="op in opcionesFuenteIngresos" :key="op.value" :value="op.value">
                {{ op.label }}
              </option>
            </select>

            <!-- Botón de envío -->
            <button type="submit" class="btn-submit">
              Enviar
            </button>
          </form>
        </div>

        <!-- Sección imágenes (derecha) -->
        <div class="sedes">
          <img v-for="i in [2, 11, 30, 10]" :key="`right-sede-${i}`" class="sede-img"
            :src="`https://backend.salchimonster.com/read-product-image/600/site-${i}`" alt="Sede Derecha" />
        </div>
      </div>
    </div>
  </div>

</template>

<script setup>
import { ref, computed } from 'vue'
import { URI } from '@/service/conection' // si quieres, puedes reemplazar esto por useRuntimeConfig

const visibleDialog = ref(false)
const last_id = ref(null)

const formulario = ref({
  nombre: '',
  telefono: '',
  email: '',
  razon: '',
  inversion: '',
  zona: '',
  ciudad: '',
  sectorGastronomico: '',
  operacionFranquicia: '',
  fuenteIngresos: '',
  status: 'Pendiente'
})

const opcionesInversion = [
  {
    label: '$250.000.000 - $300.000.000 (1 franquicia)',
    value: '$250.000.000 - $300.000.000 1 franquicia'
  },
  {
    label: '$500.000.000 - $600.000.000 (2 franquicias)',
    value: '$500.000.000 - $600.000.000 2 franquicias'
  },
  {
    label: '$750.000.000 - $900.000.000 (3 franquicias)',
    value: '$750.000.000 - $900.000.000 3 franquicias'
  }
]

const zonas = [
  { label: 'Eje Cafetero', value: 'Eje Cafetero' },
  { label: 'Cundinamarca', value: 'Cundinamarca' },
  { label: 'Caribe', value: 'Caribe' },
  { label: 'Otros', value: 'Otros' }
]

const opcionesBooleanas = [
  { label: 'Sí', value: 'true' },
  { label: 'No', value: 'false' }
]

const opcionesFuenteIngresos = [
  { label: 'Recurso propio', value: 'Propio' },
  { label: 'Recurso prestado', value: 'Prestado' },
  { label: 'Recurso Mixto', value: 'Mixto' }
]

const fieldMapping = {
  nombre: 'name',
  telefono: 'phone',
  email: 'email',
  razon: 'reason',
  inversion: 'investment_capacity',
  zona: 'zone_of_interest',
  ciudad: 'city',
  sectorGastronomico: 'is_in_gastronomic_sector',
  operacionFranquicia: 'will_participate_in_operation',
  fuenteIngresos: 'source_of_income',
  status: 'status'
}

const lastId = computed(() => {
  if (Array.isArray(last_id.value) && last_id.value[0]?.id) {
    return last_id.value[0].id
  }
  if (last_id.value?.id) {
    return last_id.value.id
  }
  return ''
})

const validarFormulario = () => {
  if (!formulario.value.nombre.trim()) {
    alert('Por favor, ingrese su nombre completo.')
    return false
  }
  if (!formulario.value.telefono.trim()) {
    alert('Por favor, ingrese su número de teléfono.')
    return false
  }
  if (
    !formulario.value.email.trim() ||
    !formulario.value.email.includes('@')
  ) {
    alert('Por favor, ingrese un correo electrónico válido.')
    return false
  }
  if (!formulario.value.razon.trim()) {
    alert('Por favor, explique su motivo de inversión.')
    return false
  }
  if (!formulario.value.inversion) {
    alert('Por favor, seleccione un rango de inversión.')
    return false
  }
  if (!formulario.value.zona) {
    alert('Por favor, seleccione una zona.')
    return false
  }
  if (!formulario.value.ciudad.trim()) {
    alert('Por favor, describa la ciudad.')
    return false
  }
  if (!formulario.value.sectorGastronomico) {
    alert('Por favor, indique si forma parte del sector gastronómico.')
    return false
  }
  if (!formulario.value.operacionFranquicia) {
    alert('Por favor, indique si participará en la operación de la franquicia.')
    return false
  }
  if (!formulario.value.fuenteIngresos) {
    alert('Por favor, seleccione una fuente de ingresos.')
    return false
  }
  return true
}

const toBool = (val) => val === true || val === 'true'

const enviarFormulario = async () => {
  if (!validarFormulario()) return

  const jsonData = {
    [fieldMapping.nombre]: formulario.value.nombre,
    [fieldMapping.telefono]: formulario.value.telefono,
    [fieldMapping.email]: formulario.value.email,
    [fieldMapping.razon]: formulario.value.razon,
    [fieldMapping.inversion]: formulario.value.inversion,
    [fieldMapping.zona]: formulario.value.zona,
    [fieldMapping.ciudad]: formulario.value.ciudad,
    [fieldMapping.sectorGastronomico]: toBool(
      formulario.value.sectorGastronomico
    ),
    [fieldMapping.operacionFranquicia]: toBool(
      formulario.value.operacionFranquicia
    ),
    [fieldMapping.fuenteIngresos]: formulario.value.fuenteIngresos,
    [fieldMapping.status]: 'Pendiente'
  }

  try {
    const res = await fetch(`${URI}/create_franquicia_request`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(jsonData)
    })

    if (!res.ok) {
      throw new Error('Error al enviar la solicitud')
    }

    const data = await res.json()
    last_id.value = data
    visibleDialog.value = true
  } catch (err) {
    console.error(err)
    alert('Ocurrió un error al enviar la solicitud. Intenta de nuevo.')
  }
}
</script>

<style scoped>
/* ====== Fondo desenfocado ====== */
.bg-blur {
  position: fixed;
  z-index: -1;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: black;
  overflow: hidden;
}

.bg-blur img {
  object-fit: cover;
  opacity: 0.4;
  width: 120vw;
  height: 100%;
  filter: blur(12px);
}

/* ====== Diálogo ====== */
.dialog-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.dialog-container {
  width: 30rem;
  max-width: 95vw;
  background-color: white;
  border-radius: 0.75rem;
  overflow: hidden;
}

.dialog-content {
  height: auto;
  color: black;
  background-color: white;
  display: flex;
  flex-direction: column;
  justify-content: end;
  align-items: center;
  padding: 1rem;
  gap: 0.5rem;
}

.dialog-id {
  font-size: 3rem;
  text-align: center;
}

.btn-close-dialog {
  font-weight: bold;
  margin: 0 auto;
  padding: 0.5rem 1.5rem;
  border-radius: 999px;
  border: none;
  cursor: pointer;
  background-color: #0ea5e9;
  color: white;
}

/* ====== Contenedor principal ====== */
.franchise-main {
  width: 100%;
  min-height: 100vh;
}

/* Contenedor interno */
.franchise-inner {
  width: 100%;
  max-width: 1600px;
  margin: auto;
  align-items: flex-start;
  display: flex;
  padding: 1rem 0;
  gap: 1rem;
}

/* Sección de imágenes */
.sedes {
  display: flex;
  flex-direction: column;
  width: 20%;
  gap: 1rem;
}

.sede-img {
  aspect-ratio: 4 / 3;
  width: 100%;
  object-fit: cover;
  border-radius: 0.5rem;
}

/* Contenedor del formulario */
.form-container {
  width: 60%;
  background-color: white;
  border-radius: 0.5rem;
  padding: 1.5rem;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  margin: 0.5rem;
}

/* Texto introductorio */
.intro-text p {
  margin-bottom: 0.5rem;
  text-align: justify;
  width: 100%;
}

/* ====== Formulario ====== */
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
  align-items: center;
  justify-content: end;
}

/* Textarea de razón */
.textarea-razon {
  resize: none;
  width: 100%;
  padding: 0.5rem;
  border-radius: 0.375rem;
  border: 1px solid #d4d4d4;
  font-size: 0.95rem;
}

.select {
  width: 100%;
  padding: 0.5rem;
  border-radius: 0.375rem;
  border: 1px solid #d4d4d4;
  font-size: 0.95rem;
  outline: none;
}

.select:focus,
.textarea-razon:focus {
  border-color: #0ea5e9;
}

/* Botón de envío */
.btn-submit {
  margin-top: 1rem;
  border: none;
  grid-column: 2 / 3;
  padding: 0.75rem 1.5rem;
  border-radius: 999px;
  background-color: #22c55e;
  color: white;
  font-weight: 600;
  cursor: pointer;
  justify-self: flex-end;
}

/* ====== Responsividad ====== */
@media (max-width: 1100px) {
  .form-grid {
    grid-template-columns: repeat(1, 1fr);
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    align-items: stretch;
  }
}

@media (max-width: 1100px) {
  .sedes {
    display: none;
  }

  .form-container {
    width: 100%;
  }
}
</style>
