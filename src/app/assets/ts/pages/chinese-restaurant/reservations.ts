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

document.addEventListener('alpine:init', () => {
    Alpine.data('chineseRestaurantReservations', (initialReservations: any[]) => ({
        reservations: initialReservations || [],
        isAddModalOpen: false,

        init() {
        }
    }));
});

Alpine.start();
