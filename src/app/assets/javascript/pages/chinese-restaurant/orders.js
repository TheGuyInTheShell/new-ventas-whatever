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
 * Registers the 'chineseRestaurantOrders' Alpine.js data component.
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('chineseRestaurantOrders', (initialDishes) => ({
        dishes: initialDishes || [],
        cart: [],
        isCheckoutOpen: false,
        selectedPayment: 'USD',

        addToCart(dish) {
            const existing = this.cart.find(item => item.id === dish.id);
            if (existing) {
                existing.qty++;
            } else {
                this.cart.push({ ...dish, qty: 1 });
            }
        },

        removeFromCart(id) {
            this.cart = this.cart.filter(item => item.id !== id);
        },

        updateQty(id, delta) {
            const item = this.cart.find(i => i.id === id);
            if (item) {
                item.qty += delta;
                if (item.qty <= 0) this.removeFromCart(id);
            }
        },

        get total() {
            return this.cart.reduce((sum, item) => sum + (item.price * item.qty), 0);
        },

        processSale() {
            alert('Sale processed successfully!');
            this.cart = [];
            this.isCheckoutOpen = false;
        }
    }));
});

Alpine.start();
