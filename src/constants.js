// Pricing in UYU (pesos uruguayos) — these are fallback defaults.
// Production values are loaded from Supabase config table.

export const PRICING = {
  price_per_word: 3, // UYU por palabra
  price_per_word_express: 4.2, // UYU por palabra (adelantar 24h)
};

// Tiempos de entrega por volumen de palabras
export const DELIVERY_TIERS = [
  { max_words: 15000, hours: 24 },
  { max_words: 25000, hours: 48 },
  { max_words: Infinity, hours: 72 },
];

// Partidas de nacimiento — precio fijo, estrategia Starbucks/decoy
export const PARTIDA_PRICING = {
  express: { hours: 0, price: 3500, label: "En el día" },
  standard: { hours: 24, price: 2500, label: "24 horas" },
  economy: { hours: 48, price: 2000, label: "48 horas" },
};

// Qué incluye el servicio
export const INCLUDES = [
  "Todo incluido en el precio por palabra",
  "Timbres incluidos",
  "Doble verificación por agentes IA",
  "Certificación por traductor público",
  "Entrega a domicilio (Montevideo / Ciudad de la Costa)",
  "Archivo digital vía email y/o WhatsApp",
];

// Calcula el tiempo de entrega según cantidad de palabras
export function getDeliveryHours(wordCount, tiers = DELIVERY_TIERS) {
  for (const tier of tiers) {
    if (wordCount <= tier.max_words) return tier.hours;
  }
  return tiers[tiers.length - 1].hours;
}

// Calcula el precio total para documentos generales
export function calcTotal(wordCount, express = false) {
  const rate = express ? PRICING.price_per_word_express : PRICING.price_per_word;
  return wordCount * rate;
}
