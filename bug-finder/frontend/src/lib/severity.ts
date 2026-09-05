import type { Bug, Severity } from "./api";

export const SEVERITY_ORDER: Severity[] = ["Critical", "High", "Medium", "Low", "Info"];

export function severityColor(sev: Severity): string {
  return {
    Critical: "bg-rose-500/20 text-rose-300 ring-rose-400/40",
    High: "bg-amber-500/20 text-amber-300 ring-amber-400/40",
    Medium: "bg-orange-500/20 text-orange-300 ring-orange-400/40",
    Low: "bg-blue-400/20 text-blue-300 ring-blue-400/40",
    Info: "bg-teal-400/20 text-teal-300 ring-teal-400/40",
  }[sev];
}

export function severityDot(sev: Severity): string {
  return {
    Critical: "bg-rose-400",
    High: "bg-amber-400",
    Medium: "bg-orange-400",
    Low: "bg-blue-400",
    Info: "bg-teal-400",
  }[sev];
}

export function bugLabel(b: Bug): string {
  return `[${b.source}] ${b.category ?? ""} ${b.title}`.trim();
}
