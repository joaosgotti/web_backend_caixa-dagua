// src/components/GraficoNivelAtual.jsx
import React, { useState, useEffect } from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import LoadingSpinner from './LoadingSpinner'; // Ajuste o caminho se necessário
import { formatDisplayTimestamp } from '../utils/formatters'; // Ajuste o caminho
import { API_BASE_URL } from '../App'; // Importa a URL base

const POLLING_INTERVAL_MS = 15000; // 15 segundos

const GraficoNivelAtual = () => {
  const [ultimaLeitura, setUltimaLeitura] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [erro, setErro] = useState(null);

  const fetchUltimaLeitura = async (isPolling = false) => {
    if (!isPolling) setIsLoading(true);
    setErro(null); // Limpa erro anterior antes de nova tentativa
    try {
      const res = await fetch(`${API_BASE_URL}/leituras/ultima`);
      if (!res.ok) {
        const errorBody = await res.json().catch(() => null);
        throw new Error(errorBody?.detail || `Falha ao buscar última leitura (${res.status})`);
      }
      const data = await res.json();
      setUltimaLeitura(data);
    } catch (err) {
      console.error("Erro GraficoNivelAtual:", err);
      setErro(err.message);
    } finally {
      if (!isPolling) setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUltimaLeitura(); // Busca inicial
    const intervalId = setInterval(() => fetchUltimaLeitura(true), POLLING_INTERVAL_MS);
    return () => clearInterval(intervalId);
  }, []);

  const nivelAtualParaPizza = ultimaLeitura && typeof ultimaLeitura.nivel === 'number' ? ultimaLeitura.nivel : 0;
  const dadosPizza = [
    { name: "Nível", value: nivelAtualParaPizza },
    { name: "Vazio", value: Math.max(0, 100 - nivelAtualParaPizza) },
  ];
  const PIE_CHART_COLORS = ['#38bdf8', '#334155']; // sky-400, slate-700

  return (
    <div className="bg-slate-800 rounded-xl shadow-lg p-6 sm:p-8 transition-shadow hover:shadow-xl border border-slate-700 flex flex-col items-center min-h-[350px]"> {/* Altura mínima para consistência */}
      <h2 className="text-xl sm:text-2xl font-semibold mb-3 text-slate-100 border-b pb-2 border-slate-700 w-full text-center">
        Nível Atual
      </h2>
      {isLoading && !ultimaLeitura ? (
        <div className="flex-grow flex items-center justify-center w-full"><LoadingSpinner mensagem="Carregando nível atual..." /></div>
      ) : erro && !ultimaLeitura ? ( // Mostrar erro se o carregamento inicial falhar e não houver dados
         <div className="flex-grow flex flex-col items-center justify-center text-center">
            <p className="text-red-400 font-semibold">Erro:</p>
            <p className="text-red-300 text-sm">{erro}</p>
          </div>
      ) : ultimaLeitura && typeof ultimaLeitura.nivel === 'number' ? (
        <div className="w-full flex-grow flex flex-col justify-center items-center">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={dadosPizza} cx="50%" cy="50%" innerRadius={60} outerRadius={90} dataKey="value" paddingAngle={0} stroke="none">
                {dadosPizza.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={PIE_CHART_COLORS[index % PIE_CHART_COLORS.length]} />
                ))}
              </Pie>
              <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" className="fill-sky-300 text-4xl font-bold">
                {`${nivelAtualParaPizza.toFixed(0)}%`}
              </text>
              <Tooltip
                formatter={(value) => [`${Number(value).toFixed(0)}%`]}
                contentStyle={{ backgroundColor: 'rgba(30, 41, 59, 0.95)', border: '1px solid #475569', borderRadius: '8px' }}
                itemStyle={{ color: '#cbd5e1' }}
                labelStyle={{ display: 'none' }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="text-center mt-3 space-y-1">
            <p className="text-sm text-slate-400">
              {erro ? <span className="text-yellow-400 text-xs">(Erro no polling: {erro})</span> : <span>Atualizado: <span className="text-slate-300">{formatDisplayTimestamp(ultimaLeitura.created_on)}</span></span>}
            </p>
            <p className="text-sm text-slate-400">
              Distância: <span className="text-slate-300">{typeof ultimaLeitura.distancia === 'number' ? `${ultimaLeitura.distancia.toFixed(0)} cm` : 'N/A'}</span>
            </p>
          </div>
        </div>
      ) : (
         <div className="flex-grow flex items-center justify-center w-full">
            <p className="text-slate-500">Nenhuma leitura disponível.</p>
        </div>
      )}
    </div>
  );
};

export default GraficoNivelAtual;