"use client";

import { FardoCard } from "@/components/ui/FardoCard";
import { FardoTag } from "@/components/ui/FardoTag";

type ForecastPoint = {
  date: string;
  predicted_mentions: number;
};

type ScenarioForecastCardProps = {
  horizonDays: number;
  risk?: "low" | "medium" | "high";
  scenarioForecast?: {
    base: ForecastPoint[];
    bull: ForecastPoint[];
    bear: ForecastPoint[];
  };
};

export function ScenarioForecastCard({
  horizonDays,
  risk,
  scenarioForecast,
}: ScenarioForecastCardProps) {
  const baseLast = scenarioForecast?.base?.at(-1)?.predicted_mentions ?? 0;
  const bullLast = scenarioForecast?.bull?.at(-1)?.predicted_mentions ?? 0;
  const bearLast = scenarioForecast?.bear?.at(-1)?.predicted_mentions ?? 0;

  return (
    <FardoCard>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-medium">Predicción por escenarios ({horizonDays} días)</h2>
        <FardoTag tone={riskTone(risk)}>{`Riesgo narrativa: ${risk || "low"}`}</FardoTag>
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        <ScenarioCell title="Base" value={baseLast} />
        <ScenarioCell title="Bull" value={bullLast} />
        <ScenarioCell title="Bear" value={bearLast} />
      </div>
    </FardoCard>
  );
}

function ScenarioCell({ title, value }: { title: string; value: number }) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-xs uppercase tracking-wide text-gray-500">{title}</p>
      <p className="text-2xl font-semibold">{value}</p>
      <p className="text-xs text-gray-500">Menciones proyectadas al cierre</p>
    </div>
  );
}

function riskTone(risk?: "low" | "medium" | "high"): "success" | "warning" | "error" | "info" {
  if (risk === "high") return "error";
  if (risk === "medium") return "warning";
  if (risk === "low") return "success";
  return "info";
}
