/**
 * App Module - JavaScript Entry Point
 *
 * Import your CSS here so Rolldown bundles it via PostCSS (Tailwind).
 * Add any app-level JS imports below.
 */
import "../css/app.css"
import Alpine from "alpinejs"
import mask from '@alpinejs/mask'
import focus from '@alpinejs/focus'
import collapse from '@alpinejs/collapse'


Alpine.plugin(mask)
Alpine.plugin(focus)
Alpine.plugin(collapse)


Alpine.start();