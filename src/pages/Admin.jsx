import { useEffect, useState } from "react";
import { supabase } from "../lib/supabase";
import { useAuth } from "../contexts/AuthContext";
import { Navbar } from "../components/Navbar";
import { Icon } from "../components/Icon";

const STATUS_COLORS = {
  pending_payment: "bg-amber-100 text-amber-700",
  paid: "bg-green-100 text-green-700",
  processing: "bg-blue-100 text-blue-700",
  translating: "bg-blue-100 text-blue-700",
  reviewing: "bg-purple-100 text-purple-700",
  ready: "bg-accent-100 text-accent-700",
  delivered: "bg-green-100 text-green-700",
  done: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

export function Admin() {
  const { user, loading: authLoading } = useAuth();
  const [tab, setTab] = useState("orders");
  const [orders, setOrders] = useState([]);
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingConfig, setEditingConfig] = useState(null);
  const [editValue, setEditValue] = useState("");

  useEffect(() => {
    if (authLoading) return;
    loadData();
  }, [authLoading]);

  async function loadData() {
    setLoading(true);
    const [ordersRes, configRes] = await Promise.all([
      supabase.from("orders").select("*").order("created_at", { ascending: false }),
      supabase.from("config").select("*"),
    ]);
    setOrders(ordersRes.data || []);
    setConfigs(configRes.data || []);
    setLoading(false);
  }

  async function updateOrderStatus(orderId, newStatus) {
    await supabase.from("orders").update({ status: newStatus }).eq("id", orderId);
    loadData();
  }

  async function saveConfig(key) {
    try {
      const parsed = JSON.parse(editValue);
      await supabase
        .from("config")
        .update({ value: parsed, updated_at: new Date().toISOString() })
        .eq("key", key);
      setEditingConfig(null);
      loadData();
    } catch {
      alert("JSON inválido");
    }
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
        <Navbar />
        <div className="flex items-center justify-center py-32">
          <div className="animate-spin w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <Navbar />
      <div className="max-w-4xl mx-auto px-5 py-8">
        <h1 className="text-xl font-bold text-brand-900 mb-6">
          Panel de administración
        </h1>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          {["orders", "config"].map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                tab === t
                  ? "bg-brand-600 text-white"
                  : "bg-white text-slate-500 border border-slate-200"
              }`}
            >
              {t === "orders" ? `Órdenes (${orders.length})` : "Configuración"}
            </button>
          ))}
          <button
            onClick={loadData}
            className="ml-auto px-3 py-2 rounded-lg text-sm text-slate-500 border border-slate-200 hover:bg-slate-50"
          >
            Recargar
          </button>
        </div>

        {tab === "orders" && (
          <div className="space-y-3">
            {orders.length === 0 && (
              <p className="text-sm text-slate-400 text-center py-8">
                No hay órdenes todavía
              </p>
            )}
            {orders.map((o) => (
              <div
                key={o.id}
                className="bg-white rounded-xl border border-slate-100 shadow-sm p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono text-slate-400">
                      #{o.id.substring(0, 8)}
                    </span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-semibold ${STATUS_COLORS[o.status] || "bg-slate-100 text-slate-500"}`}
                    >
                      {o.status}
                    </span>
                  </div>
                  <span className="text-sm font-bold text-brand-900">
                    ${o.total_uyu?.toLocaleString()} UYU
                  </span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-slate-500">
                  <span>{o.file_name}</span>
                  <span>{o.delivery_email}</span>
                  <span>{o.word_count?.toLocaleString()} palabras</span>
                  <span>{new Date(o.created_at).toLocaleDateString()}</span>
                </div>
                <div className="flex gap-1.5 mt-3">
                  {["paid", "processing", "translating", "reviewing", "ready", "done"].map(
                    (s) => (
                      <button
                        key={s}
                        onClick={() => updateOrderStatus(o.id, s)}
                        disabled={o.status === s}
                        className={`text-[10px] px-2 py-1 rounded font-semibold transition-all ${
                          o.status === s
                            ? "bg-brand-600 text-white"
                            : "bg-slate-50 text-slate-400 hover:bg-slate-100"
                        }`}
                      >
                        {s}
                      </button>
                    )
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === "config" && (
          <div className="space-y-3">
            {configs.map((c) => (
              <div
                key={c.key}
                className="bg-white rounded-xl border border-slate-100 shadow-sm p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <span className="text-sm font-bold text-brand-900 font-mono">
                      {c.key}
                    </span>
                    {c.description && (
                      <span className="text-xs text-slate-400 ml-2">
                        {c.description}
                      </span>
                    )}
                  </div>
                  {editingConfig === c.key ? (
                    <div className="flex gap-1">
                      <button
                        onClick={() => saveConfig(c.key)}
                        className="text-xs px-2 py-1 bg-accent-500 text-white rounded font-semibold"
                      >
                        Guardar
                      </button>
                      <button
                        onClick={() => setEditingConfig(null)}
                        className="text-xs px-2 py-1 bg-slate-100 text-slate-500 rounded font-semibold"
                      >
                        Cancelar
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => {
                        setEditingConfig(c.key);
                        setEditValue(JSON.stringify(c.value, null, 2));
                      }}
                      className="text-xs px-2 py-1 bg-slate-50 text-slate-500 rounded font-semibold hover:bg-slate-100"
                    >
                      Editar
                    </button>
                  )}
                </div>
                {editingConfig === c.key ? (
                  <textarea
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    className="w-full font-mono text-xs bg-slate-50 rounded-lg p-3 border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-400"
                    rows={4}
                  />
                ) : (
                  <pre className="text-xs text-slate-500 bg-slate-50 rounded-lg p-3 overflow-x-auto">
                    {JSON.stringify(c.value, null, 2)}
                  </pre>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
