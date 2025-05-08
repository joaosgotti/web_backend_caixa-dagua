// src/components/GraficoHistorico.jsx
import React, { useState, useEffect } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import LoadingSpinner from './LoadingSpinner'; // Ajuste o caminho se necessário
import { formatXAxis, formatTooltipLabel } from '../utils/formatters'; // Ajuste o caminho

const GraficoHistorico = ({ titulo, endpoint, periodoLabel, alturaGrafico = 300 }) => {
  const [dados, setDados] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [erro, setErro] = useState(null);

  const formatarDadosParaGrafico = (dadosApi) => (
    Array.isArray(dadosApi)
      ? dadosApi
          .map((item) => ({
            timestamp: new Date(item.created_on).getTime(),
            nivel: typeof item.nivel === "number" ? item.nivel : null,
          }))
          .filter((item) => !isNaN(item.timestamp) && item.nivel !== null)
          .sort((a, b) => a.timestamp - b.timestamp)
      : []
  );

  useEffect(() => {
    const fetchDadosHistoricos = async () => {
      setIsLoading(true);
      setErro(null);
      try {
        // console.log(`GraficoHistorico: Buscando dados para ${periodoLabel} de ${endpoint}`);
        const res = await fetch(endpoint);
        if (!res.ok) {
          const errorBody = await res.json().catch(() => null);
          throw new Error(errorBody?.detail || `Falha ao buscar dados históricos (${res.status})`);
        }
        const dataApi = await res.json();
        setDados(formatarDadosParaGrafico(dataApi));
      } catch (err) {
        console.error(`Erro GraficoHistorico (${periodoLabel}):`, err);
        setErro(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    if (endpoint) { // Só busca se o endpoint for fornecido
        fetchDadosHistoricos();
    } else {
        setIsLoading(false);
        setDados([]); // Limpa os dados se não houver endpoint
    }
  }, [endpoint, periodoLabel]); // Re-executa se o endpoint ou label mudar

  return (
    <div className="bg-slate-800 rounded-xl shadow-lg p-6 sm:p-8 transition-shadow hover:shadow-xl border border-slate-700 flex flex-col min-h-[350px]"> {/* Altura mínima para consistência */}
      <h2 className="text-xl sm:text-2xl font-semibold mb-5 text-slate-100 border-b pb-2 border-slate-700">
        {titulo}
      </h2>
      <div className="flex-grow" style={{ minHeight: `${alturaGrafico}px` }}>
        {isLoading ? (
          <div style={{ height: `${alturaGrafico}px` }} className="flex items-center justify-center"><LoadingSpinner mensagem={`Carregando ${periodoLabel}...`} /></div>
        ) : erro ? (
          <div style={{ height: `${alturaGrafico}px` }} className="flex flex-col items-center justify-center text-center">
            <p className="text-red-400 font-semibold">Erro ao carregar:</p>
            <p className="text-red-300 text-sm">{erro}</p>
          </div>
        ) : dados && dados.length > 0 ? (
          <ResponsiveContainer width="100%" height={alturaGrafico}>
            <LineChart data={dados} margin={{ top: 5, right: 30, left: -15, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
              <XAxis dataKey="timestamp" tickFormatter={formatXAxis} stroke="#94a3b8" tick={{ fontSize: 10 }} interval="preserveStartEnd" minTickGap={35} />
              <YAxis stroke="#94a3b8" tick={{ fontSize: 10 }} domain={[0, 'dataMax + 5']} tickFormatter={(value) => `${value}%`} allowDataOverflow={true} />
              <Tooltip labelFormatter={formatTooltipLabel} contentStyle={{ backgroundColor: 'rgba(30, 41, 59, 0.95)', border: '1px solid #475569', borderRadius: '8px' }} itemStyle={{ color: '#67e8f9' }} labelStyle={{ color: '#cbd5e1', fontWeight: 'bold' }} formatter={(value) => [`${typeof value === 'number' ? value.toFixed(0) : '?'}%`, 'Nível']} />
              <Legend wrapperStyle={{ paddingTop: '20px' }} itemStyle={{ color: '#cbd5e1' }} />
              <Line type="monotone" dataKey="nivel" name="Nível (%)" stroke="#67e8f9" strokeWidth={2} dot={false} activeDot={{ r: 5, strokeWidth: 1, fill: '#67e8f9', stroke: '#f0f9ff' }} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ height: `${alturaGrafico}px` }} className="flex items-center justify-center">
            <p className="text-slate-500">Nenhum dado histórico disponível.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default GraficoHistorico;