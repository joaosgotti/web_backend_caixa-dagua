// src/App.jsx
import { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from "recharts";

// Importa o CSS (certifique-se que App.css existe ou remova o import)
// import './App.css'; // Descomente se você tiver App.css

// Componente LoadingSpinner
const LoadingSpinner = () => (
  <div className="flex justify-center items-center h-full">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-400"></div>
    <p className="ml-3 text-slate-400">Carregando...</p>
  </div>
);

// Defina o intervalo de polling em milissegundos
const POLLING_INTERVAL_MS = 15000;

function App() {
  const [ultimaLeitura, setUltimaLeitura] = useState(null);
  const [leituras24h, setLeituras24h] = useState([]);
  const [erro, setErro] = useState(null);
  const [isLoadingUltimaInicial, setIsLoadingUltimaInicial] = useState(true);
  const [isLoading24hInicial, setIsLoading24hInicial] = useState(true);

  // URLs da API (considere usar variáveis de ambiente)
  const ULTIMA_LEITURA_URL = "https://projeto-caixa-dagua-api.onrender.com/leituras/ultima";
  const ULTIMAS_24H_URL = "https://projeto-caixa-dagua-api.onrender.com/leituras";

  // Função auxiliar para buscar dados
  const fetchData = async (url, setData, setLoading, setError, isPolling = false) => {
    if (!isPolling && setLoading) {
       setLoading(true);
    }
    try {
      const res = await fetch(url);
      if (!res.ok) {
        let errorBody = null;
        try { errorBody = await res.json(); } catch (e) { /* Ignore */ }
        const errorMsg = errorBody?.message || res.statusText || 'Falha ao buscar dados';
        throw new Error(`Erro ${res.status}: ${errorMsg}`);
      }
      const data = await res.json();
      setData(data);
      setError(null); // Limpa erro se sucesso
    } catch (err) {
      console.error(`Erro ao buscar dados de ${url}:`, err);
      setError(err.message || "Ocorreu um erro desconhecido");
    } finally {
       if (!isPolling && setLoading) {
         setLoading(false);
       }
    }
  };

  // ---- Efeitos ----
  useEffect(() => {
    console.log("Buscando histórico inicial (24h)...");
    fetchData(
      ULTIMAS_24H_URL,
      (data) => {
        const formattedData = Array.isArray(data) ? data
          .map(item => ({
            ...item,
            distancia: typeof item.distancia === 'number' ? item.distancia : null,
            timestamp: new Date(item.timestamp || item.created_on).getTime()
          }))
          .filter(item => !isNaN(item.timestamp) && item.distancia !== null)
          .sort((a, b) => a.timestamp - b.timestamp)
        : [];
        setLeituras24h(formattedData);
      },
      setIsLoading24hInicial,
      setErro
    );
  }, []);

  useEffect(() => {
    console.log("Buscando última leitura inicial...");
    fetchData(
      ULTIMA_LEITURA_URL,
      (data) => {
        setUltimaLeitura(data);
      },
      setIsLoadingUltimaInicial,
      setErro
    );

    console.log(`Configurando polling a cada ${POLLING_INTERVAL_MS / 1000} segundos...`);
    const intervalId = setInterval(() => {
      console.log("Polling: Buscando última leitura...");
      fetchData(
        ULTIMA_LEITURA_URL,
        (data) => {
          setUltimaLeitura(data);
        },
        null,
        setErro,
        true
      );
    }, POLLING_INTERVAL_MS);

    return () => {
      console.log("Limpando intervalo de polling.");
      clearInterval(intervalId);
    };
  }, []);

  // ---- Funções de Formatação ----
  const formatXAxis = (timestamp) =>
    typeof timestamp === 'number' && !isNaN(timestamp) ? new Date(timestamp).toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'America/Recife'
    }) : '';

  const formatTooltipLabel = (timestamp) =>
     typeof timestamp === 'number' && !isNaN(timestamp) ? new Date(timestamp).toLocaleString('pt-BR', {
      dateStyle: 'short',
      timeStyle: 'medium',
      timeZone: 'America/Recife'
    }) : 'Inválido';

  const formatUltimaLeituraTimestamp = (timestampString) => {
    if (!timestampString) return 'Indisponível';
    try {
      const date = new Date(timestampString);
      if (isNaN(date.getTime())) {
        throw new Error('Invalid date string received');
      }
      return date.toLocaleString('pt-BR', {
        dateStyle: 'full',
        timeStyle: 'medium',
        timeZone: 'America/Recife'
      });
    } catch (e) {
      console.error("Erro ao formatar timestamp da última leitura:", timestampString, e);
      return 'Data inválida';
    }
  }

  // ---- Renderização JSX ----
  return (
    // 1: Div Principal (Aberta)
    <div className="flex flex-col items-center justify-start min-h-screen p-4 sm:p-6 bg-slate-900 font-sans text-slate-200">
      {/* 2: Div Container Interno (Aberta) */}
      <div className="w-full max-w-6xl">
        <h1 className="text-4xl sm:text-5xl font-extrabold text-center mb-2 tracking-tight bg-gradient-to-r from-sky-400 to-indigo-400 bg-clip-text text-transparent drop-shadow-sm">
          Monitoramento da Caixa d'Água
        </h1>
        <p dir="rtl" className="text-lg sm:text-xl text-center mb-8 sm:mb-10 text-slate-400 font-sans">
          مراقبة خزان المياه
        </p>

        {erro && (
          <div className="bg-red-900/80 border border-red-700 text-red-200 px-4 py-3 rounded-lg relative mb-6 text-center shadow max-w-3xl mx-auto" role="alert">
            <strong className="font-bold">Ocorreu um erro:</strong> <span className="block sm:inline ml-2">{erro}</span>
          </div>
        )}

        {/* 3: Div Grid Principal (Aberta) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">

          {/* 4: Div Coluna Esquerda (Aberta) */}
          <div className="md:col-span-1 flex flex-col gap-6 lg:gap-8">

            {/* Card da Última Leitura */}
            <div className="bg-slate-800 rounded-xl shadow-lg p-6 sm:p-8 transition-shadow hover:shadow-xl border border-slate-700 flex flex-col min-h-[180px]">
              <h2 className="text-xl sm:text-2xl font-semibold mb-5 text-slate-100 border-b pb-2 border-slate-700 flex-shrink-0">
                Última Leitura
              </h2>
              <div className="flex-grow flex items-center justify-center">
                {isLoadingUltimaInicial ? (
                  <LoadingSpinner />
                ) : ultimaLeitura ? (
                  <div className="text-slate-300 space-y-3 text-base sm:text-lg text-center sm:text-left">
                    <p><span className="font-medium text-slate-100">Nível:</span>{' '}{typeof ultimaLeitura.distancia === 'number' ? `${ultimaLeitura.distancia.toFixed(0)} cm` : 'Indisponível'}</p>
                    <p><span className="font-medium text-slate-100">Porcentagem:</span>{' '}{typeof ultimaLeitura.nivel === 'number' ? `${ultimaLeitura.nivel.toFixed(0)}%` : 'Indisponível'}</p>
                    <p><span className="font-medium text-slate-100">Data:</span>{' '}{formatUltimaLeituraTimestamp(ultimaLeitura.timestamp || ultimaLeitura.created_on)}</p>
                  </div>
                ) : !erro ? (
                  <p className="text-slate-500">Nenhuma leitura disponível.</p>
                ) : null }
              </div>
            </div>

            {/* Bloco de Perfil */}
            <div className="bg-slate-800 rounded-xl shadow-lg p-6 transition-shadow hover:shadow-xl border border-slate-700 flex items-center gap-4">
              <img
                src="/jvsv.jpg" // Certifique-se que está na pasta /public
                alt="Foto de João Vitor"
                className="w-16 h-16 sm:w-20 sm:h-20 rounded-full object-cover border-2 border-sky-400 flex-shrink-0"
              />
              <div>
                <p className="text-xs sm:text-sm text-slate-400">Desenvolvido por:</p>
                <p className="text-base sm:text-lg font-semibold text-slate-100">João V. Sgotti Veiga</p>
              </div>
            </div>
          </div>
          {/* 4: Div Coluna Esquerda (Fechada) */}

          {/* 5: Div Coluna Direita (Aberta) */}
          <div className="md:col-span-2 bg-slate-800 rounded-xl shadow-lg p-6 sm:p-8 transition-shadow hover:shadow-xl border border-slate-700 flex flex-col">
            <h2 className="text-xl sm:text-2xl font-semibold mb-5 text-slate-100 border-b pb-2 border-slate-700 flex-shrink-0">
              Histórico (Últimas 24h)
            </h2>
            {/* 6: Div Container do Gráfico/Spinner/Mensagem (Aberta) */}
            <div className="flex-grow min-h-[300px]">
              {isLoading24hInicial ? (
                <div className="h-[300px] flex items-center justify-center"><LoadingSpinner /></div>
              ) : leituras24h.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={leituras24h} margin={{ top: 5, right: 25, left: -15, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={formatXAxis}
                      stroke="#94a3b8"
                      tick={{ fontSize: 11, fill: '#94a3b8' }}
                      interval="preserveStartEnd"
                      minTickGap={40}
                    />
                    <YAxis
                      stroke="#94a3b8"
                      tick={{ fontSize: 11, fill: '#94a3b8' }}
                      domain={['dataMin - 5', 'dataMax + 5']}
                      tickFormatter={(value) => typeof value === 'number' ? value.toFixed(0) : ''}
                    />
                    <Tooltip
                      labelFormatter={formatTooltipLabel}
                      contentStyle={{ backgroundColor: 'rgba(30, 41, 59, 0.95)', border: '1px solid #475569', borderRadius: '8px', boxShadow: '2px 2px 10px rgba(0,0,0,0.3)' }}
                      itemStyle={{ color: '#818cf8' }}
                      labelStyle={{ color: '#cbd5e1', fontWeight: 'bold' }}
                      formatter={(value) => [`${typeof value === 'number' ? value.toFixed(1) : '?'} cm`, 'Distância']}
                    />
                    <Legend wrapperStyle={{ paddingTop: '20px', paddingBottom: '5px' }} itemStyle={{ color: '#cbd5e1' }} />
                    <Line
                      type="monotone"
                      dataKey="distancia"
                      name="Distância (cm)"
                      stroke="#818cf8"
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 6, fill: '#818cf8', stroke: '#e2e8f0', strokeWidth: 2 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : !erro ? (
                 // Caso: Sem dados e sem erro
                <div className="h-[300px] flex items-center justify-center">
                    <p className="text-slate-500">Nenhum dado histórico disponível.</p>
                </div>
              ) : null /* Caso: Com erro (mensagem global é mostrada) */ }
            </div>
             
          </div>
           
        </div>

      </div>

    </div>
  ); // Fim do return statement
} // <--- FECHAMENTO CORRETO DA FUNÇÃO App

export default App; // Exporta o componente