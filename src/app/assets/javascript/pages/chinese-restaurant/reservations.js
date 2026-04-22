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
 * Registers the 'chineseRestaurantReservations' Alpine.js data component.
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('chineseRestaurantReservations', (initialReservations) => ({
        reservations: initialReservations || [],
        isAddModalOpen: false,

        init() {
            // Initialization logic
        }
    }));
});

Alpine.start();
