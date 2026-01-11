"use client";

import dynamic from "next/dynamic";
import React from "react";
import { Skeleton } from "./skeleton";

// SSR을 끄고 클라이언트에서만 로드하도록 설정 (필수!)
const Plot = dynamic(() => import("react-plotly.js"), {
  ssr: false,
  loading: () => <Skeleton className="h-[400px] w-full rounded-lg" />,
});

interface PlotlyChartProps {
  data: any[];
  layout?: any;
}

export function PlotlyChart({ data, layout }: PlotlyChartProps) {
  // Generate unique revision key to force Plotly to recognize data changes
  const revision = React.useMemo(
    () => Date.now() + Math.random(),
    [data, layout]
  );

  // Ensure layout has explicit sizing to prevent crop issues
  const enhancedLayout = React.useMemo(
    () => ({
      ...layout,
      autosize: false,
      width: undefined, // Let container control width
      height: layout?.height || 500,
    }),
    [layout]
  );

  const chartStyle = React.useMemo(
    () => ({ width: "100%", height: "100%" }),
    []
  );

  // Debugging: render log
  console.log("PlotlyChart Rendered", { 
    dataLen: data?.length, 
    revision,
    height: enhancedLayout.height 
  });

  return (
    <div className="relative z-0 h-full min-h-[500px] w-full rounded-lg border bg-white p-4">
      <Plot
        data={data}
        layout={enhancedLayout}
        revision={revision}
        useResizeHandler={false}
        style={chartStyle}
        config={{
          responsive: true,
          displayModeBar: false,
          scrollZoom: false,
        }}
      />
    </div>
  );
}
