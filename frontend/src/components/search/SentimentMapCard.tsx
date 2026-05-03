"use client";

import { SentimentMap } from "@/lib/api";
import { FardoCard } from "@/components/ui/FardoCard";
import { FardoTag } from "@/components/ui/FardoTag";

type SentimentMapCardProps = {
  sentimentMap: SentimentMap;
};

export function SentimentMapCard({ sentimentMap }: SentimentMapCardProps) {
  const total =
    sentimentMap.totals.positive + sentimentMap.totals.neutral + sentimentMap.totals.negative;
  return (
    <FardoCard>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-medium">Mapa de sentimiento</h2>
        <FardoTag tone="info">Total: {total}</FardoTag>
      </div>

      <div className="mb-4 grid gap-3 md:grid-cols-3">
        <MetricPill
          label="Positivo"
          value={sentimentMap.totals.positive}
          percentage={sentimentMap.distribution.positive}
          tone="success"
        />
        <MetricPill
          label="Neutral"
          value={sentimentMap.totals.neutral}
          percentage={sentimentMap.distribution.neutral}
          tone="info"
        />
        <MetricPill
          label="Negativo"
          value={sentimentMap.totals.negative}
          percentage={sentimentMap.distribution.negative}
          tone="error"
        />
      </div>

      <h3 className="mb-2 text-sm font-medium">Sentimiento por fuente</h3>
      <div className="space-y-2 text-sm">
        {Object.entries(sentimentMap.by_source).map(([source, agg]) => (
          <div key={source} className="flex items-center justify-between rounded-md border px-3 py-2">
            <span>{source}</span>
            <span>
              +{agg.positive} / ={agg.neutral} / -{agg.negative}
            </span>
          </div>
        ))}
      </div>
    </FardoCard>
  );
}

function MetricPill({
  label,
  value,
  percentage,
  tone,
}: {
  label: string;
  value: number;
  percentage: number;
  tone: "success" | "info" | "error";
}) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-xs uppercase tracking-wide text-gray-500">{label}</p>
      <p className="text-2xl font-semibold">{value}</p>
      <div className="mt-1 flex items-center justify-between">
        <span className="text-xs text-gray-500">{(percentage * 100).toFixed(1)}%</span>
        <FardoTag tone={tone}>{label}</FardoTag>
      </div>
    </div>
  );
}
