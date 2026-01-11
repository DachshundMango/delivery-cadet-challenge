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

export const PlotlyChart = React.memo(
  function PlotlyChart({ data, layout }: PlotlyChartProps) {
    // 레이아웃이 변경되어도 차트 높이를 안정적으로 유지하기 위한 style 설정
    const chartStyle = React.useMemo(
      () => ({ width: "100%", height: "100%", minHeight: "400px" }),
      [],
    );

    // 디버깅: 리렌더링 로그 (콘솔에서 확인)
    console.log("PlotlyChart Rendered", { dataLen: data?.length });

    return (
      <div className="relative z-0 h-full min-h-[400px] w-full rounded-lg border bg-white p-4">
        <Plot
          data={data}
          layout={layout}
          useResizeHandler={true}
          style={chartStyle}
          config={{
            responsive: true,
            displayModeBar: false,
            scrollZoom: false, // 스크롤 시 줌 방지 (UX 개선)
          }}
        />
      </div>
    );
  },
  (prevProps, nextProps) => {
    // Props가 실제로 변경되었을 때만 리렌더링 (Deep compare가 필요할 수 있으나, 보통 data 레퍼런스가 바뀌지 않으면 됨)
    // 여기서는 JSON 문자열화하여 간단비교하거나, 단순히 data와 layout 레퍼런스 비교
    return (
      JSON.stringify(prevProps.data) === JSON.stringify(nextProps.data) &&
      JSON.stringify(prevProps.layout) === JSON.stringify(nextProps.layout)
    );
  },
);
