// app/service/order/orderService.ts

import axios from "axios";
import { URI } from "../conection";

// Nuxt 3: stores y router desde #imports
import { usecartStore } from "#imports";
import { useSitesStore } from "#imports";
import { useUserStore } from "#imports";
import { useReportesStore } from "#imports";
import { useRouter } from "#imports";

/* ----------------------------- Helpers UI/valid ---------------------------- */

function alertMissing(msg: string) {
  alert(msg);
}

/**
 * Helper para obtener los stores siempre que se necesiten.
 * Evita tenerlos en variables globales “const store = ...”
 */
function getStores() {
  const cart = usecartStore();
  const site = useSitesStore();
  const user = useUserStore();
  const report = useReportesStore();
  return { cart, site, user, report };
}

/**
 * Normaliza el teléfono:
 * - Si phone_code es objeto con dialCode, usa eso.
 * - Si es string, intenta que empiece con +.
 * - Quita espacios del número.
 */
function buildPhone() {
  const { user } = getStores();

  const code = (user.user as any)?.phone_code;
  const number = user.user.phone_number?.toString().replace(/\s+/g, "") || "";

  let dial = "";
  if (!code) return null;

  if (typeof code === "string") {
    dial = code.startsWith("+") ? code : `+${code}`;
  } else if (typeof code === "object" && "dialCode" in code) {
    dial = (code.dialCode as string) || "";
    dial = dial.startsWith("+") ? dial : `+${dial}`;
  }

  if (!dial || !number) return null;
  return `${dial}${number}`;
}

/* --------------------------------- Domain --------------------------------- */

/** Arma la orden base desde los stores. */
function preparar_orden() {
  const { cart, site, user } = getStores();

  user.user.was_reserva = false;
  cart.sending_order = true;

  const order_products = cart.cart; // se envía como pe_json
  const site_id = site.location?.site?.site_id;
  const pe_site_id = site.location?.site?.pe_site_id;
  const payment_method_id = user.user.payment_method_option?.id ?? null;
  const order_type_id = user.user.order_type?.id ?? null;
  const placa = user.user.placa?.toString().trim() || "";
  const address_details = cart.address_details;

  const delivery_price =
    payment_method_id === 7 ? 0 : site.location?.neigborhood?.delivery_price ?? 0;

  const baseNotes = cart?.cart?.order_notes ?? "";
  const order_notes = baseNotes || "";

  const phone = buildPhone();

  /* -------------------------------------------------------------------------- */
  /* LÓGICA DE DIRECCIÓN MODIFICADA                       */
  /* -------------------------------------------------------------------------- */
  
  let final_address = user.user.address || "";

  // 1. Verificamos si es Google Maps revisando si existe address_details con place_id
  const isGoogleMaps = address_details && address_details.place_id;

  // 2. Si NO es Google Maps (es parámetros), NO es Recoger, y tenemos un barrio seleccionado:
  if (!isGoogleMaps && order_type_id !== 2) {
    const neighborhoodName = site.location?.neigborhood?.name;
    if (neighborhoodName && final_address) {
       // Concatenamos el barrio al final
       final_address = `${final_address} - ${neighborhoodName}`;
    }
  }

  const user_data = {
    user_name: user.user.name?.toString().trim() || "",
    user_phone: phone || "",
    user_address:
      order_type_id === 2
        ? "recoger / pick up"
        : final_address, // Usamos la dirección ya procesada
    email: user.user.email?.toString().trim() || "",
  };

  /* -------------------------------------------------------------------------- */

  const order = {
    order_products: [], // backend recibe pe_json del carrito completo
    site_id,
    pe_site_id,
    order_type_id,
    placa,
    delivery_person_id: 4,
    payment_method_id,
    delivery_price,
    order_notes: order_notes || "SIN NOTAS",
    user_data,
    order_aditionals: [],
    pe_json: order_products,
    address_details: address_details,
    total: 0,
  };

  return order;
}

/**
 * Valida y alerta por **cada** falta (no junta mensajes).
 * Retorna true si todo OK.
 */
function validateOrder(order: any): boolean {
  const { cart, user } = getStores();

  // 1) Método de entrega obligatorio
  if (!order.order_type_id) {
    alertMissing("Error: Debe seleccionar un método de entrega.");
  }

  // 2) Placa si es 'Pasar a recoger' (id 2) y la sede es 33
  if (order.order_type_id === 2 && order.site_id === 33) {
    if (!order.placa || order.placa.trim() === "") {
      alertMissing("Error: Debe proporcionar la placa del vehículo para recogida.");
    }
  }

  // 3) Código de país y teléfono
  if (!order.user_data.user_phone || order.user_data.user_phone.trim() === "") {
    const hasPhoneCode = !!(user.user as any)?.phone_code;
    const hasPhoneNumber = !!user.user.phone_number?.toString().trim();
    if (!hasPhoneCode) {
      alertMissing("Error: El código de país del teléfono es obligatorio.");
    }
    if (!hasPhoneNumber) {
      alertMissing("Error: Debe ingresar su número de teléfono.");
    }
  }

  // 4) Nombre
  if (!order.user_data.user_name || order.user_data.user_name.trim() === "") {
    alertMissing("Error: Debe ingresar su nombre.");
  }

  // 5) Dirección (excepto recoger)
  if (order.order_type_id !== 2) {
    if (!order.user_data.user_address || order.user_data.user_address.trim() === "") {
      alertMissing("Error: Debe ingresar su dirección.");
    }
  }

  // 6) Email
  if (!order.user_data.email || order.user_data.email.trim() === "") {
    alertMissing("Error: Debe ingresar su correo electrónico.");
  }

  // 7) Site y delivery_price
  if (!order.site_id) {
    alertMissing("Error: Debe seleccionar una sede válida.");
  }
  if (order.delivery_price == null) {
    alertMissing("Error: El costo de envío no está disponible para su zona.");
  }

  // 8) Método de pago
  if (!order.payment_method_id && order.payment_method_id !== 0) {
    alertMissing("Error: Debe seleccionar un método de pago.");
  }

  // Evaluación final estricta
  const ok =
    !!order.order_type_id &&
    !(order.order_type_id === 2 &&
      order.site_id === 33 &&
      (!order.placa || order.placa.trim() === "")) &&
    !!order.user_data.user_name &&
    order.user_data.user_name.trim() !== "" &&
    !!order.user_data.user_phone &&
    order.user_data.user_phone.trim() !== "" &&
    !!order.user_data.email &&
    order.user_data.email.trim() !== "" &&
    !!order.site_id &&
    order.delivery_price != null &&
    (order.order_type_id === 2 ||
      (order.user_data.user_address && order.user_data.user_address.trim() !== "")) &&
    (order.payment_method_id || order.payment_method_id === 0);

  if (!ok) {
    cart.sending_order = false;
    return false;
  }

  return true;
}

/* --------------------------------- Service -------------------------------- */

export const orderService = {
  async sendOrder() {
    const { cart, report, user } = getStores();
    const router = useRouter();

    // Prepara y valida
    const order = preparar_orden();

    if (!order) {
      cart.sending_order = false;
      alertMissing(
        "Error: No se pudo preparar el pedido. Recargue e intente de nuevo."
      );
      return null;
    }

    if (!validateOrder(order)) {
      // validateOrder ya lanzó alerts por cada falta
      return null;
    }

    try {
      report.setLoading(true, `enviando tu pedido ${user.user.name}`);
      const response = await axios.post(`${URI}/order`, order);

      if (response.status === 200) {
        cart.sending_order = false;
        cart.last_order = response.data;
        report.setLoading(false, "enviando tu pedido");

        // Redirección condicional: mantiene tu lógica original
        if (order.payment_method_id !== 9 || user.user.token) {
          router.push(`/gracias?order_id=${response.data}`);
        }

        return response.data;
      } else {
        console.error(
          "An error occurred while sending the order:",
          response.status
        );
        alertMissing("Ocurrió un error enviando el pedido. Intenta de nuevo.");
        report.setLoading(false, "enviando tu pedido");
        cart.sending_order = false;
        return null;
      }
    } catch (error) {
      console.error("An error occurred while sending the order:", error);
      report.setLoading(false, "enviando tu pedido");
      cart.sending_order = false;
      alertMissing(
        "Ocurrió un error enviando el pedido. Revisa tu conexión a internet e intenta de nuevo."
      );
      return null;
    }
  },

  preparar_orden() {
    return preparar_orden();
  },
};

/* ------------------------------ NOTA IMPORTANTE ----------------------------

- Quité las definiciones duplicadas (imports, stores, funciones).
- Ahora todo usa #imports (stores + useRouter), apropiado para Nuxt 3.
- Los stores se obtienen con getStores() dentro de cada función para evitar
  problemas de contexto/SSR.
- Se mantiene toda tu lógica de validación, teléfono, placa, recoger, etc.

---------------------------------------------------------------------------- */
