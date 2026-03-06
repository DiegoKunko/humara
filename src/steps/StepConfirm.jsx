import { useState } from "react";
import { Icon } from "../components/Icon";

export const StepConfirm = ({
  file,
  dir,
  words,
  docType,
  tier,
  deliveryHours,
  f,
  total,
  rate,
  onPay,
}) => {
  const [paying, setPaying] = useState(false);
  const isPartida = docType === "partida_nacimiento";

  const handlePay = async () => {
    setPaying(true);
    await onPay();
    setPaying(false);
  };

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-bold text-brand-900">
          Confirmar y pagar
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Revisá los detalles de tu pedido.
        </p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        {[
          [
            <Icon key="i" name="file" size={15} color="#2563eb" />,
            "Documento",
            file?.name,
          ],
          [
            <Icon key="i" name="globe" size={15} color="#2563eb" />,
            "Traducción",
            dir === "en-es" ? "Inglés a Español" : "Español a Inglés",
          ],
          isPartida
            ? [
                <Icon key="i" name="file" size={15} color="#2563eb" />,
                "Tipo",
                "Partida de nacimiento",
              ]
            : [
                <Icon key="i" name="scan" size={15} color="#2563eb" />,
                "Palabras",
                `${words.toLocaleString()} ($${rate}/pal)`,
              ],
          [
            <Icon key="i" name="clock" size={15} color="#2563eb" />,
            "Entrega",
            deliveryHours === 0 ? "En el día" : `${deliveryHours} horas`,
          ],
          [
            <Icon key="i" name="user" size={15} color="#2563eb" />,
            "Nombre",
            f.name,
          ],
          [
            <Icon key="i" name="home" size={15} color="#2563eb" />,
            "Dirección",
            `${f.address}, ${f.city}`,
          ],
          [
            <Icon key="i" name="mail" size={15} color="#2563eb" />,
            "Email",
            f.email,
          ],
        ].map(([ic, k, v], i) => (
          <div
            key={i}
            className="flex items-center justify-between px-5 py-3.5 border-b border-slate-50"
          >
            <span className="flex items-center gap-2.5 text-sm text-slate-400">
              {ic}
              {k}
            </span>
            <span className="text-sm text-brand-900 font-medium text-right max-w-[55%] truncate">
              {v}
            </span>
          </div>
        ))}
        <div className="px-5 py-5 gradient-brand flex items-center justify-between text-white">
          <span className="font-bold text-lg">Total</span>
          <span className="text-3xl font-extrabold">
            ${total.toLocaleString()} UYU
          </span>
        </div>
      </div>

      <p className="text-xs text-center text-slate-400">
        El precio puede ajustarse si el conteo de palabras difiere. Te
        notificamos antes de procesar.
      </p>

      <button
        onClick={handlePay}
        disabled={paying}
        className="w-full py-4 btn-primary rounded-2xl text-sm tracking-wide disabled:opacity-50"
      >
        {paying ? "Procesando..." : `Pagar $${total.toLocaleString()} UYU`}
      </button>

      <div className="flex items-center justify-center gap-4 text-xs text-slate-300 pb-4">
        <span className="flex items-center gap-1">
          <Icon name="lock" size={11} color="#cbd5e1" />
          SSL
        </span>
        <span className="flex items-center gap-1">
          <Icon name="shield" size={11} color="#cbd5e1" />
          Certificado
        </span>
        <span className="flex items-center gap-1">
          <Icon name="truck" size={11} color="#cbd5e1" />
          Asegurado
        </span>
      </div>
    </div>
  );
};
