// src/App.jsx
import React from 'react';

// Importe os componentes de gráfico que serão criados
import GraficoNivelAtual from './components/GraficoNivelAtual';
import GraficoHistorico from './components/GraficoHistorico';

import './App.css'; // Se você tiver um App.css global

// A URL base da API pode ser definida aqui ou importada se for usada em múltiplos lugares
export const API_BASE_URL = "http://localhost:8000"; // Ou sua URL de dev

function App() {
  return (
    <div className="flex flex-col items-center justify-start min-h-screen p-4 sm:p-6 text-slate-200 font-sans">
      <div className="w-full max-w-7xl"> {/* Aumentei o max-w para acomodar mais gráficos */}
        <header className="text-center mb-8 sm:mb-10">
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-sky-400 to-indigo-400 bg-clip-text text-transparent drop-shadow-sm">
            Monitoramento da Caixa d'Água
          </h1>
          <p dir="rtl" className="text-lg sm:text-xl mt-1 text-slate-400">
            مراقبة خزان المياه
          </p>
        </header>

        {/* Layout dos Gráficos */}
        {/* Usaremos um grid para organizar. Você pode ajustar col-span e layout como preferir */}
        <main className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
          
          {/* Coluna Esquerda: Nível Atual e talvez um histórico menor */}
          <div className="flex flex-col gap-6 lg:gap-8">
            <GraficoNivelAtual />
            <GraficoHistorico
            titulo="Nível (Últimos 7 Dias)"
            endpoint={`${API_BASE_URL}/leituras/d/7`}
            periodoLabel="7d"
            alturaGrafico={250}
              
            />
          </div>

          {/* Coluna Direita: Históricos maiores */}
          <div className="flex flex-col gap-6 lg:gap-8">
            <GraficoHistorico
              titulo="Nível (Últimas 24h)"
              endpoint={`${API_BASE_URL}/leituras/h/24`}
              periodoLabel="24h" // Usado para logs ou identificação interna se necessário
              alturaGrafico={250} // Pode passar props para customizar cada instância
            />
            <GraficoHistorico
              titulo="Nível (Últimos 30 Dias)"
              endpoint={`${API_BASE_URL}/leituras/d/30`}
              periodoLabel="30d"
              alturaGrafico={250}
            />
          </div>
        </main>
        
        <footer className="mt-12 text-center">
            <div className="bg-slate-800/70 rounded-xl shadow-lg p-4 max-w-xs mx-auto transition-shadow hover:shadow-xl border border-slate-700/50 flex items-center justify-center gap-3">
            <img src="/jvsv.jpg" alt="Foto de João Vitor" className="w-12 h-12 rounded-full object-cover border-2 border-sky-400"/>
            <div>
                <p className="text-xs text-slate-400">Desenvolvido por:</p>
                <p className="text-sm font-semibold text-slate-100">João V. Sgotti Veiga</p>
            </div>
            </div>
        </footer>

      </div>
    </div>
  );
}

export default App;