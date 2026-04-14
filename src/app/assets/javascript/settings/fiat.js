import Alpine from "alpinejs";
import { fiatStore, fiatActions } from "../store/fiatStore";

/**
 * Registers the 'fiatConfig' Alpine.js data component.
 * This component acts as a bridge between the reactive UI and the Fiat Store.
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('fiatConfig', () => ({
        /** Current context snapshot from the fiatStore */
        storeContext: fiatStore.getSnapshot().context,
        /** Form state for creating a new fiat */
        newFiat: { name: '', expression: '' },
        /** Form state for creating a new comparison */
        newComparison: { fromId: null, toId: null, rate: null },
        /** Local UI state for comparison rates */
        compRates: {},
        /** Local UI state for add operation status */
        isAddingFiat: false,

        /**
         * Initializes the component. Subscribes to store changes and performs initial fetch.
         */
        init() {
            fiatStore.subscribe(snapshot => {
                this.storeContext = snapshot.context;
            });
            fiatActions.fetchFiats();
        },

        // Helper Getters
        get fiats() { return this.storeContext.fiats; },
        get mainFiatId() { return this.storeContext.mainFiatId; },
        get comparisons() { return this.storeContext.comparisons; },
        get exchangeRates() { return this.storeContext.exchangeRates; },
        /** Returns comparisons defined with 'custom' context */
        get customComparisons() { return this.storeContext.comparisons.filter(c => c.context === 'custom'); },

        /**
         * Event handler for adding a new fiat currency.
         * @async
         */
        async onAddFiat() {
            if (this.newFiat.name && this.newFiat.expression) {
                this.isAddingFiat = true;
                await fiatActions.createFiat(this.newFiat.name, this.newFiat.expression);
                this.newFiat.name = '';
                this.newFiat.expression = '';
                this.isAddingFiat = false;
            }
        },

        /**
         * Event handler for setting the main fiat currency.
         * @async
         * @param {number} id
         */
        async onSetMainFiat(id) {
            await fiatActions.setMainFiat(id);
        },

        /**
         * Event handler for updating an exchange rate between the main currency and another.
         * @async
         * @param {number} fiatId - The ID of the non-main fiat currency.
         * @param {string|number} rate - The exchange rate value.
         */
        async onSetRate(fiatId, rate) {
            if (this.mainFiatId && rate) {
                await fiatActions.createLink(this.mainFiatId, fiatId, parseFloat(rate), 'main');
            }
        },

        /**
         * Event handler for adding a custom comparison between any two currencies.
         * @async
         */
        async onAddComparison() {
            if (this.newComparison.fromId && this.newComparison.toId && this.newComparison.rate) {
                if (this.newComparison.fromId === this.newComparison.toId) {
                    alert('Cannot compare a currency with itself');
                    return;
                }
                await fiatActions.createLink(
                    parseInt(this.newComparison.fromId),
                    parseInt(this.newComparison.toId),
                    parseFloat(this.newComparison.rate),
                    'custom'
                );
                this.newComparison = { fromId: null, toId: null, rate: null };
            }
        },

        /**
         * Event handler for deleting a fiat currency.
         * @async
         * @param {number} id
         */
        async onDeleteFiat(id) {
            if (confirm('Are you sure you want to delete this currency?')) {
                await fiatActions.deleteFiat(id);
            }
        },

        /**
         * Event handler for deleting a custom comparison.
         * @async
         * @param {number} id
         */
        async onDeleteComparison(id) {
            if (confirm('Are you sure you want to delete this comparison?')) {
                await fiatActions.deleteComparison(id);
            }
        },

        /**
         * Returns the name of a currency given its ID.
         * @param {number} id
         * @returns {string}
         */
        getFiatName(id) {
            const f = this.fiats.find(f => f.id === id);
            return f ? f.name : `#${id}`;
        },

        /**
         * Returns the expression/symbol of a currency given its ID.
         * @param {number} id
         * @returns {string}
         */
        getFiatExpression(id) {
            const f = this.fiats.find(f => f.id === id);
            return f ? f.expression : '';
        }
    }));
});


Alpine.start();