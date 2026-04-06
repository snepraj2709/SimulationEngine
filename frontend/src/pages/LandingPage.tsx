import { Link } from "react-router-dom";

export function LandingPage() {
  return (
    <div className="min-h-screen px-6 py-10">
      <div className="mx-auto flex max-w-7xl flex-col gap-10">
        <header className="flex items-center justify-between">
          <div className="rounded-full border border-slate-300 bg-white/70 px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-700">
            Decision Simulation Engine
          </div>
          <div className="flex gap-3">
            <Link to="/login" className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700">
              Log in
            </Link>
            <Link to="/register" className="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white">
              Get started
            </Link>
          </div>
        </header>

        <section className="grid gap-8 lg:grid-cols-[1.4fr_1fr]">
          <div className="panel overflow-hidden p-8">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-teal-700">Growth, Product, Pricing, Strategy</p>
            <h1 className="mt-4 max-w-3xl text-5xl font-semibold leading-tight text-slate-950">
              Simulate how customer segments react before you ship the pricing or product change.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
              Submit a product URL. The engine extracts positioning and monetization signals, generates ICPs, proposes realistic business scenarios, and produces explainable downstream outcome simulations.
            </p>
            <div className="mt-8 flex flex-wrap gap-4">
              <Link to="/register" className="rounded-full bg-slate-950 px-6 py-3 text-sm font-semibold text-white">
                Build a simulation
              </Link>
              <Link to="/login" className="rounded-full border border-slate-300 px-6 py-3 text-sm font-semibold text-slate-700">
                Open dashboard
              </Link>
            </div>
          </div>
          <div className="panel p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Included demo</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">Netflix premium price increase in India</h2>
            <div className="mt-6 grid gap-3">
              {[
                "3 default scenarios generated immediately",
                "5 deterministic ICPs with weighted drivers",
                "Retention, downgrade, upgrade, churn, and revenue projections",
                "Second-order effects and feedback capture",
              ].map((item) => (
                <div key={item} className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
                  {item}
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
