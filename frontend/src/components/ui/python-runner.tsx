"use client";

import { usePython } from "react-py";
import { useEffect, useState } from "react";
import { Loader2, Play, Terminal } from "lucide-react";

export function PythonRunner({ code }: { code: string }) {
  // packages에 pandas 추가 (로드 시간이 조금 걸림)
  const { runPython, stdout, stderr, isLoading, isRunning } = usePython({
    packages: { official: ["pandas"] },
  });
  const [hasRun, setHasRun] = useState(false);

  // 컴포넌트 마운트 시 자동 실행 (지연 실행으로 타이밍 이슈 완화)
  useEffect(() => {
    if (!isLoading && !hasRun && code && runPython) {
      const timer = setTimeout(() => {
        try {
          runPython(code);
          setHasRun(true);
        } catch (error) {
          console.error("Failed to run Python code:", error);
        }
      }, 500); // 0.5초 대기 후 실행
      return () => clearTimeout(timer);
    }
  }, [isLoading, hasRun, code, runPython]);

  return (
    <div className="my-4 w-full max-w-3xl overflow-hidden rounded-lg border border-gray-800 bg-[#1e1e1e] text-gray-100 shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-700 bg-[#2d2d2d] px-4 py-2">
        <div className="flex items-center gap-2">
          <Terminal className="h-4 w-4 text-green-400" />
          <span className="text-sm font-medium">Python Analysis</span>
        </div>
        <div className="text-xs text-gray-400">Powered by Pyodide 🐍</div>
      </div>

      {/* Code Viewer (Optional: can use syntax highlighter) */}
      <div className="overflow-x-auto bg-[#1e1e1e] p-4 font-mono text-xs text-gray-300 opacity-80">
        <pre>{code}</pre>
      </div>

      {/* Output Section */}
      <div className="border-t border-gray-700 bg-black p-4 font-mono text-sm">
        {isLoading ? (
          <div className="flex items-center gap-2 text-yellow-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Loading Python Environment (pandas)...</span>
          </div>
        ) : isRunning ? (
          <div className="flex items-center gap-2 text-blue-400">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Running Analysis...</span>
          </div>
        ) : (
          <>
            {stdout && (
              <div className="mb-2">
                <div className="mb-1 text-xs text-gray-500">STDOUT</div>
                <div className="whitespace-pre-wrap text-green-400">
                  {stdout}
                </div>
              </div>
            )}
            {stderr && (
              <div>
                <div className="mb-1 text-xs text-gray-500">STDERR</div>
                <div className="whitespace-pre-wrap text-red-400">{stderr}</div>
              </div>
            )}
            {!stdout && !stderr && (
              <div className="text-gray-600 italic">No output</div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
