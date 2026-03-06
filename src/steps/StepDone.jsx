import { Icon } from "../components/Icon";

export const StepDone = ({
  file,
  dir,
  words,
  docType,
  tier,
  deliveryHours,
  f,
  total,
  orderId,
  onReset,
}) => {
  const isPartida = docType === "partida_nacimiento";

  return (
    <div className="min-h-screen bg-gradient-to-b from-brand-50 via-white to-white flex items-center justify-center p-5">
      <div className="max-w-md w-full">
        <div className="text-center mb-10">
          <div className="w-20 h-20 bg-gradient-to-br from-accent-400 to-accent-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-accent-100">
            <Icon name="check" size={32} color="white" strokeWidth={3} />
          </div>
          <h2 className="text-2xl font-bold text-brand-900 tracking-tight">
            Pedido confirmado
          </h2>
          <p className="text-slate-500 text-sm mt-2">
            Tu traducción certificada está en proceso
          </p>
          {orderId && (
            <p className="text-xs text-slate-400 mt-1 font-mono">
              #{orderId.substring(0, 8)}
            </p>
          )}
        </div>
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
          {[
            [<Icon key="i" name="file" size={15} />, "Documento", file?.name],
            [
              <Icon key="i" name="globe" size={15} />,
              "Traducción",
              dir === "en-es" ? "Inglés a Español" : "Español a Inglés",
            ],
            [
              <Icon key="i" name="file" size={15} />,
              isPartida ? "Tipo" : "Palabras",
              isPartida ? "Partida de nacimiento" : words.toLocaleString(),
            ],
            [
              <Icon key="i" name="clock" size={15} />,
              "Entrega",
              deliveryHours === 0 ? "En el día" : `${deliveryHours} horas`,
            ],
            [
              <Icon key="i" name="home" size={15} />,
              "Dirección",
              `${f.address}, ${f.city}`,
            ],
          ].map(([ic, k, v], i) => (
            <div
              key={i}
              className="flex items-center justify-between px-5 py-3.5 border-b border-slate-50 last:border-0"
            >
              <span className="flex items-center gap-2 text-sm text-slate-400">
                {ic}
                {k}
              </span>
              <span className="text-sm text-brand-900 font-medium text-right max-w-[55%] truncate">
                {v}
              </span>
            </div>
          ))}
          <div className="flex items-center justify-between px-5 py-5 gradient-brand text-white">
            <span className="font-semibold">Total</span>
            <span className="text-2xl font-bold">
              ${total.toLocaleString()} UYU
            </span>
          </div>
        </div>
        <p className="text-center text-xs text-slate-400 mt-6">
          Recibirás actualizaciones en {f.email}
        </p>
        <button
          onClick={onReset}
          className="block mx-auto mt-4 text-sm text-brand-500 hover:text-brand-600 font-medium"
        >
          Nueva traducción
        </button>
      </div>
    </div>
  );
};
