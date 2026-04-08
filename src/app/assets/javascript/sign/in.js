/**
 * App Module - JavaScript Entry Point
 *
 * Import your CSS here so Rolldown bundles it via PostCSS (Tailwind).
 * Add any app-level JS imports below.
 */

import Alpine from "alpinejs"
import mask from '@alpinejs/mask'
import focus from '@alpinejs/focus'
import collapse from '@alpinejs/collapse'
import "htmx.org"

Alpine.plugin(mask)
Alpine.plugin(focus)
Alpine.plugin(collapse)

document.addEventListener('alpine:init', () => {

})


Alpine.start();
