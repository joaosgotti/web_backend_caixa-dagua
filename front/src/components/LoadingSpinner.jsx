// src/components/LoadingSpinner.jsx
import React from 'react';

const LoadingSpinner = ({ mensagem = "Carregando dados..." }) => (
  <div className="flex flex-col justify-center items-center h-full py-10">
    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-t-2 border-sky-400"></div>
    {mensagem && <p className="mt-3 text-slate-400">{mensagem}</p>}
  </div>
);

export default LoadingSpinner;