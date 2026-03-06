import { Icon } from "./Icon";

export const BottomBar = ({
  step,
  canNext,
  onBack,
  onNext,
  total,
  file,
  analyzing,
}) => (
  <div className="fixed bottom-0 left-0 right-0 bg-white/90 backdrop-blur-xl border-t border-slate-100 z-20">
    <div className="max-w-2xl mx-auto px-5 md:px-8 h-20 flex items-center justify-between">
      {step > 0 ? (
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-brand-600 font-semibold transition-colors"
        >
          <Icon name="back" size={16} />
          Atrás
        </button>
      ) : (
        <div className="text-xs text-slate-300">
          {file && !analyzing && (
            <span className="font-semibold text-brand-900">
              ${total.toLocaleString()} UYU
            </span>
          )}
        </div>
      )}
      {step < 3 && (
        <button
          onClick={onNext}
          disabled={!canNext}
          className={`flex items-center gap-2 px-7 py-3.5 rounded-xl text-sm font-bold transition-all ${
            canNext
              ? "btn-primary"
              : "bg-slate-100 text-slate-300 cursor-not-allowed"
          }`}
        >
          Continuar{" "}
          <Icon
            name="arrow"
            size={15}
            color={canNext ? "white" : "#cbd5e1"}
            strokeWidth={2.5}
          />
        </button>
      )}
    </div>
  </div>
);
