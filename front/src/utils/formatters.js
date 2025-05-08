// src/utils/formatters.js

export const formatXAxis = (timestamp) =>
    new Date(timestamp).toLocaleTimeString("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
    });
  
  export const formatTooltipLabel = (timestamp) =>
    new Date(timestamp).toLocaleString("pt-BR", {
      dateStyle: "short",
      timeStyle: "medium",
    });
  
  export const formatDisplayTimestamp = (timestampString) => {
    if (!timestampString) return 'Indisponível';
    try {
      return new Date(timestampString).toLocaleString('pt-BR', {
        dateStyle: 'full',
        timeStyle: 'medium',
        timeZone: 'America/Recife' // Garante a exibição no fuso desejado
      });
    } catch (e) {
      console.error("Erro ao formatar timestamp:", timestampString, e);
      return 'Data inválida';
    }
  };