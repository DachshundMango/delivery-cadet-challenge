import { AIMessage, ToolMessage } from "@langchain/langgraph-sdk";
import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronUp } from "lucide-react";
// chart components import
import { PlotlyChart } from "@/components/ui/plotly-chart";
// python runner component import
import { PythonRunner } from "@/components/ui/python-runner";

function isComplexValue(value: any): boolean {
  return Array.isArray(value) || (typeof value === "object" && value !== null);
}

export function ToolCalls({
  toolCalls,
}: {
  toolCalls: AIMessage["tool_calls"];
}) {
  if (!toolCalls || toolCalls.length === 0) return null;

  return (
    <div className="mx-auto grid max-w-3xl grid-rows-[1fr_auto] gap-2">
      {toolCalls.map((tc, idx) => {
        const args = tc.args as Record<string, any>;
        const hasArgs = Object.keys(args).length > 0;
        return (
          <div
            key={idx}
            className="overflow-hidden rounded-lg border border-gray-200"
          >
            <div className="border-b border-gray-200 bg-gray-50 px-4 py-2">
              <h3 className="font-medium text-gray-900">
                {tc.name}
                {tc.id && (
                  <code className="ml-2 rounded bg-gray-100 px-2 py-1 text-sm">
                    {tc.id}
                  </code>
                )}
              </h3>
            </div>
            {hasArgs ? (
              <table className="min-w-full divide-y divide-gray-200">
                <tbody className="divide-y divide-gray-200">
                  {Object.entries(args).map(([key, value], argIdx) => (
                    <tr key={argIdx}>
                      <td className="px-4 py-2 text-sm font-medium whitespace-nowrap text-gray-900">
                        {key}
                      </td>
                      <td className="px-4 py-2 text-sm text-gray-500">
                        {isComplexValue(value) ? (
                          <code className="rounded bg-gray-50 px-2 py-1 font-mono text-sm break-all">
                            {JSON.stringify(value, null, 2)}
                          </code>
                        ) : (
                          String(value)
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <code className="block p-3 text-sm">{"{}"}</code>
            )}
          </div>
        );
      })}
    </div>
  );
}

export function ToolResult({ message }: { message: ToolMessage }) {
  const [isExpanded, setIsExpanded] = useState(false);

  // [최적화] 메시지 내용 파싱 결과를 메모이제이션하여 불필요한 객체 생성 방지
  const { parsedContent, isJsonContent, isPlotly } = useMemo(() => {
    let parsed: any;
    let isJson = false;

    try {
      if (typeof message.content === "string") {
        parsed = JSON.parse(message.content);
        isJson = isComplexValue(parsed);
      }
    } catch {
      parsed = message.content;
    }

    const isPlotlyChart =
      isJson &&
      !Array.isArray(parsed) &&
      parsed?.type === "plotly" &&
      Array.isArray(parsed?.data);

    return {
      parsedContent: parsed,
      isJsonContent: isJson,
      isPlotly: isPlotlyChart,
    };
  }, [message.content]);

  const isPython = message.name === "python_interpreter";

  const contentStr = isJsonContent
    ? JSON.stringify(parsedContent, null, 2)
    : String(message.content);
  const contentLines = contentStr.split("\n");
  const shouldTruncate = contentLines.length > 4 || contentStr.length > 500;
  const displayedContent =
    shouldTruncate && !isExpanded
      ? contentStr.length > 500
        ? contentStr.slice(0, 500) + "..."
        : contentLines.slice(0, 4).join("\n") + "\n..."
      : contentStr;

  return (
    <div className="mx-auto grid max-w-3xl grid-rows-[1fr_auto] gap-2">
      <div className="overflow-hidden rounded-lg border border-gray-200">
        {/* Hide header for Plotly charts (chart title provides context) and Python interpreter */}
        {!isPlotly && !isPython && (
          <div className="border-b border-gray-200 bg-gray-50 px-4 py-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              {message.name ? (
                <h3 className="font-medium text-gray-900">
                  Tool Result:{" "}
                  <code className="rounded bg-gray-100 px-2 py-1">
                    {message.name}
                  </code>
                </h3>
              ) : (
                <h3 className="font-medium text-gray-900">Tool Result</h3>
              )}
              {message.tool_call_id && (
                <code className="ml-2 rounded bg-gray-100 px-2 py-1 text-sm">
                  {message.tool_call_id}
                </code>
              )}
            </div>
          </div>
        )}

        {/* Plotly 차트는 애니메이션 컨테이너 밖으로 완전히 분리하여 리사이징 간섭 차단 */}
        {isPlotly ? (
          <div className="w-full bg-gray-100 p-3">
            <PlotlyChart
              data={parsedContent.data}
              layout={parsedContent.layout}
            />
          </div>
        ) : (
          <motion.div
            className="min-w-full bg-gray-100"
            initial={false}
            animate={{ height: "auto" }}
            transition={{ duration: 0.3 }}
          >
            <div className="p-3">
              <AnimatePresence
                mode="wait"
                initial={false}
              >
                <motion.div
                  key={isExpanded ? "expanded" : "collapsed"}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  {isPython ? (
                    <PythonRunner code={message.content as string} />
                  ) : isJsonContent ? (
                    <table className="min-w-full divide-y divide-gray-200">
                      <tbody className="divide-y divide-gray-200">
                        {(Array.isArray(parsedContent)
                          ? isExpanded
                            ? parsedContent
                            : parsedContent.slice(0, 5)
                          : Object.entries(parsedContent)
                        ).map((item, argIdx) => {
                          const [key, value] = Array.isArray(parsedContent)
                            ? [argIdx, item]
                            : [item[0], item[1]];
                          return (
                            <tr key={argIdx}>
                              <td className="px-4 py-2 text-sm font-medium whitespace-nowrap text-gray-900">
                                {key}
                              </td>
                              <td className="px-4 py-2 text-sm text-gray-500">
                                {isComplexValue(value) ? (
                                  <code className="rounded bg-gray-50 px-2 py-1 font-mono text-sm break-all">
                                    {JSON.stringify(value, null, 2)}
                                  </code>
                                ) : (
                                  String(value)
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  ) : (
                    <code className="block text-sm">{displayedContent}</code>
                  )}
                </motion.div>
              </AnimatePresence>
            </div>
            {/* JSON이 아니고 내용이 길거나, JSON 배열이 5개 초과일 때만 확장 버튼 표시 */}
            {((shouldTruncate && !isJsonContent) ||
              (isJsonContent &&
                Array.isArray(parsedContent) &&
                parsedContent.length > 5)) && (
              <motion.button
                onClick={() => setIsExpanded(!isExpanded)}
                className="flex w-full cursor-pointer items-center justify-center border-t-[1px] border-gray-200 py-2 text-gray-500 transition-all duration-200 ease-in-out hover:bg-gray-50 hover:text-gray-600"
                initial={{ scale: 1 }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                {isExpanded ? <ChevronUp /> : <ChevronDown />}
              </motion.button>
            )}
          </motion.div>
        )}
      </div>
    </div>
  );
}
