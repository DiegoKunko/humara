import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { AuthModal } from "./AuthModal";
import { Icon } from "./Icon";

export const Navbar = () => {
  const { user, signOut } = useAuth();
  const [showAuth, setShowAuth] = useState(false);

  return (
    <>
      <nav className="border-b border-slate-100 bg-white/80 backdrop-blur-md sticky top-0 z-20">
        <div className="max-w-5xl mx-auto px-5 md:px-8 h-16 flex items-center justify-between">
          <Link to="/">
            <img src="/logo-humara.png" alt="Humara" className="h-16" />
          </Link>
          <div className="flex items-center gap-4">
            <Link
              to="/faq"
              className="hidden md:block text-xs font-semibold text-slate-500 hover:text-brand-600 transition-colors"
            >
              FAQ
            </Link>
            <Link
              to="/about"
              className="hidden md:block text-xs font-semibold text-slate-500 hover:text-brand-600 transition-colors"
            >
              Cómo funciona
            </Link>
            <div className="flex items-center gap-1.5 bg-accent-50 text-accent-600 px-3 py-1.5 rounded-full">
              <Icon name="shield" size={13} />
              <span className="text-xs font-semibold">Certificado</span>
            </div>
            {user ? (
              <button
                onClick={signOut}
                className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-600 transition-colors"
              >
                <Icon name="logout" size={14} />
                <span className="hidden md:inline">Salir</span>
              </button>
            ) : (
              <button
                onClick={() => setShowAuth(true)}
                className="text-xs font-semibold text-brand-600 hover:text-brand-700 transition-colors"
              >
                Ingresar
              </button>
            )}
          </div>
        </div>
      </nav>
      {showAuth && <AuthModal onClose={() => setShowAuth(false)} />}
    </>
  );
};
