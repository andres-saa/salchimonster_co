import { URI } from "../conection";

export const paymentMethodService = {
  async getPaymentMethods() {
    try {
      const response = await fetch(`${URI}/payment_methods/`);

      if (!response.ok) {
        console.error(
          "An error occurred while fetching the ingredients:",
          response.status
        );
        return null;
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error(
        "An error occurred while fetching the ingredients:",
        error
      );
      return null;
    }
  },
};
