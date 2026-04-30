import Alpine from "alpinejs";
import mask from '@alpinejs/mask';
import focus from '@alpinejs/focus';
import collapse from '@alpinejs/collapse';
import "htmx.org";

(window as any).Alpine = Alpine;

// Register Alpine.js plugins
Alpine.plugin(mask);
Alpine.plugin(focus);
Alpine.plugin(collapse);

interface Dish {
    id: number;
    name: string;
    price: number;
    ingredients: number[];
}

document.addEventListener('alpine:init', () => {
    Alpine.data('chineseRestaurantMenu', (initialDishes: Dish[]) => ({
        search: '',
        sortBy: 'name_asc',
        isModalOpen: false,
        isIngredientsModalOpen: false,
        ingredientsData: { name: '', list: [] as any[] },
        dishes: initialDishes || [],

        init() {
        },

        get filteredDishes(): Dish[] {
            let result = [...(this as any).dishes];
            if ((this as any).search) {
                const q = (this as any).search.toLowerCase();
                result = result.filter((d: Dish) => d.name.toLowerCase().includes(q));
            }
            if ((this as any).sortBy === 'name_asc') {
                result.sort((a: Dish, b: Dish) => a.name.localeCompare(b.name));
            } else if ((this as any).sortBy === 'price_asc') {
                result.sort((a: Dish, b: Dish) => a.price - b.price);
            } else if ((this as any).sortBy === 'price_desc') {
                result.sort((a: Dish, b: Dish) => b.price - a.price);
            }
            return result;
        },

        openIngredients(dish: Dish) {
            (this as any).ingredientsData = {
                name: dish.name,
                list: dish.ingredients.map(id => ({ name: 'Ingredient ' + id, qty: 1, price: 2.0 }))
            };
            (this as any).isIngredientsModalOpen = true;
        }
    }));
});

Alpine.start();
