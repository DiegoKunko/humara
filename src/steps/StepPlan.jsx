import { Icon } from "../components/Icon";
import { PRICING } from "../constants";

export const StepPlan = ({ plan, setPlan, pages, total, file, dir }) => (
  <div className="space-y-5">
    <div>
      <h2 className="text-xl font-bold text-brand-900">Velocidad de entrega</h2>
      <p className="text-sm text-slate-400 mt-1">Ambos incluyen certificación de traductor público.</p>
    </div>
    <div className="space-y-3">
      {Object.entries(PRICING).map(([k, p]) => (
        <button key={k} onClick={() => setPlan(k)}
          className={`w-full flex items-center gap-4 p-5 rounded-2xl text-left transition-all border-2 ${
            plan === k ? "border-brand-500 bg-brand-50 shadow-sm shadow-brand-100" : "border-slate-100 hover:border-slate-200 bg-white"
          }`}>
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${
            plan === k ? "gradient-brand shadow-md shadow-brand-200" : "bg-slate-100"
          }`}>
            <Icon name={k === "express" ? "zap" : "clock"} size={20} color={plan === k ? "white" : "#94a3b8"} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <p className="font-bold text-brand-900">{p.name}</p>
              {k === "express" && <span className="text-[10px] font-bold uppercase bg-accent-100 text-accent-600 px-2 py-0.5 rounded-full">Popular</span>}
            </div>
            <p className="text-sm text-slate-400">Entrega en {p.hours} horas</p>
          </div>
          <div className="text-right flex-shrink-0">
            <p className="text-xl font-extrabold text-brand-900">${p.price}</p>
            <p className="text-xs text-slate-400">por página</p>
          </div>
        </button>
      ))}
    </div>

    {/* Quote card */}
    <div className="surface-dark">
      <div className="flex items-center justify-between text-xs text-brand-300 mb-3">
        <span className="font-semibold uppercase tracking-wider">Tu cotización</span>
        <span>{file?.name}</span>
      </div>
      <div className="space-y-2">
        {[
          ["Páginas detectadas", pages],
          ["Precio por página", `$${PRICING[plan].price}`],
          ["Traducción", dir === "en-es" ? "Inglés → Español" : "Español → Inglés"],
          ["Entrega", `${PRICING[plan].hours} horas`],
        ].map(([k, v]) => (
          <div key={k} className="flex justify-between text-sm">
            <span className="text-brand-300">{k}</span>
            <span className="font-medium">{v}</span>
          </div>
        ))}
      </div>
      <div className="border-t border-white/10 mt-4 pt-4 flex justify-between items-end">
        <span className="text-brand-300 font-semibold">Total</span>
        <span className="text-3xl font-extrabold">USD ${total}</span>
      </div>
    </div>
  </div>
);
