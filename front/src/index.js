import React from 'react';
import ReactDOM from 'react-dom/client';  // React 18+ usa o 'root' ao invés de 'render'
import App from './App';  // Importa o componente App

const root = ReactDOM.createRoot(document.getElementById('root'));  // Pega o elemento 'root' do HTML
root.render(
  <React.StrictMode>
    <App />  {/* Renderiza o App */}
  </React.StrictMode>
);
