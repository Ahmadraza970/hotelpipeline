import { useEffect, useState } from "react";
import { health } from "../lib/api";

export function HealthBadge() {
  const [state, setState] = useState<"loading" | "ok" | "down">("loading");
  useEffect(() => {
    health()
      .then(() => setState("ok"))
      .catch(() => setState("down"));
  }, []);
  const dot =
    state === "ok"
      ? "bg-emerald-400"
      : state === "down"
        ? "bg-rose-400"
        : "bg-slate-400";
  const label = state === "ok" ? "API online" : state === "down" ? "API offline" : "Checking…";
  return (
    <div className="inline-flex items-center gap-2 rounded-full bg-panel px-3 py-1 text-xs text-slate-300">
      <span className={`h-2 w-2 rounded-full ${dot}`} />
      {label}
    </div>
  );
}
