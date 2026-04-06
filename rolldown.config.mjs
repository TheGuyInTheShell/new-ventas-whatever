import { defineConfig } from "rolldown";
import postcss from "rollup-plugin-postcss";
import { globSync, glob } from 'tinyglobby';
import path from 'path';
import { pathToFileURL } from 'node:url';
import { optimizeLodashImports } from "@optimize-lodash/rollup-plugin";

// 1. Buscamos todas las configuraciones de plugins
const subConfigPaths = await glob(['plugins/**/rolldown.config.mjs'], {
  absolute: true,
  ignore: ['**/node_modules/**']
});

const loadSubConfigs = async () => {
  const configs = await Promise.all(
    subConfigPaths.map(async (configPath) => {
      // Importación dinámica (esencial para archivos .mjs)
      const module = await import(pathToFileURL(configPath).href);
      return module.default;
    })
  );
  return configs.flat(); // Aplanamos en caso de que un sub-config devuelva un array
};

const subConfigs = await loadSubConfigs();

// 2. Configuración base del proyecto
const baseConfig = defineConfig({
  input: Object.fromEntries(
    globSync('src/app/assets/**/*.js').map((file) => [
      // This removes `src/` as well as the file extension from each
      // file, so e.g. src/nested/foo.js becomes nested/foo, and
      // normalizes Windows backslashes to forward slashes.
      path
        .relative('src/app/assets/', file.slice(0, file.length - path.extname(file).length))
        .split(path.sep)
        .join('/'),
      // This expands the relative paths to absolute paths, so e.g.
      // src/nested/foo.js becomes /project/src/nested/foo.js
      path.resolve(file),
    ]),
  ),
  output: {
    dir: "./src/app/web/out/",
    format: "esm",
    entryFileNames: "[name].js",
    minify: true,
  },
  moduleTypes: {
    ".css": "js",
  },
  plugins: [
    postcss({
      extract: "css/app.css", // relative to output.dir → src/app/web/out/css/app.css
      minimize: true,
    }),
    optimizeLodashImports(),
  ],
});

// 3. Exportación múltiple
export default [
  baseConfig,
  ...subConfigs
];
