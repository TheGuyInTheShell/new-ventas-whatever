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
 * Registers the 'chineseRestaurantStaff' Alpine.js data component.
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('chineseRestaurantStaff', (initialStaff) => ({
        staff: initialStaff || [],

        getStatusClass(status) {
            if (status === 'Active') return 'badge-success';
            if (status === 'On Break') return 'badge-warning';
            return 'badge-ghost';
        }
    }));
});

Alpine.start();
