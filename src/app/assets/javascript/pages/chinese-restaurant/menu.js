import Alpine from "alpinejs";
import mask from '@alpinejs/mask';
import focus from '@alpinejs/focus';
import collapse from '@alpinejs/collapse';
import "htmx.org";

window.Alpine = Alpine;

// Register Alpine.js plugins
Alpine.plugin(mask);
Alpine.plugin(focus);
Alpine.plugin(collapse);

/**
 * Registers the 'chineseRestaurantMenu' Alpine.js data component.
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('chineseRestaurantMenu', (initialDishes) => ({
        search: '',
        sortBy: 'name_asc',
        isModalOpen: false,
        isIngredientsModalOpen: false,
        ingredientsData: { name: '', list: [] },
        dishes: initialDishes || [],

        init() {
            // Initialization logic if needed
        },

        get filteredDishes() {
            let result = [...this.dishes];
            if (this.search) {
                const q = this.search.toLowerCase();
                result = result.filter(d => d.name.toLowerCase().includes(q));
            }
            if (this.sortBy === 'name_asc') {
                result.sort((a, b) => a.name.localeCompare(b.name));
            } else if (this.sortBy === 'price_asc') {
                result.sort((a, b) => a.price - b.price);
            } else if (this.sortBy === 'price_desc') {
                result.sort((a, b) => b.price - a.price);
            }
            return result;
        },

        openIngredients(dish) {
            this.ingredientsData = {
                name: dish.name,
                list: dish.ingredients.map(id => ({ name: 'Ingredient ' + id, qty: 1, price: 2.0 }))
            };
            this.isIngredientsModalOpen = true;
        }
    }));
});

Alpine.start();
