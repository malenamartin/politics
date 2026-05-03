import { ForecastBaselinePoint, ForecastPoint } from "@/lib/api";

import { FardoCard } from "@/components/ui/FardoCard";
import { FardoTag } from "@/components/ui/FardoTag";

type ForecastCardProps = {
  baseline: ForecastBaselinePoint[];
  forecast: ForecastPoint[];
  confidence: number;
  horizon: number;
  blockedReason?: string;
};

export function ForecastCard({
  baseline,
  forecast,
  confidence,
  horizon,
  blockedReason,
}: ForecastCardProps) {
  return (
    <FardoCard className="mt-6">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-lg font-medium">Predicción {horizon} días</h2>
        {!blockedReason && <FardoTag tone="info">Confianza {(confidence * 100).toFixed(1)}%</FardoTag>}
      </div>

      {blockedReason ? (
        <p className="text-sm" style={{ color: "var(--fardo-color-text-muted)" }}>
          {blockedReason}
        </p>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <div>
            <p className="mb-2 text-sm font-medium">Últimos datos observados</p>
            <table className="w-full text-sm">
              <thead>
                <tr style={{ color: "var(--fardo-color-text-muted)" }}>
                  <th className="pb-1 text-left">Fecha</th>
                  <th className="pb-1 text-right">Menciones</th>
                </tr>
              </thead>
              <tbody>
                {baseline.slice(-5).map((row) => (
                  <tr key={`base-${row.date}`} className="border-t">
                    <td className="py-1">{row.date}</td>
                    <td className="py-1 text-right">{row.mentions}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div>
            <p className="mb-2 text-sm font-medium">Proyección</p>
            <table className="w-full text-sm">
              <thead>
                <tr style={{ color: "var(--fardo-color-text-muted)" }}>
                  <th className="pb-1 text-left">Fecha</th>
                  <th className="pb-1 text-right">Menciones</th>
                </tr>
              </thead>
              <tbody>
                {forecast.slice(0, 7).map((row) => (
                  <tr key={`pred-${row.date}`} className="border-t">
                    <td className="py-1">{row.date}</td>
                    <td className="py-1 text-right">{row.predicted_mentions}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </FardoCard>
  );
}
