import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { supabase } from "../lib/supabase";
import { Navbar } from "../components/Navbar";
import { Icon } from "../components/Icon";

const STATUS_LABELS = {
  pending_payment: { label: "Pendiente de pago", color: "bg-amber-100 text-amber-700" },
  paid: { label: "Pagado", color: "bg-green-100 text-green-700" },
  processing: { label: "En proceso", color: "bg-blue-100 text-blue-700" },
  translating: { label: "Traduciendo", color: "bg-blue-100 text-blue-700" },
  reviewing: { label: "En revisión", color: "bg-purple-100 text-purple-700" },
  ready: { label: "Listo para descargar", color: "bg-accent-100 text-accent-700" },
  delivered: { label: "Entregado", color: "bg-green-100 text-green-700" },
  done: { label: "Completado", color: "bg-green-100 text-green-700" },
  failed: { label: "Error", color: "bg-red-100 text-red-700" },
};

export function OrderStatus() {
  const { id } = useParams();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase
      .from("orders")
      .select("*")
      .eq("id", id)
      .single()
      .then(({ data }) => {
        setOrder(data);
        setLoading(false);
      });

    // Realtime subscription
    const channel = supabase
      .channel(`order-${id}`)
      .on(
        "postgres_changes",
        { event: "UPDATE", schema: "public", table: "orders", filter: `id=eq.${id}` },
        (payload) => setOrder(payload.new)
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
        <Navbar />
        <div className="flex items-center justify-center py-32">
          <div className="animate-spin w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full" />
        </div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
        <Navbar />
        <div className="max-w-md mx-auto text-center py-32 px-5">
          <h2 className="text-xl font-bold text-brand-900">Orden no encontrada</h2>
          <Link to="/" className="text-sm text-brand-500 mt-4 block">
            Volver al inicio
          </Link>
        </div>
      </div>
    );
  }

  const st = STATUS_LABELS[order.status] || STATUS_LABELS.processing;

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <Navbar />
      <div className="max-w-md mx-auto px-5 py-12">
        <div className="text-center mb-8">
          <h2 className="text-xl font-bold text-brand-900">Estado del pedido</h2>
          <p className="text-xs text-slate-400 mt-1 font-mono">#{id.substring(0, 8)}</p>
        </div>

        <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold mx-auto mb-6 ${st.color}`}>
          {st.label}
        </div>

        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
          {[
            ["Documento", order.file_name],
            ["Palabras", order.word_count?.toLocaleString() || "N/A"],
            ["Total", `$${order.total_uyu?.toLocaleString()} UYU`],
            ["Entrega", order.delivery_hours === 0 ? "En el día" : `${order.delivery_hours} horas`],
            ["Email", order.delivery_email],
          ].map(([k, v], i) => (
            <div key={i} className="flex justify-between px-5 py-3 border-b border-slate-50 last:border-0 text-sm">
              <span className="text-slate-400">{k}</span>
              <span className="text-brand-900 font-medium">{v}</span>
            </div>
          ))}
        </div>

        {order.status === "ready" && order.output_path && (
          <button
            onClick={async () => {
              const { data } = await supabase.storage
                .from("documents")
                .createSignedUrl(order.output_path, 3600);
              if (data?.signedUrl) window.open(data.signedUrl);
            }}
            className="w-full mt-6 py-4 btn-primary rounded-2xl text-sm flex items-center justify-center gap-2"
          >
            <Icon name="download" size={16} color="white" />
            Descargar traducción
          </button>
        )}

        <Link
          to="/"
          className="block text-center mt-6 text-sm text-brand-500 hover:text-brand-600 font-medium"
        >
          Nueva traducción
        </Link>
      </div>
    </div>
  );
}
