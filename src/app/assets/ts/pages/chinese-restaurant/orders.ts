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
}

interface CartItem extends Dish {
    qty: number;
}

document.addEventListener('alpine:init', () => {
    Alpine.data('chineseRestaurantOrders', (initialDishes: Dish[]) => ({
        dishes: initialDishes || [],
        cart: [] as CartItem[],
        isCheckoutOpen: false,
        selectedPayment: 'USD',

        addToCart(dish: Dish) {
            const existing = (this as any).cart.find((item: CartItem) => item.id === dish.id);
            if (existing) {
                existing.qty++;
            } else {
                (this as any).cart.push({ ...dish, qty: 1 });
            }
        },

        removeFromCart(id: number) {
            (this as any).cart = (this as any).cart.filter((item: CartItem) => item.id !== id);
        },

        updateQty(id: number, delta: number) {
            const item = (this as any).cart.find((i: CartItem) => i.id === id);
            if (item) {
                item.qty += delta;
                if (item.qty <= 0) this.removeFromCart(id);
            }
        },

        get total(): number {
            return (this as any).cart.reduce((sum: number, item: CartItem) => sum + (item.price * item.qty), 0);
        },

        processSale() {
            alert('Sale processed successfully!');
            (this as any).cart = [];
            (this as any).isCheckoutOpen = false;
        }
    }));
});

Alpine.start();
