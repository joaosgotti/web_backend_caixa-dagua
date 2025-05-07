// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html", // Inclui o HTML principal (padrão Vite)
    "./src/**/*.{js,ts,jsx,tsx}", // Procura classes em todos esses tipos de arquivos dentro da pasta src
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}