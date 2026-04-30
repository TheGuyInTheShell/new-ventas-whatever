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
    Alpine.data('chineseRestaurantTables', (initialTables: any[]) => ({
        tables: initialTables || [],

        getStatusClass(status: string) {
            if (status === 'Available') return 'bg-success/10 text-success border-success/20';
            if (status === 'Occupied') return 'bg-error/10 text-error border-error/20';
            if (status === 'Reserved') return 'bg-warning/10 text-warning border-warning/20';
            return 'bg-base-200 text-base-content/40 border-base-300';
        },

        getStatusDot(status: string) {
            if (status === 'Available') return 'bg-success';
            if (status === 'Occupied') return 'bg-error';
            if (status === 'Reserved') return 'bg-warning';
            return 'bg-base-content/20';
        }
    }));
});

Alpine.start();
