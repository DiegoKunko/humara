import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { Icon } from "./Icon";

export function AuthModal({ onClose }) {
  const { signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!email) return;
    setLoading(true);
    setError("");
    const { error: err } = await signIn(email);
    setLoading(false);
    if (err) {
      setError(err.message);
    } else {
      setSent(true);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm mx-4 p-6 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-600"
        >
          <Icon name="x" size={18} />
        </button>

        {sent ? (
          <div className="text-center py-4">
            <div className="w-14 h-14 gradient-brand rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Icon name="mail" size={24} color="white" />
            </div>
            <h3 className="text-lg font-bold text-brand-900">
              Revisá tu email
            </h3>
            <p className="text-sm text-slate-500 mt-2">
              Te enviamos un link de acceso a{" "}
              <strong className="text-brand-700">{email}</strong>
            </p>
          </div>
        ) : (
          <>
            <h3 className="text-lg font-bold text-brand-900 mb-1">
              Ingresar
            </h3>
            <p className="text-sm text-slate-500 mb-5">
              Ingresá tu email y te enviamos un link de acceso.
            </p>
            <form onSubmit={handleSubmit} className="space-y-3">
              <input
                type="email"
                placeholder="tu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-transparent"
                autoFocus
              />
              {error && (
                <p className="text-xs text-red-500">{error}</p>
              )}
              <button
                type="submit"
                disabled={loading || !email}
                className="w-full py-3 btn-primary rounded-xl text-sm font-semibold disabled:opacity-50"
              >
                {loading ? "Enviando..." : "Enviar link de acceso"}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
