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

const ADMIN_EMAILS = [
  "andrea.faraco@gmail.com",
  "dpraderi@gmail.com",
  "amalvasio@must.com.uy",
];

function getConfigNumber(configs, key, fallback) {
  const row = configs.find((c) => c.key === key);
  if (!row) return fallback;
  const v = row.value;
  const n = typeof v === "number" ? v : parseFloat(v);
  return Number.isFinite(n) ? n : fallback;
}

function computeCostMetrics(orders, configs) {
  const usdToUyu = getConfigNumber(configs, "usd_to_uyu_rate", 40);
  const andreaRate = getConfigNumber(configs, "andrea_rate_uyu_per_hour", 600);
  const andreaMin1k = getConfigNumber(
    configs,
    "andrea_minutes_per_1000_words",
    15
  );

  const rows = orders
    .filter((o) => o.total_uyu != null)
    .map((o) => {
      const revenue = Number(o.total_uyu) || 0;
      const aiCostUsd = Number(o.ai_cost_usd) || 0;
      const aiCostUyu = aiCostUsd * usdToUyu;
      const words = Number(o.word_count) || 0;
      const humanMinutes = (words / 1000) * andreaMin1k;
      const humanCostUyu = (humanMinutes / 60) * andreaRate;
      const margenUyu = revenue - aiCostUyu - humanCostUyu;
      const margenPct = revenue > 0 ? (margenUyu / revenue) * 100 : null;
      return {
        ...o,
        _revenue: revenue,
        _aiCostUsd: aiCostUsd,
        _aiCostUyu: aiCostUyu,
        _humanMinutes: humanMinutes,
        _humanCostUyu: humanCostUyu,
        _margenUyu: margenUyu,
        _margenPct: margenPct,
      };
    });

  const totalRevenue = rows.reduce((a, r) => a + r._revenue, 0);
  const totalAiUsd = rows.reduce((a, r) => a + r._aiCostUsd, 0);
  const totalAiUyu = totalAiUsd * usdToUyu;
  const totalHumanUyu = rows.reduce((a, r) => a + r._humanCostUyu, 0);
  const totalMargenUyu = totalRevenue - totalAiUyu - totalHumanUyu;
  const marginPct = totalRevenue > 0 ? (totalMargenUyu / totalRevenue) * 100 : 0;

  // Distribución de score
  const withScore = rows.filter((r) => r.review_score != null);
  const scoreAbove90 = withScore.filter((r) => r.review_score >= 0.9).length;
  const scoreBelow90 = withScore.filter((r) => r.review_score < 0.9).length;
  const avgScore =
    withScore.length > 0
      ? withScore.reduce((a, r) => a + Number(r.review_score), 0) /
        withScore.length
      : null;

  // Órdenes de bajo margen
  const lowMargin = rows
    .filter((r) => r._margenPct != null && r._margenPct < 50)
    .sort((a, b) => a._margenPct - b._margenPct);

  return {
    rows,
    usdToUyu,
    andreaRate,
    andreaMin1k,
    totalRevenue,
    totalAiUsd,
    totalAiUyu,
    totalHumanUyu,
    totalMargenUyu,
    marginPct,
    scoreAbove90,
    scoreBelow90,
    avgScore,
    lowMargin,
    numOrders: rows.length,
  };
}

function formatUYU(n) {
  if (n == null || !Number.isFinite(n)) return "—";
  return `$${Math.round(n).toLocaleString("es-UY")}`;
}

function formatUSD(n) {
  if (n == null || !Number.isFinite(n)) return "—";
  return `$${n.toFixed(2)}`;
}

export function Admin() {
  const { user, loading: authLoading, signIn } = useAuth();
  const [tab, setTab] = useState("orders");
  const [orders, setOrders] = useState([]);
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingConfig, setEditingConfig] = useState(null);
  const [editValue, setEditValue] = useState("");
  const [loginEmail, setLoginEmail] = useState("");
  const [loginSent, setLoginSent] = useState(false);

  const isAdmin = user && ADMIN_EMAILS.includes(user.email);

  const metrics = computeCostMetrics(orders, configs);

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

  if (authLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
        <Navbar />
        <div className="flex items-center justify-center py-32">
          <div className="animate-spin w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full" />
        </div>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
        <Navbar />
        <div className="max-w-sm mx-auto px-5 py-20 text-center">
          <h1 className="text-xl font-bold text-brand-900 mb-4">
            Acceso restringido
          </h1>
          {loginSent ? (
            <p className="text-sm text-slate-500">
              Te enviamos un link de acceso a <strong>{loginEmail}</strong>.
              Revisá tu email.
            </p>
          ) : (
            <>
              <p className="text-sm text-slate-500 mb-6">
                Ingresá tu email autorizado para acceder al panel.
              </p>
              <input
                type="email"
                placeholder="tu@email.com"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-brand-400"
              />
              <button
                onClick={async () => {
                  if (!ADMIN_EMAILS.includes(loginEmail.toLowerCase())) {
                    alert("Email no autorizado");
                    return;
                  }
                  const { error } = await signIn(loginEmail);
                  if (!error) setLoginSent(true);
                }}
                className="w-full px-4 py-3 rounded-xl bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700 transition-colors"
              >
                Ingresar
              </button>
            </>
          )}
        </div>
      </div>
    );
  }

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

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <Navbar />
      <div className="max-w-4xl mx-auto px-5 py-8">
        <h1 className="text-xl font-bold text-brand-900 mb-6">
          Panel de administración
        </h1>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          {["orders", "costs", "config"].map((t) => {
            const labels = {
              orders: `Órdenes (${orders.length})`,
              costs: "Costos y margen",
              config: "Configuración",
            };
            return (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                  tab === t
                    ? "bg-brand-600 text-white"
                    : "bg-white text-slate-500 border border-slate-200"
                }`}
              >
                {labels[t]}
              </button>
            );
          })}
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

        {tab === "costs" && (
          <div className="space-y-6">
            {/* KPIs */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4">
                <p className="text-[11px] text-slate-400 uppercase tracking-wide mb-1">
                  Ingresos
                </p>
                <p className="text-xl font-bold text-brand-900">
                  {formatUYU(metrics.totalRevenue)}
                </p>
                <p className="text-[11px] text-slate-400 mt-1">
                  {metrics.numOrders} órdenes
                </p>
              </div>
              <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4">
                <p className="text-[11px] text-slate-400 uppercase tracking-wide mb-1">
                  Costo IA
                </p>
                <p className="text-xl font-bold text-slate-700">
                  {formatUYU(metrics.totalAiUyu)}
                </p>
                <p className="text-[11px] text-slate-400 mt-1">
                  {formatUSD(metrics.totalAiUsd)} · @ {metrics.usdToUyu} UYU
                </p>
              </div>
              <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4">
                <p className="text-[11px] text-slate-400 uppercase tracking-wide mb-1">
                  Costo humano
                </p>
                <p className="text-xl font-bold text-slate-700">
                  {formatUYU(metrics.totalHumanUyu)}
                </p>
                <p className="text-[11px] text-slate-400 mt-1">
                  estimación Andrea
                </p>
              </div>
              <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4">
                <p className="text-[11px] text-slate-400 uppercase tracking-wide mb-1">
                  Margen
                </p>
                <p
                  className={`text-xl font-bold ${
                    metrics.marginPct >= 50
                      ? "text-green-600"
                      : metrics.marginPct >= 20
                        ? "text-amber-600"
                        : "text-red-600"
                  }`}
                >
                  {formatUYU(metrics.totalMargenUyu)}
                </p>
                <p className="text-[11px] text-slate-400 mt-1">
                  {metrics.marginPct.toFixed(1)}% del ingreso
                </p>
              </div>
            </div>

            {/* Quality metrics */}
            <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-bold text-brand-900">
                  Calidad automática
                </h3>
                <span className="text-[11px] text-slate-400">
                  Meta: 90% sin intervención manual
                </span>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <p className="text-[11px] text-slate-400">Score promedio</p>
                  <p className="text-lg font-bold text-slate-700">
                    {metrics.avgScore != null
                      ? `${(metrics.avgScore * 100).toFixed(1)}%`
                      : "—"}
                  </p>
                </div>
                <div>
                  <p className="text-[11px] text-slate-400">Sobre 90%</p>
                  <p className="text-lg font-bold text-green-600">
                    {metrics.scoreAbove90}
                  </p>
                </div>
                <div>
                  <p className="text-[11px] text-slate-400">Bajo 90% (warning)</p>
                  <p className="text-lg font-bold text-red-600">
                    {metrics.scoreBelow90}
                  </p>
                </div>
              </div>
            </div>

            {/* Assumptions panel */}
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
              <p className="text-[11px] font-bold text-amber-800 uppercase tracking-wide mb-2">
                Supuestos del cálculo
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs text-amber-900">
                <div>
                  Tarifa Andrea: <strong>${metrics.andreaRate}/hora UYU</strong>
                </div>
                <div>
                  Tiempo estimado: <strong>{metrics.andreaMin1k} min / 1000 palabras</strong>
                </div>
                <div>
                  TC USD→UYU: <strong>{metrics.usdToUyu}</strong>
                </div>
              </div>
              <p className="text-[11px] text-amber-700 mt-2">
                Ajustá estos valores desde la tab <strong>Configuración</strong>{" "}
                (keys: <code>andrea_rate_uyu_per_hour</code>,{" "}
                <code>andrea_minutes_per_1000_words</code>,{" "}
                <code>usd_to_uyu_rate</code>).
              </p>
            </div>

            {/* Low margin alert */}
            {metrics.lowMargin.length > 0 && (
              <div className="bg-white rounded-xl border border-red-200 shadow-sm p-4">
                <h3 className="text-sm font-bold text-red-700 mb-3">
                  ⚠ Órdenes con margen bajo (&lt; 50%)
                </h3>
                <div className="space-y-2">
                  {metrics.lowMargin.slice(0, 5).map((o) => (
                    <div
                      key={o.id}
                      className="flex items-center justify-between text-xs border-b border-slate-100 pb-2 last:border-0"
                    >
                      <div className="flex-1">
                        <span className="font-mono text-slate-400">
                          #{o.id.substring(0, 8)}
                        </span>
                        <span className="ml-2 text-slate-600">{o.file_name}</span>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold text-red-600">
                          {o._margenPct.toFixed(0)}%
                        </div>
                        <div className="text-[10px] text-slate-400">
                          {formatUYU(o._margenUyu)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Per-order cost breakdown */}
            <div className="bg-white rounded-xl border border-slate-100 shadow-sm">
              <div className="p-4 border-b border-slate-100">
                <h3 className="text-sm font-bold text-brand-900">
                  Desglose por orden
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead className="bg-slate-50">
                    <tr className="text-left text-slate-500">
                      <th className="px-3 py-2 font-semibold">Orden</th>
                      <th className="px-3 py-2 font-semibold text-right">Palabras</th>
                      <th className="px-3 py-2 font-semibold text-right">Ingreso</th>
                      <th className="px-3 py-2 font-semibold text-right">Costo IA</th>
                      <th className="px-3 py-2 font-semibold text-right">Costo humano</th>
                      <th className="px-3 py-2 font-semibold text-right">Margen</th>
                      <th className="px-3 py-2 font-semibold text-right">Score</th>
                      <th className="px-3 py-2 font-semibold text-right">Intentos</th>
                    </tr>
                  </thead>
                  <tbody>
                    {metrics.rows.length === 0 && (
                      <tr>
                        <td colSpan={8} className="px-3 py-6 text-center text-slate-400">
                          No hay órdenes con datos de costo todavía
                        </td>
                      </tr>
                    )}
                    {metrics.rows.map((o) => (
                      <tr key={o.id} className="border-b border-slate-50 last:border-0">
                        <td className="px-3 py-2">
                          <div className="font-mono text-slate-400">
                            #{o.id.substring(0, 8)}
                          </div>
                          <div className="text-slate-600 truncate max-w-[180px]">
                            {o.file_name}
                          </div>
                        </td>
                        <td className="px-3 py-2 text-right text-slate-600">
                          {(Number(o.word_count) || 0).toLocaleString()}
                        </td>
                        <td className="px-3 py-2 text-right font-semibold text-slate-700">
                          {formatUYU(o._revenue)}
                        </td>
                        <td className="px-3 py-2 text-right text-slate-500">
                          {formatUYU(o._aiCostUyu)}
                        </td>
                        <td className="px-3 py-2 text-right text-slate-500">
                          {formatUYU(o._humanCostUyu)}
                        </td>
                        <td
                          className={`px-3 py-2 text-right font-semibold ${
                            o._margenPct == null
                              ? "text-slate-400"
                              : o._margenPct >= 50
                                ? "text-green-600"
                                : o._margenPct >= 20
                                  ? "text-amber-600"
                                  : "text-red-600"
                          }`}
                        >
                          {o._margenPct != null
                            ? `${o._margenPct.toFixed(0)}%`
                            : "—"}
                        </td>
                        <td className="px-3 py-2 text-right">
                          {o.review_score != null ? (
                            <span
                              className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                                o.review_score >= 0.9
                                  ? "bg-green-100 text-green-700"
                                  : "bg-red-100 text-red-700"
                              }`}
                            >
                              {(Number(o.review_score) * 100).toFixed(0)}%
                            </span>
                          ) : (
                            <span className="text-slate-300">—</span>
                          )}
                        </td>
                        <td className="px-3 py-2 text-right text-slate-500">
                          {o.review_attempts ?? "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Optimization insights */}
            <div className="bg-gradient-to-br from-brand-50 to-accent-50 rounded-xl border border-brand-100 p-5">
              <h3 className="text-sm font-bold text-brand-900 mb-3">
                Palancas de optimización
              </h3>
              <ul className="space-y-2 text-xs text-slate-700">
                <li className="flex gap-2">
                  <span className="text-brand-600">→</span>
                  <span>
                    <strong>Subir el % de jobs automáticos &gt;90%.</strong>{" "}
                    Cada job bajo el umbral consume tiempo de Andrea que podría
                    dedicarse a certificar más volumen. Hoy:{" "}
                    <strong>
                      {metrics.scoreAbove90}/{metrics.scoreAbove90 + metrics.scoreBelow90}
                    </strong>{" "}
                    pasan solos.
                  </span>
                </li>
                <li className="flex gap-2">
                  <span className="text-brand-600">→</span>
                  <span>
                    <strong>Reducir el tiempo de Andrea por mil palabras.</strong>{" "}
                    Hoy estimamos {metrics.andreaMin1k} min/1000. Cada minuto
                    menos es costo directo ahorrado — depende de cuánto feedback
                    de Andrea se incorpore al pipeline.
                  </span>
                </li>
                <li className="flex gap-2">
                  <span className="text-brand-600">→</span>
                  <span>
                    <strong>Subir precio en documentos complejos.</strong>{" "}
                    Documentos con tablas, OCR o multi-idioma cuestan más al
                    sistema. Identificalos en el ranking de margen bajo y
                    ajustá el pricing por tipo.
                  </span>
                </li>
                <li className="flex gap-2">
                  <span className="text-brand-600">→</span>
                  <span>
                    <strong>Cachear glosarios y terminología por cliente.</strong>{" "}
                    Clientes recurrentes (mismas empresas) deberían tener
                    glosarios dedicados que suban el score inicial y eviten
                    iteraciones del loop.
                  </span>
                </li>
              </ul>
            </div>
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
