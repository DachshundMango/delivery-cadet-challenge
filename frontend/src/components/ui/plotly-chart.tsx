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
  return (
    <div className="w-full h-full min-h-[400px] border rounded-lg p-2 bg-white relative z-0">
      <Plot
        data={data}
        layout={{
          ...layout,
          autosize: true,
          margin: { l: 50, r: 20, t: 30, b: 50 },
          height: 400,
        }}
        useResizeHandler={true}
        style={{ width: "100%", height: "100%" }}
        config={{ responsive: true, displayModeBar: false }}
      />
    </div>
  );
}