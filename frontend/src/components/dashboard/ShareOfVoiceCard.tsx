import { ShareItem } from "@/lib/api";

import { FardoCard } from "@/components/ui/FardoCard";

type ShareOfVoiceCardProps = {
  items: ShareItem[];
};

export function ShareOfVoiceCard({ items }: ShareOfVoiceCardProps) {
  return (
    <FardoCard>
      <h2 className="mb-4 text-lg font-medium">Share of Voice</h2>
      <div className="space-y-4">
        {items.map((item) => (
          <div key={item.entity_name}>
            <div className="mb-1 flex justify-between text-sm">
              <span>{item.entity_name}</span>
              <span>{(item.share_of_voice * 100).toFixed(1)}%</span>
            </div>
            <div className="h-2 rounded-full" style={{ background: "var(--fardo-gray-200)" }}>
              <div
                className="h-2 rounded-full"
                style={{
                  background: "var(--fardo-color-bg-brand)",
                  width: `${Math.max(3, item.share_of_voice * 100)}%`,
                }}
              />
            </div>
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
