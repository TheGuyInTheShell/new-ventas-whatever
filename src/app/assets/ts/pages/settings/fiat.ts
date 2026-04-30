import Alpine from "alpinejs";
import mask from '@alpinejs/mask';
import focus from '@alpinejs/focus';
import collapse from '@alpinejs/collapse';
import "htmx.org";
import { fiatStore, fiatActions } from "../../store/fiatStore";

(window as any).Alpine = Alpine;

Alpine.plugin(mask);
Alpine.plugin(focus);
Alpine.plugin(collapse);

document.addEventListener('alpine:init', () => {
    Alpine.data('fiatConfig', () => ({
        storeContext: fiatStore.getSnapshot().context,
        newFiat: { name: '', expression: '' },
        newComparison: { fromId: null as number | null, toId: null as number | null, rate: null as number | null },
        compRates: {} as Record<number, number>,
        isAddingFiat: false,

        init() {
            fiatStore.subscribe(snapshot => {
                this.storeContext = snapshot.context;
            });
            fiatActions.fetchFiats();
        },

        get fiats() { return this.storeContext.fiats; },
        get mainFiatId() { return this.storeContext.mainFiatId; },
        get comparisons() { return this.storeContext.comparisons; },
        get exchangeRates() { return this.storeContext.exchangeRates; },
        get customComparisons() { return this.storeContext.comparisons.filter(c => c.context === 'custom'); },

        async onAddFiat() {
            if (this.newFiat.name && this.newFiat.expression) {
                this.isAddingFiat = true;
                await fiatActions.createFiat(this.newFiat.name, this.newFiat.expression);
                this.newFiat.name = '';
                this.newFiat.expression = '';
                this.isAddingFiat = false;
            }
        },

        async onSetMainFiat(id: number) {
            await fiatActions.setMainFiat(id);
        },

        async onSetRate(fiatId: number, rate: string | number) {
            if (this.mainFiatId && rate) {
                await fiatActions.createLink(this.mainFiatId, fiatId, typeof rate === 'string' ? parseFloat(rate) : rate);
            }
        },

        async onAddComparison() {
            if (this.newComparison.fromId && this.newComparison.toId && this.newComparison.rate) {
                if (this.newComparison.fromId === this.newComparison.toId) {
                    alert('Cannot compare a currency with itself');
                    return;
                }
                await fiatActions.createLink(
                    this.newComparison.fromId,
                    this.newComparison.toId,
                    this.newComparison.rate
                );
                this.newComparison = { fromId: null, toId: null, rate: null };
            }
        },

        async onDeleteFiat(id: number) {
            if (confirm('Are you sure you want to delete this currency?')) {
                await fiatActions.deleteFiat(id);
            }
        },

        async onDeleteComparison(id: number) {
            if (confirm('Are you sure you want to delete this comparison?')) {
                await fiatActions.deleteComparison(id);
            }
        },

        getFiatName(id: number) {
            if (!Array.isArray(this.fiats)) return `#${id}`;
            const f = this.fiats.find(f => f.id === id);
            return f ? f.name : `#${id}`;
        },

        getFiatExpression(id: number) {
            if (!Array.isArray(this.fiats)) return '';
            const f = this.fiats.find(f => f.id === id);
            return f ? f.expression : '';
        }
    }));
});

Alpine.start();
