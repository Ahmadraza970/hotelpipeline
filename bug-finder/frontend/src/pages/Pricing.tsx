import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { setPremium } from "../lib/premium";
import { Header } from "../components/Header";

interface Plan {
  id: string;
  name: string;
  price: string;
  tagline: string;
  featured: boolean;
  features: string[];
}

const PLANS: Plan[] = [
  {
    id: "free",
    name: "Free",
    price: "$0",
    tagline: "For quick debugging of small snippets.",
    featured: false,
    features: ["Lint-level findings", "500 lines / month", "Up to 3 files / scan", "Export .patch"],
  },
  {
    id: "pro",
    name: "Pro",
    price: "$12/mo",
    tagline: "For daily coding and code review.",
    featured: true,
    features: ["AI semantic findings", "AI fix generator (unlimited)", "GitHub PR creation", "2000 lines / month", "10 files / scan", "Priority support"],
  },
  {
    id: "team",
    name: "Team",
    price: "$24/mo",
    tagline: "For teams shipping together.",
    featured: false,
    features: ["Everything in Pro", "Shared projects", "Team workspace", "Unlimited lines", "Role-based access"],
  },
];

export function Pricing() {
  const navigate = useNavigate();
  const [upgrading, setUpgrading] = useState<string | null>(null);
  const upgrade = (plan: string) => {
    setUpgrading(plan);
    // MVP: simulate checkout completion (no real billing). In production this
    // opens a Stripe/Checkout session and returns a signed token.
    setTimeout(() => {
      setPremium(plan === "pro" || plan === "team");
      setUpgrading(null);
      navigate("/");
    }, 700);
  };
  return (
    <>
      <Header />
      <main className="mx-auto max-w-5xl px-4 py-14 text-center">
        <h1 className="text-3xl font-extrabold tracking-tight text-white">Simple, fair pricing</h1>
        <p className="mt-3 text-slate-300">
          Start with the free tier — no card required. Pro unlocks AI-powered fixes.
        </p>
        <div className="mx-auto mt-10 grid gap-6 sm:grid-cols-3">
          {PLANS.map((p) => (
            <div
              key={p.id}
              className={
                "flex flex-col rounded-xl border p-6 text-left shadow-xl " +
                (p.featured
                  ? "border-brand ring-2 ring-brand bg-panel"
                  : "border-panel bg-panel")
              }
            >
              <h3 className="text-lg font-semibold text-white">{p.name}</h3>
              <p className="mt-1 text-sm text-slate-400">{p.tagline}</p>
              <p className="mt-4 text-3xl font-extrabold text-white">{p.price}</p>
              <ul className="mt-5 space-y-2 text-sm text-slate-300">
                {p.features.map((f) => (
                  <li key={f} className="flex items-center gap-2">
                    <span className="text-emerald-400">✓</span> {f}
                  </li>
                ))}
              </ul>
              <button
                onClick={() => upgrade(p.id)}
                disabled={p.id === "free" || !!upgrading}
                className={
                  "mt-6 rounded px-4 py-2 text-sm font-semibold text-white " +
                  (p.featured
                    ? "bg-brand hover:bg-brand-hover disabled:opacity-60"
                    : "bg-panel-2 hover:bg-panel disabled:opacity-60")
                }
              >
                {p.id === "free" ? "Current plan" : upgrading === p.id ? "Upgrading…" : "Upgrade"}
              </button>
            </div>
          ))}
        </div>
        <p className="mt-10 text-xs text-slate-500">
          Demo mode: clicking Upgrade enables Pro locally so you can preview the AI flow.
          Real billing is wired up in v1.1.
        </p>
      </main>
    </>
  );
}
