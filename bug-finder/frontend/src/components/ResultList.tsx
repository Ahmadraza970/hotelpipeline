import type { Bug } from "../lib/api";
import { severityDot } from "../lib/severity";

interface Props {
  bugs: Bug[];
  selectedId: string | null;
  onSelect: (b: Bug | null) => void;
  activeFile: string;
}

export function ResultList({ bugs, selectedId, onSelect, activeFile }: Props) {
  const forFile = bugs.filter((b) => b.file === activeFile);
  if (bugs.length === 0) {
    return (
      <div className="p-4 text-sm text-slate-400">
        No bugs. <span className="cursor-pointer text-brand underline" onClick={() => onSelect(null)}>Clear selection</span>.
      </div>
    );
  }
  const bySeverity = (s: string) => bugs.filter((b) => b.severity === s);
  return (
    <div className="space-y-4 p-3 text-sm">
      {forFile.length > 0 && (
        <div>
          <div className="mb-1 text-xs font-semibold text-slate-400">In {activeFile}</div>
          {forFile.map((b) => (
            <ResultRow key={b.id} bug={b} selected={b.id === selectedId} onSelect={onSelect} />
          ))}
        </div>
      )}
      {bugs.filter((b) => b.file !== activeFile).length > 0 && (
        <div>
          <div className="mb-1 text-xs font-semibold text-slate-400">Other files</div>
          {bugs
            .filter((b) => b.file !== activeFile)
            .map((b) => (
              <ResultRow key={b.id} bug={b} selected={b.id === selectedId} onSelect={onSelect} />
            ))}
        </div>
      )}
      <div className="border-t border-panel pt-3 text-xs text-slate-400">
        Total: {bugs.length} · Critical: {bySeverity("Critical").length}, High:{" "}
        {bySeverity("High").length}, Medium: {bySeverity("Medium").length}, Low:{" "}
        {bySeverity("Low").length}, Info: {bySeverity("Info").length}.
      </div>
    </div>
  );
}

function ResultRow({ bug, selected, onSelect }: { bug: Bug; selected: boolean; onSelect: (b: Bug | null) => void }) {
  return (
    <button
      onClick={() => onSelect(bug)}
      className={
        "mb-2 w-full text-left rounded p-2 text-left transition " +
        (selected ? "ring-2 ring-brand bg-panel-2" : "hover:bg-panel-2/60")
      }
    >
      <div className="flex items-start gap-2">
        <span className={`mt-0.5 h-2.5 w-2.5 shrink-0 rounded-full ${severityDot(bug.severity)}`} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline gap-1 text-xs text-slate-400">
            <span className="font-mono">{bug.file}:{bug.line}</span>
            <span className={`inline-block rounded px-1.5 py-0.25 text-[10px] font-semibold uppercase ${severityPill(bug.severity)}`}>
              {bug.severity}
            </span>
            <span className="rounded bg-panel-2 px-1 py-0.25 text-xs">{bug.source}</span>
          </div>
          <div className="mt-0.5 font-medium text-slate-100">{bug.title}</div>
          <div className="mt-0.5 line-clamp-2 text-slate-300">{bug.description}</div>
          {bug.confidence < 100 && (
            <div className="mt-0.5 w-16 rounded bg-panel-2">
              <div className="h-1.5 rounded bg-brand" style={{ width: `${bug.confidence}%` }} />
              <span className="sr-only">{bug.confidence}% confidence</span>
            </div>
          )}
        </div>
      </div>
    </button>
  );
}

function severityPill(s: string) {
  return {
    Critical: "bg-rose-500/20 text-rose-300",
    High: "bg-amber-500/20 text-amber-300",
    Medium: "bg-orange-500/20 text-orange-300",
    Low: "bg-blue-400/20 text-blue-300",
    Info: "bg-teal-400/20 text-teal-300",
  }[s] ?? "bg-slate-400/20 text-slate-300";
}
