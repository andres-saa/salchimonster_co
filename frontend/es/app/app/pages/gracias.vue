<template>
  <div class="page-container">
    <div v-if="order?.order_id" class="receipt-card">
      
      <header class="receipt-header">
        <h2 class="client-name">
          🤩{{ clienteNombresUpper }} {{ clienteApellidosUpper }}🤩
        </h2>
        <p class="thank-you-msg">🔥 ¡MUCHAS GRACIAS POR TU COMPRA! 🔥</p>
      </header>

      <div class="receipt-body">
        
        <div class="status-section">
          <span v-if="order.responsible_id" class="badge badge-success">Pago autorizado</span>
          <span v-if="order.responsible_id" class="badge badge-success">{{ order.name }}</span>
          
          <div class="order-meta">
            <p class="order-id">ID: {{ order.order_id }}</p>
            <p class="order-user">{{ order.user_name }} {{ order.second_name }} {{ order.first_last_name }} {{ order.second_last_name }}</p>
            <div class="order-dates">
              <span><b>Fecha:</b> {{ fechaISO }}</span>
              <span><b>Hora:</b> {{ horaISO }}</span>
            </div>
          </div>
        </div>

        <div class="products-table">
          <div class="table-header">
            <span>PRODUCTOS</span>
            <span class="text-right">TOTAL</span>
          </div>

          <div class="table-rows">
            <div v-for="(product, idx) in order.pe_json?.listaPedidos || []" :key="idx" class="product-row-group">
              
              <div class="product-row">
                <div class="product-info">
                  <span v-if="order.site_id === 32">
                    <b>({{ product.pedido_cantidad }} kg)</b> {{ product.pedido_nombre_producto }}
                    <small>({{ product.pedido_cantidad / product.presentacion }} {{ product.presentation_unit_measure }})</small>
                  </span>
                  <span v-else>
                    <b>({{ product.pedido_cantidad }})</b> {{ product.pedido_nombre_producto }}
                  </span>
                </div>
                <div class="product-price">
                  {{ formatoPesosColombianos((product.pedido_base_price ?? product.pedido_precio ?? 0) * (product.pedido_cantidad ?? 0)) }}
                </div>
              </div>

              <div v-if="product.lista_productocombo?.length > 0" class="combo-details">
                <p class="combo-label">COMBO INCLUYE</p>
                <p v-for="(i, k) in product.lista_productocombo" :key="k" class="combo-item">
                  -- <b>{{ i.pedido_cantidad }}</b> {{ i.pedido_nombre }}
                </p>
              </div>

              <div v-for="(mod, j) in product.modificadorseleccionList || []" :key="j" class="modifier-row">
                <span class="modifier-name">
                  - ({{ product.pedido_cantidad }}) <b>{{ mod.modificadorseleccion_cantidad }}</b> {{ mod.modificadorseleccion_nombre }}
                </span>
                <span class="modifier-price">
                  {{ formatoPesosColombianos((mod.pedido_precio ?? 0) * (mod.modificadorseleccion_cantidad ?? 0) * (product.pedido_cantidad ?? 0)) }}
                </span>
              </div>
              
              <div class="separator"></div>
            </div>
          </div>
        </div>

        <div class="totals-section">
          <div class="total-row">
            <span>Subtotal</span>
            <b>{{ formatoPesosColombianos(subtotal) }}</b>
          </div>
          
          <div v-if="descuento > 0" class="total-row discount-text">
            <span>Descuento</span>
            <b>- <span class="strike">{{ formatoPesosColombianos(descuento) }}</span></b>
          </div>

          <div class="total-row">
            <span>Domicilio</span>
            <b>{{ formatoPesosColombianos(envio) }}</b>
          </div>

          <div class="total-row final-total">
            <span>Total</span>
            <span>{{ formatoPesosColombianos(pagocon) }}</span>
          </div>
        </div>

        <div v-if="isLoggedIn" class="section-block admin-link-block">
            <div class="section-title dark">Link de Pago (Admin)</div>
            <div class="link-control">
                <input type="text" :value="paymentLink" readonly class="link-input" />
                <button @click="copyPaymentLink" class="btn-copy">
                    <i class="pi" :class="linkCopied ? 'pi-check' : 'pi-copy'"></i>
                    {{ linkCopied ? 'Copiado' : 'Copiar' }}
                </button>
            </div>
        </div>
        <div class="section-block">
          <div class="section-title dark">Notas</div>
          <div class="notes-box">
            {{ (order.order_notes || '').toLowerCase() }}
          </div>
        </div>

        <div class="section-block">
          <div class="section-title dark">Cliente</div>
          <div class="info-grid">
            <div class="info-item">
              <span class="label">Nombre</span>
              <span class="value">{{ order.user_name }} {{ order.second_name }} {{ order.first_last_name }} {{ order.second_last_name }}</span>
            </div>
            
            <div v-if="order.site_id === 32" class="info-item">
              <span class="label">Cédula / NIT</span>
              <span class="value">{{ order.cedula_nit }}</span>
            </div>

            <div class="info-item">
              <span class="label">Método de entrega</span>
              <span class="value">{{ order.order_type }}</span>
            </div>

            <div v-if="order.site_id === 32" class="info-item">
              <span class="label">Fecha entrega</span>
              <span class="value">{{ order.pe_json?.delivery?.delivery_horaentrega }}</span>
            </div>

            <div v-if="order.placa" class="info-item">
              <span class="label">Placa</span>
              <span class="value">{{ order.placa }}</span>
            </div>

            <div class="info-item">
              <span class="label">Teléfono</span>
              <span class="value">{{ order.user_phone }}</span>
            </div>

            <div v-if="order.site_id === 32" class="info-item">
              <span class="label">Correo</span>
              <span class="value">{{ order.email }}</span>
            </div>

            <div v-if="order.order_type !== 'Pasar a recoger'" class="info-item">
              <span class="label">Dirección</span>
              <span class="value capitalize">{{ (order.user_address || '').toLowerCase() }}</span>
            </div>

            <div class="info-item">
              <span class="label">Método de pago</span>
              <span class="value capitalize">{{ (order.payment_method || '').toLowerCase() }}</span>
            </div>
          </div>
        </div>

        <div v-if="route.query?.ref_payco" class="section-block epayco-block">
          <h4>Información de pago</h4>
          <div class="info-grid two-cols">
            <div class="info-item"><span class="label">Ref. Comercio</span><span class="value">{{ epayco_data?.x_id_factura }}</span></div>
            <div class="info-item"><span class="label">Ref. ePayco</span><span class="value">{{ epayco_data?.x_ref_payco }}</span></div>
            <div class="info-item"><span class="label">Banco</span><span class="value">{{ epayco_data?.x_bank_name }}</span></div>
            <div class="info-item"><span class="label">Estado</span><span class="value">{{ epayco_data?.x_transaction_state }}</span></div>
            <div class="info-item"><span class="label">Total</span><span class="value">{{ formatoPesosColombianos(epayco_data?.x_amount) }}</span></div>
          </div>
        </div>

      </div>

      <footer class="receipt-footer">
        <NuxtLink :to="`/rastrear?order_id=${order.order_id}`" class="full-width">
          <button class="btn btn-warning full-width">PUEDES RASTREARLO AQUÍ</button>
        </NuxtLink>
        
        <a v-if="showBtnTransferencia" :href="whatsappUrlTransferencia" target="_blank" class="full-width">
          <button class="btn btn-whatsapp full-width pulse-anim">
            <i class="pi pi-whatsapp"></i> REALIZAR TRANSFERENCIA
          </button>
        </a>
        
        <NuxtLink to="/" class="full-width">
          <button class="btn btn-outline-danger full-width">
            <i class="pi pi-arrow-left"></i> VOLVER AL MENÚ
          </button>
        </NuxtLink>
      </footer>

    </div>

    <div v-else class="loading-state">
      <div class="spinner"></div>
      <h2>Cargando tu pedido...</h2>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { URI } from "~/service/conection"; 
// Importamos el store de usuario para verificar login
import { useUserStore } from '#imports'; 

const route = useRoute();
const user = useUserStore();

// Estado
const order = ref(null);
const sites = ref([]); 
const epayco_data = ref({});
const linkCopied = ref(false); // Estado visual para el botón de copiar

/* ================= UTILS ================= */
const formatoPesosColombianos = (n) => {
  const v = Number(n ?? 0);
  return v.toLocaleString("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });
};

/* ================= COMPUTED PROPERTIES ================= */

// Verificar si está logueado
const isLoggedIn = computed(() => {
  return !!user.user?.token && !!user.user?.inserted_by;
});

// Generar link de pago
const paymentLink = computed(() => {
    if(!order.value?.order_id) return '';
    return `https://salchimonster.com/pagar/${order.value.order_id}`;
});

// Copiar link al portapapeles
const copyPaymentLink = async () => {
    try {
        await navigator.clipboard.writeText(paymentLink.value);
        linkCopied.value = true;
        // Restaurar botón después de 2 segundos
        setTimeout(() => {
            linkCopied.value = false;
        }, 2000);
    } catch (err) {
        console.error('Error al copiar el link:', err);
    }
};

// Datos Cliente
const clienteNombresUpper = computed(() => (order.value?.pe_json?.cliente?.cliente_nombres || "").toUpperCase());
const clienteApellidosUpper = computed(() => (order.value?.pe_json?.cliente?.cliente_apellidos || "").toUpperCase());

// Fecha y Hora
const fechaISO = computed(() => (order.value?.latest_status_timestamp || "").split("T")?.[0] || "");
const horaISO = computed(() => (order.value?.latest_status_timestamp || "").split("T")?.[1]?.split(":")?.slice(0, 2)?.join(":") || "");

// Totales Financieros
const envio = computed(() => Number(order.value?.pe_json?.delivery?.delivery_costoenvio ?? 0));
const pagocon = computed(() => Number(order.value?.pe_json?.delivery?.delivery_pagocon ?? 0));
const descuento = computed(() => Number(order.value?.pe_json?.delivery?.total_descuento ?? 0));
const subtotal = computed(() => pagocon.value + descuento.value - envio.value);

// Lógica de Teléfono Dinámica
const targetPhone = computed(() => {
  if (!order.value?.site_id || sites.value.length === 0) return null;
  const currentSite = sites.value.find(s => s.site_id === order.value.site_id);
  if (!currentSite || !currentSite.site_phone) return null;
  const rawPhone = String(currentSite.site_phone);
  const cleanPhone = rawPhone.replace(/\D/g, ''); 
  return cleanPhone.length > 6 ? cleanPhone : null;
});

// Mensajes para WhatsApp
const textTransferencia = computed(() => {
  const c = order.value?.pe_json?.cliente || {};
  const lista = order.value?.pe_json?.listaPedidos || [];
  
  const productos = lista.map((p) => {
    if (order.value?.site_id === 32) {
      const cantidad = p?.pedido_cantidad || 0;
      const presentacion = p?.presentacion || 1;
      const unidad = p?.presentation_unit_measure || "";
      return `*(${cantidad} kilos)* de ${p?.pedido_nombre_producto || ""} (${cantidad / presentacion} ${unidad})`;
    }
    return `*(${p?.pedido_cantidad || 0})* ${p?.pedido_nombre_producto || ""}`;
  }).join("\n");

  return `Hola soy *${(c.cliente_nombres || "").toUpperCase()} ${(c.cliente_apellidos || "").toUpperCase()}* 🤗 acabo de hacer el siguiente pedido en la página web.
${productos ? "\n" + productos + "\n" : ""}
El número de la orden es *#${order.value?.order_id || ""}*.

*Escribo para Realizar la Transferencia* 🙏`;
});

const whatsappUrlTransferencia = computed(() => {
  if (!targetPhone.value) return "#"; 
  const baseUrl = "https://api.whatsapp.com/send";
  const urlParams = new URLSearchParams({ phone: targetPhone.value, text: textTransferencia.value });
  return `${baseUrl}?${urlParams.toString()}`;
});

const showBtnTransferencia = computed(() => {
  const isTransfer = Number(order.value?.payment_method_id) === 6;
  const hasPhone = !!targetPhone.value;
  return isTransfer && hasPhone;
});

/* ================= API FETCH ================= */
const loadOrder = async () => {
  const order_id = route.query?.order_id;
  if (!order_id) return;

  try {
    const response = await fetch(`${URI}/order-by-id/${order_id}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);
    const data = await response.json();
    order.value = data || null;
  } catch (e) {
    console.error("Error al obtener la orden:", e);
    order.value = null;
  }
};

const loadSites = async () => {
  try {
    const response = await fetch('https://backend.salchimonster.com/sites', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!response.ok) throw new Error("Error al cargar sedes");
    sites.value = await response.json();
  } catch (e) {
    console.error("Error cargando sites:", e);
  }
};

const loadEpaycoDataIfAny = () => {
  if (route.query?.ref_payco) {
      epayco_data.value = {
          x_id_factura: route.query?.x_id_factura,
          x_ref_payco: route.query?.x_ref_payco,
          x_transaction_state: route.query?.x_transaction_state,
          x_bank_name: route.query?.x_bank_name,
          x_amount: route.query?.x_amount,
      }
  }
};

/* ================= LIFECYCLE ================= */
onMounted(async () => {
  await Promise.all([loadOrder(), loadSites()]);
  loadEpaycoDataIfAny();
});
</script>

<style scoped>
/* Reset básico */
* {
  box-sizing: border-box;
  text-decoration: none;
}

.page-container {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: #111;
  background-color: #f3f4f6;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 2rem 1rem;
}

.receipt-card {
  background: #fff;
  width: 100%;
  max-width: 480px;
  border-radius: 0.75rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  position: relative;
  margin-bottom: 2rem;
}

.receipt-card::before {
  content: "";
  position: absolute;
  top: -5px;
  left: 0;
  width: 100%;
  height: 5px;
  background: radial-gradient(circle, transparent, transparent 50%, #fff 50%, #fff 100%) -7px -8px / 16px 16px repeat-x;
}

.receipt-header {
  padding: 2rem 1.5rem 1rem 1.5rem;
  text-align: center;
  border-bottom: 2px dashed #eee;
}

.client-name {
  font-size: 1.5rem;
  font-weight: 800;
  margin: 0 0 0.5rem 0;
  color: #000;
  line-height: 1.2;
}

.thank-you-msg {
  font-size: 1.1rem;
  font-weight: 700;
  margin: 0;
  color: #333;
}

.receipt-body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.6rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 4px;
  text-transform: uppercase;
  margin-right: 0.5rem;
  margin-bottom: 0.5rem;
}

.badge-success {
  background-color: #dcfce7;
  color: #166534;
}

.order-meta {
  text-align: center;
  margin-top: 0.5rem;
}
.order-id {
  font-weight: 800;
  font-size: 1.2rem;
  margin: 0;
}
.order-user {
  font-weight: 600;
  margin: 0.25rem 0;
}
.order-dates {
  display: flex;
  flex-direction: column;
  font-size: 0.9rem;
  color: #555;
}

.table-header {
  background-color: #000;
  color: #fff;
  font-weight: 700;
  text-transform: uppercase;
  padding: 0.5rem 0.75rem;
  display: flex;
  justify-content: space-between;
  border-radius: 4px 4px 0 0;
  font-size: 0.85rem;
}

.table-rows {
  border: 1px solid #eee;
  border-top: none;
  padding: 0.5rem;
}

.product-row-group {
  margin-bottom: 0.5rem;
}

.product-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 0.25rem;
}

.product-info {
  font-size: 0.95rem;
  line-height: 1.3;
}

.product-price {
  font-weight: 600;
  white-space: nowrap;
}

.combo-details, .modifier-row {
  font-size: 0.85rem;
  color: #555;
  padding-left: 1rem;
}

.combo-label {
  font-weight: 700;
  font-size: 0.75rem;
  margin: 0.25rem 0;
}

.modifier-row {
  display: flex;
  justify-content: space-between;
}

.separator {
  height: 1px;
  background-color: #eee;
  margin-top: 0.5rem;
}

.totals-section {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  border-top: 2px solid #000;
  padding-top: 0.75rem;
}

.total-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.95rem;
}

.final-total {
  font-size: 1.2rem;
  font-weight: 800;
  margin-top: 0.5rem;
}

.strike {
  text-decoration: line-through;
}
.discount-text {
  color: #b91c1c;
}

/* BLOQUE DE LINK DE PAGO */
.admin-link-block {
    margin-bottom: 0.5rem;
}
.link-control {
    display: flex;
    gap: 0.5rem;
    align-items: stretch;
}
.link-input {
    flex: 1;
    background-color: #f9f9f9;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 0.5rem;
    color: #444;
    font-size: 0.9rem;
    outline: none;
}
.btn-copy {
    background-color: #000;
    color: #fff;
    border: none;
    border-radius: 4px;
    padding: 0 1rem;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    transition: background-color 0.2s;
}
.btn-copy:hover {
    background-color: #333;
}

.section-block {
  margin-top: 0.5rem;
}

.section-title {
  font-weight: 700;
  text-transform: uppercase;
  padding: 0.35rem 0.5rem;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}

.section-title.dark {
  background-color: #000;
  color: #fff;
}

.notes-box {
  border: 1px solid #000;
  padding: 0.75rem;
  font-size: 0.9rem;
  background-color: #fff;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.75rem;
}

.info-item {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 1rem;
  font-size: 0.9rem;
  align-items: baseline;
}

.info-item .label {
  font-weight: 700;
  color: #444;
}

.info-item .value {
  color: #000;
}

.capitalize {
  text-transform: capitalize;
}

.receipt-footer {
  padding: 1.5rem;
  background-color: #f9fafb;
  border-top: 1px solid #eee;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  border-radius: 0 0 0.75rem 0.75rem;
}

.full-width {
  width: 100%;
}

.btn {
  width: 100%;
  padding: 1rem;
  border: none;
  border-radius: 0.5rem;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: transform 0.1s, opacity 0.2s;
}

.btn:active {
  transform: scale(0.98);
}

.btn-warning {
  background-color: var(--primary-color, #f59e0b);
  color: #fff;
}

.btn-whatsapp {
  background-color: #25D366;
  color: #fff;
}

.btn-outline-danger {
  background-color: transparent;
  border: 1px solid #dc2626;
  color: #dc2626;
}

@keyframes pulse-green {
  0% { box-shadow: 0 0 0 0 rgba(37, 211, 102, 0.7); }
  70% { box-shadow: 0 0 0 10px rgba(37, 211, 102, 0); }
  100% { box-shadow: 0 0 0 0 rgba(37, 211, 102, 0); }
}

.pulse-anim {
  animation: pulse-green 2s infinite;
}

.loading-state {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 80vh;
  width: 100%;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #000;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>