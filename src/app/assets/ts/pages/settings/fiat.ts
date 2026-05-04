import Alpine from "alpinejs";
import mask from '@alpinejs/mask';
import focus from '@alpinejs/focus';
import collapse from '@alpinejs/collapse';
import "htmx.org";
import { fiatStore, fiatActions } from "../../store/fiatStore";
import { notifySuccess, notifyError, notifyWarning } from "../../includes/toast";

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
            fiatStore.subscribe((snapshot: any) => {
                this.storeContext = snapshot.context;
            });
            fiatActions.fetchFiats();
        },

        get fiats() { return this.storeContext.fiats; },
        get mainFiatId() { return this.storeContext.mainFiatId; },
        get comparisons() { return this.storeContext.comparisons; },
        get exchangeRates() { return this.storeContext.exchangeRates; },
        get currentComparisons() { return this.storeContext.comparisons.filter((c: any) => c.context === 'current'); },
        get customComparisons() { return this.storeContext.comparisons.filter((c: any) => c.context === 'custom'); },

        async onAddFiat() {
            if (this.newFiat.name && this.newFiat.expression) {
                this.isAddingFiat = true;
                try {
                    const success = await fiatActions.createFiat(this.newFiat.name, this.newFiat.expression);
                    if (success) {
                        notifySuccess(`Currency ${this.newFiat.name} added`, 'Settings');
                        this.newFiat.name = '';
                        this.newFiat.expression = '';
                    } else {
                        notifyError('Failed to add currency', 'Error');
                    }
                } catch (e: any) {
                    notifyError(e.message || 'Error adding currency', 'Error');
                } finally {
                    this.isAddingFiat = false;
                }
            }
        },

        async onSetMainFiat(id: number) {
            try {
                await fiatActions.setMainFiat(id);
                notifySuccess('Main currency updated', 'Settings');
            } catch (e: any) {
                notifyError('Failed to set main currency', 'Error');
            }
        },

        async onSetRate(fiatId: number, rate: string | number) {
            if (this.mainFiatId && rate) {
                try {
                    await fiatActions.createLink(this.mainFiatId, fiatId, typeof rate === 'string' ? parseFloat(rate) : rate);
                    notifySuccess('Exchange rate updated', 'Settings');
                } catch (e: any) {
                    notifyError('Failed to update rate', 'Error');
                }
            }
        },

        async onAddComparison() {
            if (this.newComparison.fromId && this.newComparison.toId && this.newComparison.rate) {
                if (this.newComparison.fromId === this.newComparison.toId) {
                    notifyWarning('Cannot compare a currency with itself', 'Settings');
                    return;
                }
                try {
                    const success = await fiatActions.createLink(
                        this.newComparison.fromId,
                        this.newComparison.toId,
                        this.newComparison.rate,
                        true // Use custom context
                    );
                    if (success) {
                        notifySuccess('Comparison added', 'Settings');
                        this.newComparison = { fromId: null, toId: null, rate: null };
                    } else {
                        notifyError('Failed to add comparison', 'Error');
                    }
                } catch (e: any) {
                    notifyError(e.message || 'Error adding comparison', 'Error');
                }
            }
        },

        async onDeleteFiat(id: number) {
            if (confirm('Are you sure you want to delete this currency?')) {
                try {
                    await fiatActions.deleteFiat(id);
                    notifySuccess('Currency deleted', 'Settings');
                } catch (e: any) {
                    notifyError('Failed to delete currency', 'Error');
                }
            }
        },

        async onDeleteComparison(id: number) {
            if (confirm('Are you sure you want to delete this comparison?')) {
                try {
                    await fiatActions.deleteComparison(id);
                    notifySuccess('Comparison deleted', 'Settings');
                } catch (e: any) {
                    notifyError('Failed to delete comparison', 'Error');
                }
            }
        },

        getFiatName(id: number) {
            if (!Array.isArray(this.fiats)) return `#${id}`;
            const f = this.fiats.find((f: any) => f.id === id);
            return f ? f.name : `#${id}`;
        },

        getFiatExpression(id: number) {
            if (!Array.isArray(this.fiats)) return '';
            const f = this.fiats.find((f: any) => f.id === id);
            return f ? f.expression : '';
        }
    }));
});

Alpine.start();
