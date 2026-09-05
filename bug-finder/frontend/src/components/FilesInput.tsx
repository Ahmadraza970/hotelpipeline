import { useState } from "react";

export interface FileEntry {
  name: string;
  content: string;
}

interface Props {
  value: FileEntry[];
  onChange: (files: FileEntry[]) => void;
  loadExample?: FileEntry[];
}

export function FilesInput({ value, onChange, loadExample }: Props) {
  const update = (idx: number, patch: Partial<FileEntry>) => {
    const next = [...value];
    next[idx] = { ...next[idx], ...patch };
    onChange(next);
  };
  const remove = (idx: number) => {
    const next = [...value];
    next.splice(idx, 1);
    onChange(next);
  };
  const add = () => onChange([...value, { name: "index.js", content: "" }]);

  return (
    <div className="space-y-3">
      {value.map((f, i) => (
        <div key={i} className="grid grid-cols-[140px_1fr_auto] items-start gap-2">
          <input
            type="text"
            placeholder="e.g. add.py"
            className="col-span-1 h-8 rounded bg-panel-2 border border-panel-2 text-slate-100 placeholder-slate-500 focus:border-brand focus:outline-none"
            value={f.name}
            onChange={(e) => update(i, { name: e.target.value })}
          />
          <textarea
            placeholder="paste code here..."
            className="col-span-1 min-h-[120px] w-full resize-y rounded bg-panel-2 border border-panel-2 text-slate-100 font-mono text-sm placeholder-slate-500 focus:border-brand focus:outline-none"
            value={f.content}
            onChange={(e) => update(i, { content: e.target.value })}
          />
          <button
            onClick={() => remove(i)}
            className="col-start-auto mt-1 h-7 w-7 shrink-0 rounded text-rose-300 hover:bg-rose-900/30"
            title="Remove file"
          >
            ✕
          </button>
        </div>
      ))}

      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <button
            type="button"
            onClick={add}
            className="rounded bg-panel-2 px-3 py-1.5 text-sm text-slate-200 hover:bg-panel"
          >
            + Add file
          </button>
          {loadExample && value.length === 0 && (
            <button
              type="button"
              onClick={() => onChange(loadExample)}
              className="rounded bg-brand px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-hover"
            >
              Load example
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export function useFileUpload(onFiles: (files: FileEntry[]) => void) {
  const [drag, setDrag] = useState(false);
  const handleFiles = (fileList: FileList | null) => {
    if (!fileList) return;
    Promise.all(
      Array.from(fileList).map(async (f) => ({ name: f.name, content: await f.text() })),
    ).then(onFiles);
  };
  return {
    drag,
    handlers: {
      onDragOver: (e: React.DragEvent) => {
        e.preventDefault();
        setDrag(true);
      },
      onDragLeave: () => setDrag(false),
      onDrop: (e: React.DragEvent) => {
        e.preventDefault();
        setDrag(false);
        handleFiles(e.dataTransfer.files);
      },
    },
    inputProps: {
      type: "file" as const,
      multiple: true,
      accept: ".py,.js,.jsx,.ts,.tsx",
      onChange: (e: React.ChangeEvent<HTMLInputElement>) => handleFiles(e.target.files),
    },
  };
}
