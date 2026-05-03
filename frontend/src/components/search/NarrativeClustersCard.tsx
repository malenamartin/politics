"use client";

import { SentimentMap } from "@/lib/api";
import { FardoCard } from "@/components/ui/FardoCard";
import { FardoTag } from "@/components/ui/FardoTag";

type NarrativeClustersCardProps = {
  sentimentMap: SentimentMap;
};

export function NarrativeClustersCard({ sentimentMap }: NarrativeClustersCardProps) {
  const items = sentimentMap.narrative_intensity || [];
  return (
    <FardoCard>
      <h2 className="mb-3 text-lg font-medium">Narrativas clave</h2>
      <div className="space-y-2">
        {items.length === 0 ? (
          <p className="text-sm text-gray-500">Sin narrativas suficientes para mostrar.</p>
        ) : null}
        {items.map((item) => (
          <div key={item.tag} className="rounded-md border p-3">
            <div className="mb-2 flex items-center justify-between gap-2">
              <p className="font-medium">{item.tag}</p>
              <FardoTag tone={item.avg_sentiment >= 0 ? "success" : "error"}>
                Sent {item.avg_sentiment.toFixed(2)}
              </FardoTag>
            </div>
            <div className="flex items-center justify-between text-sm text-gray-600">
              <span>Volumen: {item.volume}</span>
              <span>Momentum: {item.momentum.toFixed(2)}</span>
            </div>
          </div>
        ))}
      </div>
    </FardoCard>
  );
}
