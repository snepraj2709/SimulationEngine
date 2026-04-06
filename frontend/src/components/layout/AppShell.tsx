import { PropsWithChildren } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuthStore } from "@/store/auth-store";

interface AppShellProps extends PropsWithChildren {
  title: string;
  subtitle?: string;
}

export function AppShell({ title, subtitle, children }: AppShellProps) {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const clearSession = useAuthStore((state) => state.clearSession);

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-6 py-4">
          <div className="flex items-center gap-4">
            <Link to="/dashboard" className="rounded-full border border-slate-300 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-slate-700">
              Decision Engine
            </Link>
            <div>
              <h1 className="text-xl font-semibold text-slate-950">{title}</h1>
              {subtitle ? <p className="text-sm text-slate-600">{subtitle}</p> : null}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-slate-600 sm:inline">{user?.full_name}</span>
            <button
              type="button"
              onClick={() => {
                clearSession();
                navigate("/login");
              }}
              className="rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:bg-slate-100"
            >
              Log out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
    </div>
  );
}
