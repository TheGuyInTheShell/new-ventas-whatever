import { Alpine as AlpineType } from 'alpinejs';

declare global {
    interface Window {
        Alpine: AlpineType;
        htmx: any; // htmx doesn't have official types yet, keeping it as any for now but explicitly declared
    }
}
