import { URI } from "../conection";

export const adicionalesService = {
  async getAditional(product_instance_id) {
    try {
      const response = await fetch(
        `${URI}/adicionales-new-active/${product_instance_id}`
      );

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

  async getAditionalGroup(product_instance_ids, site_id) {
    const requestBody = {
      instance_product_ids: product_instance_ids,
      site_id: site_id,
    };

    try {
      const response = await fetch(
        `${URI}/adicionales-new-group-active/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestBody),
        }
      );

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
