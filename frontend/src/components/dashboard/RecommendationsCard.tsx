import { RecommendationItem } from "@/lib/api";

import { FardoCard } from "@/components/ui/FardoCard";
import { FardoTag } from "@/components/ui/FardoTag";

type RecommendationsCardProps = {
  recommendations: RecommendationItem[];
  blockedReason?: string;
};

export function RecommendationsCard({ recommendations, blockedReason }: RecommendationsCardProps) {
  return (
    <FardoCard className="mt-6">
      <h2 className="mb-4 text-lg font-medium">Recomendaciones accionables</h2>

      {blockedReason ? (
        <p className="text-sm" style={{ color: "var(--fardo-color-text-muted)" }}>
          {blockedReason}
        </p>
      ) : (
        <div className="space-y-3">
          {recommendations.slice(0, 5).map((rec, index) => (
            <div
              key={`${rec.title}-${index}`}
              className="rounded-lg border p-3"
              style={{ borderColor: "var(--fardo-color-border-default)" }}
            >
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <FardoTag tone={priorityTone(rec.priority)}>{rec.priority.toUpperCase()}</FardoTag>
                <FardoTag tone="info">{rec.type}</FardoTag>
                <span className="text-xs" style={{ color: "var(--fardo-color-text-muted)" }}>
                  Confianza {(rec.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <p className="font-medium">{rec.title}</p>
              <p className="mt-1 text-sm" style={{ color: "var(--fardo-color-text-secondary)" }}>
                {rec.description}
              </p>
              <p className="mt-2 text-sm">
                <strong>Acción:</strong> {rec.actionText} | <strong>Impacto:</strong>{" "}
                {rec.expectedImpact}
              </p>
            </div>
          ))}
        </div>
      )}
    </FardoCard>
  );
}

function priorityTone(priority: RecommendationItem["priority"]): "error" | "warning" | "info" {
  if (priority === "critical" || priority === "high") return "error";
  if (priority === "medium") return "warning";
  return "info";
}
