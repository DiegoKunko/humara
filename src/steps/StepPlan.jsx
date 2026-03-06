import { Icon } from "../components/Icon";

export const StepPlan = ({
  docType,
  tier,
  setTier,
  express,
  setExpress,
  words,
  total,
  deliveryHours,
  rate,
  pricePerWord,
  pricePerWordExpress,
  partidaPricing,
  deliveryTiers,
  file,
  dir,
}) => {
  const isPartida = docType === "partida_nacimiento";

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-bold text-brand-900">
          {isPartida ? "Velocidad de entrega" : "Tu cotización"}
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          {isPartida
            ? "Elegí cuándo necesitás tu traducción certificada."
            : "Incluye timbres, certificación y entrega a domicilio."}
        </p>
      </div>

      {isPartida ? (
        /* Partida de nacimiento: 3 opciones estilo Starbucks */
        <div className="space-y-3">
          {Object.entries(partidaPricing).map(([k, p]) => (
            <button
              key={k}
              onClick={() => setTier(k)}
              className={`w-full flex items-center gap-4 p-5 rounded-2xl text-left transition-all border-2 relative ${
                tier === k
                  ? "border-brand-500 bg-brand-50 shadow-sm shadow-brand-100"
                  : "border-slate-100 hover:border-slate-200 bg-white"
              }`}
            >
              {k === "standard" && (
                <span className="absolute -top-2.5 right-4 text-[10px] font-bold uppercase bg-accent-500 text-white px-3 py-0.5 rounded-full shadow-sm">
                  Mejor valor
                </span>
              )}
              <div
                className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${
                  tier === k
                    ? "gradient-brand shadow-md shadow-brand-200"
                    : "bg-slate-100"
                }`}
              >
                <Icon
                  name={k === "express" ? "zap" : k === "economy" ? "clock" : "check"}
                  size={20}
                  color={tier === k ? "white" : "#94a3b8"}
                />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-bold text-brand-900 capitalize">{k === "economy" ? "Económico" : k === "standard" ? "Estándar" : "Express"}</p>
                <p className="text-sm text-slate-400">{p.label}</p>
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-xl font-extrabold text-brand-900">
                  ${p.price.toLocaleString()}
                </p>
                <p className="text-xs text-slate-400">UYU</p>
              </div>
            </button>
          ))}
        </div>
      ) : (
        /* Documento general: resumen + opción express */
        <div className="space-y-4">
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-5 space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">Palabras detectadas</span>
              <span className="font-semibold text-brand-900">
                {words.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">Precio por palabra</span>
              <span className="font-semibold text-brand-900">${rate} UYU</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">Entrega estimada</span>
              <span className="font-semibold text-brand-900">
                {deliveryHours} horas
              </span>
            </div>
            <div className="border-t border-slate-100 pt-3 flex justify-between items-center">
              <span className="font-bold text-brand-900">Total</span>
              <span className="text-2xl font-extrabold text-brand-900">
                ${total.toLocaleString()} UYU
              </span>
            </div>
          </div>

          {/* Express upgrade */}
          <button
            onClick={() => setExpress(!express)}
            className={`w-full flex items-center gap-4 p-4 rounded-2xl text-left transition-all border-2 ${
              express
                ? "border-accent-400 bg-accent-50"
                : "border-slate-100 hover:border-slate-200 bg-white"
            }`}
          >
            <div
              className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                express
                  ? "bg-accent-500 shadow-sm shadow-accent-200"
                  : "bg-slate-100"
              }`}
            >
              <Icon
                name="zap"
                size={18}
                color={express ? "white" : "#94a3b8"}
              />
            </div>
            <div className="flex-1">
              <p className="font-bold text-brand-900 text-sm">
                Adelantar 24 horas
              </p>
              <p className="text-xs text-slate-400">
                ${pricePerWordExpress} UYU/palabra en vez de $
                {pricePerWord}
              </p>
            </div>
            <div
              className={`w-5 h-5 rounded-md border-2 flex items-center justify-center ${
                express ? "bg-accent-500 border-accent-500" : "border-slate-300"
              }`}
            >
              {express && (
                <Icon name="check" size={12} color="white" strokeWidth={3} />
              )}
            </div>
          </button>
        </div>
      )}

      {/* Quote card */}
      <div className="surface-dark">
        <div className="flex items-center justify-between text-xs text-brand-300 mb-3">
          <span className="font-semibold uppercase tracking-wider">
            Tu cotización
          </span>
          <span>{file?.name}</span>
        </div>
        <div className="space-y-2">
          {[
            isPartida
              ? ["Tipo", "Partida de nacimiento"]
              : ["Palabras", words.toLocaleString()],
            isPartida
              ? ["Plan", tier === "economy" ? "Económico" : tier === "standard" ? "Estándar" : "Express"]
              : ["Precio/palabra", `$${rate} UYU`],
            [
              "Traducción",
              dir === "en-es" ? "Inglés a Español" : "Español a Inglés",
            ],
            [
              "Entrega",
              deliveryHours === 0 ? "En el día" : `${deliveryHours} horas`,
            ],
          ].map(([k, v]) => (
            <div key={k} className="flex justify-between text-sm">
              <span className="text-brand-300">{k}</span>
              <span className="font-medium">{v}</span>
            </div>
          ))}
        </div>
        <div className="border-t border-white/10 mt-4 pt-4 flex justify-between items-end">
          <span className="text-brand-300 font-semibold">Total</span>
          <span className="text-3xl font-extrabold">
            ${total.toLocaleString()} UYU
          </span>
        </div>
      </div>
    </div>
  );
};
