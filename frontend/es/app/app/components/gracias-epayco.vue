<template>
  <ClientOnly>
    <Dialog 
      header="TU PEDIDO" 
      v-if="order.order_id" 
      v-model:visible="order.order_id" 
      modal 
      :closable="false"
      :style="{ width: '50vw' }" 
      :breakpoints="{ '960px': '75vw', '641px': '100vw' }"
    >
      <div
        class="p-2 col-12 my-6"
        style="height: auto; min-height: 90vh; padding: 0rem; display: flex; gap: 1rem; justify-content: center; align-items: center;"
      >
        <div
          class="shadow-7 p-4"
          style="border-radius: 0.5rem; max-width: 500px; display: flex; flex-direction: column; gap: 0.5rem; font-size: 1rem; background-color: white; padding: 1rem;"
        >
          <p class="text-4xl text-center mt-5" style="font-weight: bold; text-align: center;">
            🤩{{ order?.pe_json?.cliente?.cliente_nombres?.toUpperCase() }} {{ order?.pe_json?.cliente?.cliente_apellidos?.toUpperCase() }}🤩
          </p>

          <p class="text-2xl text-center" style="font-weight: bold; text-align: center;">
            🔥MUCHAS GRACIAS POR TU COMPRA!🔥
          </p>

          <div id="factura" style="width: 100%; text-transform: uppercase;">
            <div id="factura-inner" style="width: 100%;">

              <Tag class="tag mb-2" severity="success" v-if="order.responsible_id">Pago autorizado</Tag> <br>
              <Tag class="tag" severity="success" v-if="order.responsible_id">{{ order.name }}</Tag>

              <div style="width: auto;">
                <p id="id" style="font-weight: bold; min-width: 100%; width: max-content; text-align: center; color: black; margin:0rem;">
                   ID:{{ order.order_id }}
                </p>

                <p id="client-name" style="font-weight: bold; min-width: 100%; width: max-content; text-align: center; color: black; margin:0rem;">
                   {{ order.user_name }} {{ order.second_name }} {{ order.first_last_name }} {{ order.second_last_name }}
                </p>

                <p style="padding: 0; color: black; text-align: center; margin: auto; margin-bottom: 1rem; width: max-content; min-width: max-content; display: flex; justify-content: center; flex-direction: column">
                  <b>Fecha: {{ order.latest_status_timestamp?.split('T')[0] }}</b>
                  <b>Hora: {{ order.latest_status_timestamp?.split('T')[1]?.split(':')?.slice(0,2)?.join(':') }}</b>
                </p>

                <div style="font-weight: bold; color: white; margin: 0; background-color: black; align-items: center; display: grid; grid-template-columns: auto auto;">
                  <div class="px-2" style="width: 100%;">
                    <b>Productos</b>
                  </div>
                  <div class="px-2">
                    <p style="text-align: end; font-weight: bold;">
                      <b>Total</b>
                    </p>
                  </div>
                </div>

                <div v-for="product in order.pe_json?.listaPedidos" :key="product.signature">
                  <div style="display: grid; gap: 0 1rem; grid-template-columns: auto auto;">
                    
                    <p v-if="store.currentOrder?.site_id == 32" class="p-0 m-0">
                      <b>( {{ product.pedido_cantidad }} kg )</b> {{ product.pedido_nombre_producto }}
                      ( {{ product.pedido_cantidad / product.presentacion }} {{ product.presentation_unit_measure }})
                      <br>
                    </p>

                    <p v-else class="p-0 m-0">
                      <b>( {{ product.pedido_cantidad }} )</b> {{ product.pedido_nombre_producto }}
                      <br>
                    </p>

                    <div>
                      <p v-if="product.pedido_base_price" style="text-align: end; color: black;">
                        {{ formatoPesosColombianos(product.pedido_base_price * product.pedido_cantidad) }}
                      </p>
                      <p v-else style="text-align: end; color: black;">
                        {{ formatoPesosColombianos(product.pedido_precio) }}
                      </p>
                    </div>
                  </div>

                  <p v-if="product.lista_productocombo?.length > 0" class="p-0 m-0"><b>COMBO INCLUYE</b></p>
                  <p v-if="product.lista_productocombo" class="p-0 m-0 ml-5" v-for="i in product.lista_productocombo" :key="i.pedido_nombre">
                     -- <b>{{ i.pedido_cantidad }}</b> {{ i.pedido_nombre }}
                  </p>

                  <div style="display: flex; justify-content: space-between;" class="p-0 m-0" v-for="i in product.modificadorseleccionList" :key="i.modificadorseleccion_nombre">
                    <p class="p-0 m-0">
                      - ( {{ product.pedido_cantidad }} ) <b>{{ i.modificadorseleccion_cantidad }}</b> {{ i.modificadorseleccion_nombre }}
                    </p>
                    <p class="p-0 m-0" style="text-align: end;">
                      {{ formatoPesosColombianos(i.pedido_precio * i.modificadorseleccion_cantidad * product.pedido_cantidad) }}
                    </p>
                  </div>

                  <div style="background-color: rgba(0, 0, 0, 0.286); height: 1px;"></div>
                </div>

                <div style="display: grid; margin-top: 1rem; grid-template-columns: auto auto">
                  <div><span style="font-weight: bold;"><b>Subtotal</b></span></div>
                  <div>
                    <p style="text-align: end; font-weight: bold; color: black;">
                      <b>{{ formatoPesosColombianos(order.pe_json.delivery.delivery_pagocon - order.pe_json?.delivery?.delivery_costoenvio) }}</b>
                    </p>
                  </div>

                  <div><span class="m-0" style="font-weight: bold;"><b>Domicilio</b></span></div>
                  <div>
                    <p class="m-0 p-0" style="text-align: end; font-weight: bold; color: black;">
                      <b>{{ formatoPesosColombianos(order.pe_json?.delivery?.delivery_costoenvio) }}</b>
                    </p>
                  </div>

                  <div><span style="font-weight: bold; color: black;"><b>Total</b></span></div>
                  <div>
                    <p class="m-0 p-0" style="text-align: end; color: black; font-weight: bold;">
                      <b>{{ formatoPesosColombianos(order.pe_json.delivery.delivery_pagocon) }}</b>
                    </p>
                  </div>
                </div>

                <p class="px-2" style="font-weight: bold; background-color: black; color: white; padding: 0; margin: 0; margin-top: 0.5rem;"><b>Notas</b></p>
                <p class="notas p-2 m-0" style="border: 1px solid; margin: 0; color: black; padding: 0.5rem;">
                   {{ order.order_notes?.toLowerCase() }}
                </p>

                <p class="px-2" style="background-color: black; font-weight: bold; margin-top: 1rem; color: white;">
                  <b>Cliente</b>
                </p>

                <div style="display: grid; gap: 1rem 2rem; grid-template-columns: auto auto; align-items: start;">
                  <div><span><b>Nombre</b></span></div>
                  <div><span style="text-align: start; color: black;">{{ order.user_name }} {{ order.second_name }} {{ order.first_last_name }} {{ order.second_last_name }}</span></div>

                  <template v-if="order.site_id == 32">
                    <div><span><b>Cedula / Nit</b></span></div>
                    <div><span style="text-align: start; color: black;">{{ order.cedula_nit }}</span></div>
                  </template>

                  <div><span><b>Metodo de entrega</b></span></div>
                  <div><span style="text-align: start; color: black;">{{ order.order_type }}</span></div>

                  <template v-if="order.site_id == 32">
                    <div><span><b>Fecha de entrega</b></span></div>
                    <div><p style="text-align: start; color: black;">{{ order.pe_json.delivery.delivery_horaentrega }}</p></div>
                  </template>

                  <template v-if="order.placa">
                    <div><span><b>Placa del vehiculo</b></span></div>
                    <div><p style="text-align: start; color: black;">{{ order.placa }}</p></div>
                  </template>

                  <div><span><b>Telefono</b></span></div>
                  <div><span style="text-align: start; color: black;">{{ order.user_phone }}</span></div>

                  <template v-if="order.site_id == 32">
                    <div><span><b>Correo</b></span></div>
                    <div><span style="text-align: start; color: black;">{{ order.email }}</span></div>
                  </template>

                  <template v-if="order.order_type != 'Pasar a recoger'">
                    <div><span><b>Direccion</b></span></div>
                    <div><span style="text-align: start; color: black;">{{ order.user_address?.toLowerCase() }}</span></div>
                  </template>

                  <div><span><b>Metodo de pago</b></span></div>
                  <div><span style="text-align: start; color: black;">{{ order.payment_method?.toLowerCase() }}</span></div>
                </div>

              </div>
            </div>
          </div>

          <div style="display: flex; flex-direction: column; gap: 1rem;">
            <a v-if="!route.query?.ref_payco" :href="whatsappUrl2" target="_blank">
              <Button icon="pi pi-whatsapp" severity="danger" class="wsp" style="font-weight: bold; background-color: #00b66c; border: none; width: 100%;" label="CONFIRMAR PEDIDO"></Button>
            </a>

            <a v-else :href="whatsappUrl3" target="_blank">
              <Button icon="pi pi-whatsapp" severity="danger" class="wsp" style="font-weight: bold; background-color: #00b66c; border: none; width: 100%;" label="TIENES DUDAS ? ESCRIBENOS"></Button>
            </a>

            <NuxtLink to="/">
              <Button icon="pi pi-arrow-left" severity="danger" outlined style="font-weight: bold; border: none; width: 100%;" label="VOLVER AL MENU"></Button>
            </NuxtLink>
          </div>

          <div v-if="route.query?.ref_payco">
            <h4>Información de pago</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr;">
              <div><h5> Ref. Comercio</h5></div>
              <div><h5 style="font-weight: 300;"> {{ epayco_data?.x_id_factura }}</h5></div>

              <div><h5> Ref. ePayco</h5></div>
              <div><h5 style="font-weight: 300;"> {{ epayco_data?.x_ref_payco }}</h5></div>

              <div><h5> Banco </h5></div>
              <div><h5 style="font-weight: 300;"> {{ epayco_data?.x_bank_name }}</h5></div>

              <div><h5> Estado </h5></div>
              <div><h5 style="font-weight: 300;"> {{ epayco_data?.x_transaction_state }}</h5></div>

              <div><h5> Autorización </h5></div>
              <div><h5 style="font-weight: 300;"> {{ epayco_data?.x_approval_code }}</h5></div>

              <div><h5> Tarjeta </h5></div>
              <div><h5 style="font-weight: 300;"> {{ epayco_data?.x_cardnumber }}</h5></div>

              <div><h5> Total </h5></div>
              <div><h5 style="font-weight: 300;"> {{ formatoPesosColombianos(epayco_data?.x_amount) }}</h5></div>
            </div>
          </div>

          <a style="display: flex; gap: 1rem; text-decoration: none; margin: 3rem 0" :href="`https://secure.epayco.co/landingresume?ref_payco=${route.query.ref_payco}`">
            <Button icon="pi pi-print" style="background-color: black; width: 50%; border: none; outline: none" label="Imprimir o guardar"></Button>
            <Button icon="pi pi-send" style="width: 50%; border: none; outline: none" label="Enviar a mi correo"></Button>
          </a>
        </div>
      </div>
    </Dialog>

    <div v-else style="display: flex; align-items: center; justify-content: center; height: 90vh; width: 100vw;">
      <h2>Cargando tu pedido...</h2>
    </div>
  </ClientOnly>
</template>

<script setup>
import { ref, onMounted, computed, onUnmounted } from "vue";
import { useRoute } from "#imports";
import { usecartStore } from "~/store/shoping_cart"; // Ajusta alias si es necesario
import { useUserStore } from "~/store/user";
import { useSitesStore } from "~/store/site";
import { useReportesStore } from "~/store/ventas";
import { formatoPesosColombianos } from "~/service/utils/formatoPesos";
import { fetchService } from "~/service/utils/fetchService";
import { URI } from "~/service/conection";

// Componentes de PrimeVue (generalmente se auto-importan en Nuxt, pero los dejamos por si acaso)
// Si usas el módulo de PrimeVue para Nuxt, puedes borrar estas lineas.
// import Button from "primevue/button";
// import Dialog from "primevue/dialog";
// import Tag from "primevue/tag";

// Stores
const store = usecartStore();
const user = useUserStore();
const sitestore = useSitesStore();
const reportes = useReportesStore();
const route = useRoute();

const epayco_data = ref({});
const order = ref({
  "order_id": null,
  "user_id": null,
  "site_id": null,
  "site_name": "",
  "order_notes": "",
  "pe_json": {
    "cliente": {
      "cliente_nombres": "",
      "cliente_telefono": "",
      "cliente_apellidos": "",
      "cliente_direccion": ""
    },
    "delivery": {
      "delivery_pagocon": null,
      "delivery_costoenvio": null,
      "delivery_horaentrega": "",
    },
    "listaPedidos": []
  },
  "payment_method": "",
  "user_name": "",
  "user_address": "",
  "user_phone": "",
  "order_type": "",
  "cedula_nit": null,
  "email": "",
  "placa": null
});

const text = ref("");
const text2 = ref("");
const text3 = ref("");

// Lógica unificada al montar el componente
onMounted(async () => {
  const epayco = route.query?.ref_payco;

  if (epayco) {
    const secret = "k3Y!_Pr0t3cTi0n$2025@SalchiMonster#BackEnd%Safe"; // Se mantiene key del usuario
    
    try {
      // 1. Validar transacción con ePayco
      const response = await fetchService.get(`https://secure.epayco.co/validation/v1/reference/${epayco}`);
      epayco_data.value = response?.data;

      // 2. Second Chance si fue aceptada
      if (epayco_data.value?.x_transaction_state === "Aceptada") {
        await fetchService.post(`/confirmacion-epayco/second-chance/${epayco_data.value?.x_id_factura}/${epayco}/${secret}`);
      }

      // 3. Obtener la orden de nuestra DB
      order.value = await fetchService.get(`${URI}/order/epayco/${epayco_data?.value?.x_ref_payco}`);
    } catch (error) {
      console.error("Error validando ePayco:", error);
    }
  }

  // Desactivar loading del reporte
  reportes?.setLoading(false, "enviando tu pedido");

  // Construir mensajes de Whatsapp
  const message_products = [];
  (store?.cart || []).forEach((element) => {
    message_products.push(
      `*(${element?.pedido_cantidad || 0} kilos)* de ${
        element?.pedido_nombre_producto || ""
      } ( ${element?.pedido_cantidad / element?.presentacion} ${element.presentation_unit_measure})`
    );
  });

  const userNameFull = `*${
    (user.user?.name?.toUpperCase() || "") + " " +
    (user.user?.second_name?.toUpperCase() || "") + "  " +
    (user.user?.first_last_name?.toUpperCase() || "") + " " +
    (user.user?.second_last_name?.toUpperCase() || "")
  }*`;

  // Mensaje 1 (Transferencia)
  text.value = `Hola soy ${userNameFull} 🤗 acabo de hacer el siguiente pedido en la página web *distrimonster.com*\n\n${(message_products || []).join("\n")}\n\nEl número de la orden es *#${store?.last_order || ""}*.\nLa pagina indica que es para recoger en la sede *${sitestore.location?.site?.site_name || ""}* el *${store?.delivery_horaentrega || ""}*\n\n*Escribo para Realizar la Transferecia*\n*Muchas Gracias* 🙏`;

  // Mensaje 2 (Confirmación General)
  text2.value = `Hola soy ${userNameFull}\n🤗 acabo de hacer el siguiente pedido en la página web *distrimonster.com*\n\n${(message_products || []).join("\n")}\n\nEl número de la orden es *#${store?.last_order || ""}*.\nLa pagina indica que es para recoger en la sede *${sitestore.location?.site?.site_name || ""}* el *${store?.delivery_horaentrega || ""}*\n\n*Escribo para Confirmar el pedido*\n*Muchas Gracias* 🙏`;

  // Mensaje 3 (Confirmación Pago Tarjeta)
  text3.value = `Hola soy ${userNameFull}\n🤗 acabo de hacer el siguiente pedido en la página web *salchimonster.com*\n\nEl número de la orden es *#${store?.last_order || ""}*.\n\nRealice' el pago con la tarjeta *${epayco_data.value?.x_cardnumber || 'N/A'}*\nY la referencia del pago es *${epayco_data.value?.x_ref_payco || 'N/A'}*\n\n*Muchas Gracias* 🙏`;
});

// Computados para URLs
const whatsappUrl = computed(() => {
  const baseUrl = "https://api.whatsapp.com/send";
  const urlParams = new URLSearchParams({ phone: "573053447255", text: text.value });
  return `${baseUrl}?${urlParams.toString()}`;
});

const whatsappUrl2 = computed(() => {
  const baseUrl = "https://api.whatsapp.com/send";
  const urlParams = new URLSearchParams({ phone: "573053447255", text: text2.value });
  return `${baseUrl}?${urlParams.toString()}`;
});

const whatsappUrl3 = computed(() => {
  const baseUrl = "https://api.whatsapp.com/send";
  const urlParams = new URLSearchParams({ phone: "573053447255", text: text3.value });
  return `${baseUrl}?${urlParams.toString()}`;
});

onUnmounted(() => {
  if (store?.cart) {
    store.cart = [];
  }
});
</script>

<style scoped>
@keyframes parpadeo {
  0% { filter: brightness(1); }
  50% { filter: brightness(1.1); transform: scale(1.01); }
}

.wsp {
  animation: parpadeo ease infinite 0.5s;
  transition: all ease 0.5s;
}
</style>