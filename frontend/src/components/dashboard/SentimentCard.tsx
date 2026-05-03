import { SentimentItem } from "@/lib/api";

import { FardoCard } from "@/components/ui/FardoCard";

type SentimentCardProps = {
  items: SentimentItem[];
};

export function SentimentCard({ items }: SentimentCardProps) {
  return (
    <FardoCard>
      <h2 className="mb-4 text-lg font-medium">Sentimiento por entidad</h2>
      <div className="space-y-3 text-sm">
        {groupSentimentByEntity(items).map((item) => (
          <div
            key={item.entity_name}
            className="flex items-center justify-between rounded-lg px-3 py-2"
            style={{ background: "var(--fardo-color-bg-subtle)" }}
          >
            <span>{item.entity_name}</span>
            <span>{item.avg_sentiment.toFixed(3)}</span>
          </div>
        ))}
        {!items.length && (
          <p className="text-sm" style={{ color: "var(--fardo-color-text-muted)" }}>
            Sin datos por el momento.
          </p>
        )}
      </div>
    </FardoCard>
  );
}

function groupSentimentByEntity(data: SentimentItem[]): Array<{ entity_name: string; avg_sentiment: number }> {
  const grouped = new Map<string, { sum: number; count: number }>();
  for (const item of data) {
    const current = grouped.get(item.entity_name) || { sum: 0, count: 0 };
    current.sum += item.avg_sentiment;
    current.count += 1;
    grouped.set(item.entity_name, current);
  }
  return Array.from(grouped.entries()).map(([entity_name, value]) => ({
    entity_name,
    avg_sentiment: value.sum / value.count,
  }));
}
