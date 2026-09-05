import Editor, { useMonaco } from "@monaco-editor/react";
import { useEffect, useRef } from "react";

export interface MarkerInput {
  line: number;
  message: string;
  severity: "error" | "warning" | "info";
}

interface Props {
  value?: string;
  language?: string;
  file?: string;
  markers?: MarkerInput[];
  readOnly?: boolean;
  height?: string;
}

const LANG_BY_EXT: Record<string, string> = {
  py: "python",
  js: "javascript",
  jsx: "javascript",
  ts: "typescript",
  tsx: "typescript",
  json: "json",
  md: "markdown",
};

function inferLanguage(file?: string): string {
  if (!file) return "plaintext";
  const ext = file.split(".").pop()?.toLowerCase() ?? "";
  return LANG_BY_EXT[ext] ?? ext;
}

export function CodeEditor({ value, language, file, markers = [], readOnly = true, height = "100%" }: Props) {
  const monaco = useMonaco();
  const editorRef = useRef<any>(null);
  const monacoRef = useRef<any>(null);
  const owner = "bug-finder";

  useEffect(() => {
    const m = monacoRef.current;
    const ed = editorRef.current;
    if (!m || !ed) return;
    const model = ed.getModel();
    if (!model) return;
    m.editor.setModelMarkers(
      model,
      owner,
      (markers ?? []).map((mk) => ({
        startLineNumber: mk.line,
        endLineNumber: mk.line,
        message: mk.message,
        source: mk.severity,
        severity: mk.severity === "error" ? 8 : mk.severity === "warning" ? 4 : 1,
      })),
    );
    return () => m.editor.setModelMarkers(model, owner, []);
  }, [monaco, markers]);

  const lang = language ?? inferLanguage(file);
  return (
    <Editor
      height={height}
      language={lang}
      value={value}
      theme="vs-dark"
      onMount={(editor, m) => {
        editorRef.current = editor;
        monacoRef.current = m;
      }}
      options={{
        readOnly,
        minimap: { enabled: false },
        fontSize: 13,
        lineHeight: 20,
        wordWrap: "on",
        automaticLayout: true,
        glyphMargin: true,
        renderLineHighlight: "all",
      }}
    />
  );
}
