import { Icon } from "./Icon";

const LABELS = ["Documento", "Cotización", "Entrega", "Pagar"];

export const Stepper = ({ step }) => (
  <div className="pt-6 pb-6">
    <div className="flex items-center">
      {LABELS.map((l, i) => (
        <div key={i} className="flex items-center flex-1 last:flex-none">
          <div className="flex flex-col items-center">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                i < step
                  ? "bg-accent-500 text-white"
                  : i === step
                    ? "bg-brand-100 text-brand-600 ring-2 ring-brand-500 ring-offset-2"
                    : "bg-slate-100 text-slate-400"
              }`}
            >
              {i < step ? (
                <Icon name="check" size={14} color="white" strokeWidth={3} />
              ) : (
                i + 1
              )}
            </div>
            <span
              className={`text-[10px] font-semibold mt-1.5 ${i <= step ? "text-brand-900" : "text-slate-300"}`}
            >
              {l}
            </span>
          </div>
          {i < 3 && (
            <div
              className={`flex-1 h-0.5 mx-2 mt-[-12px] rounded ${i < step ? "bg-accent-500" : "bg-slate-100"}`}
            />
          )}
        </div>
      ))}
    </div>
  </div>
);
