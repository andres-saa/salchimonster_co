import { URI } from "../conection";
import { useSitesStore } from "../../store/site";

const store = useSitesStore();

export const categoriesService = {
  async getCategories() {
    const site_id = store.location?.site?.site_id;

    if (!site_id) {
      return [];
    }

    try {
      const response = await fetch(`${URI}/categories/${site_id}/1`);

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
