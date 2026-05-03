"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import {
  createQueryRun,
  fetchQueryRun,
  fetchQueryRunResults,
  QueryRun,
  RecommendationItem,
  SentimentMap,
} from "@/lib/api";
import { NarrativeClustersCard } from "@/components/search/NarrativeClustersCard";
import { ScenarioForecastCard } from "@/components/search/ScenarioForecastCard";
import { SentimentMapCard } from "@/components/search/SentimentMapCard";
import { FardoCard } from "@/components/ui/FardoCard";
import { FardoTag } from "@/components/ui/FardoTag";

type QueryRunResultPayload = Awaited<ReturnType<typeof fetchQueryRunResults>>;

export function SearchExperience() {
  const [queryText, setQueryText] = useState(() => {
    if (typeof window === "undefined") {
      return "";
    }
    return window.localStorage.getItem("adhoc_query_text") || "";
  });
  const [lastSubmittedQuery, setLastSubmittedQuery] = useState("");
  const [horizon, setHorizon] = useState(30);
  const [loading, setLoading] = useState(false);
  const [run, setRun] = useState<QueryRun | null>(null);
  const [resultPayload, setResultPayload] = useState<QueryRunResultPayload | null>(null);
  const [error, setError] = useState("");
  const queryInputRef = useRef<HTMLInputElement | null>(null);

  const quality = resultPayload?.result?.quality;
  const sentimentMap: SentimentMap | undefined = resultPayload?.sentiment_map;

  useEffect(() => {
    window.localStorage.setItem("adhoc_query_text", queryText);
  }, [queryText]);

  const summaryCards = useMemo(() => {
    const total = resultPayload?.result?.summary.total_mentions || 0;
    const sources = resultPayload?.result?.summary.sources_used.length || 0;
    const confidence = resultPayload?.forecast.metrics.confidence || 0;
    return [
      { label: "Menciones", value: String(total) },
      { label: "Fuentes activas", value: String(sources) },
      { label: "Confianza forecast", value: `${(confidence * 100).toFixed(1)}%` },
    ];
  }, [resultPayload]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const inputValue = queryInputRef.current?.value ?? queryText;
    const normalizedQuery = inputValue.trim();
    if (!normalizedQuery) {
      setError("Ingresá un tema o persona para analizar.");
      return;
    }
    setError("");
    setLoading(true);
    setResultPayload(null);
    setLastSubmittedQuery(normalizedQuery);
    setQueryText(normalizedQuery);
    window.localStorage.setItem("adhoc_query_text", normalizedQuery);
    try {
      const created = await createQueryRun(normalizedQuery, horizon);
      setRun(created.query_run);
      const results = await waitForResults(created.query_run.id, setRun);
      setResultPayload(results);
    } catch (err) {
      const message =
        err instanceof Error && err.message
          ? err.message
          : "No se pudo procesar la consulta. Intentá nuevamente.";
      setError(message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fardo-page">
      <main className="mx-auto w-full max-w-6xl p-6 md:p-10">
        <header className="mb-8 space-y-3">
          <p className="text-sm uppercase tracking-[0.2em]" style={{ color: "var(--fardo-color-text-brand)" }}>
            Buscador universal ad-hoc
          </p>
          <h1 className="fardo-title">Consultá cualquier tema o persona</h1>
          <p className="fardo-subtitle">
            Análisis profundo multifuente con prioridad en motores IA, predicción y recomendaciones.
          </p>
        </header>

        <form
          onSubmit={onSubmit}
          noValidate
          className="fardo-card mb-6 grid gap-4 p-5 md:grid-cols-[1fr_200px_auto] md:items-end"
        >
          <label className="flex flex-col gap-2">
            <span className="fardo-kpi-label">Tema o persona</span>
            <input
              ref={queryInputRef}
              className="fardo-input"
              placeholder="Ej: Javier Milei, inflación argentina, elecciones 2027"
              value={queryText}
              onChange={(e) => {
                const nextValue = e.target.value;
                setQueryText(nextValue);
                window.localStorage.setItem("adhoc_query_text", nextValue);
              }}
            />
          </label>
          <label className="flex flex-col gap-2">
            <span className="fardo-kpi-label">Horizonte</span>
            <select
              className="fardo-input fardo-select"
              value={String(horizon)}
              onChange={(e) => setHorizon(Number(e.target.value))}
            >
              <option value="7">7 días</option>
              <option value="14">14 días</option>
              <option value="30">30 días</option>
            </select>
          </label>
          <button className="fardo-button fardo-button-primary" type="submit" disabled={loading}>
            {loading ? "Analizando..." : "Analizar"}
          </button>
        </form>

        {error ? (
          <FardoCard className="mb-6">
            <p style={{ color: "var(--fardo-color-text-danger)" }}>{error}</p>
          </FardoCard>
        ) : null}

        {run ? (
          <FardoCard className="mb-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="fardo-kpi-label">Consulta</p>
                <p className="text-sm">{run.query_text || lastSubmittedQuery}</p>
                <p className="text-xs text-gray-500">{statusDescription(run.status)}</p>
              </div>
              <FardoTag tone={statusTone(run.status)}>
                Estado: {run.status}
              </FardoTag>
            </div>
          </FardoCard>
        ) : null}

        {resultPayload ? (
          <>
            <section className="mb-6 grid gap-4 md:grid-cols-3">
              {summaryCards.map((card) => (
                <FardoCard key={card.label}>
                  <p className="fardo-kpi-label">{card.label}</p>
                  <p className="fardo-kpi-value">{card.value}</p>
                </FardoCard>
              ))}
            </section>

            <FardoCard className="mb-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="fardo-kpi-label">Confiabilidad adaptativa</p>
                  <p className="text-sm">
                    Muestra: {quality?.sample_size ?? 0} | Umbral adaptativo:{" "}
                    {quality?.adaptive_threshold ?? quality?.minimum_significant_sample ?? "-"}
                  </p>
                </div>
                <FardoTag tone={quality?.is_significant ? "success" : "warning"}>
                  {quality?.is_significant
                    ? `Confiable (${quality?.confidence_band || "medium"})`
                    : `Preliminar (${quality?.confidence_band || "low"})`}
                </FardoTag>
              </div>
            </FardoCard>

            <section className="grid gap-6 lg:grid-cols-2">
              {sentimentMap ? <SentimentMapCard sentimentMap={sentimentMap} /> : null}
              {sentimentMap ? <NarrativeClustersCard sentimentMap={sentimentMap} /> : null}
            </section>

            <FardoCard className="mt-6">
              <h2 className="mb-3 text-lg font-medium">Predicción ({resultPayload.forecast.horizon_days} días)</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr style={{ color: "var(--fardo-color-text-muted)" }}>
                      <th className="pb-2 text-left">Fecha</th>
                      <th className="pb-2 text-right">Menciones pred.</th>
                    </tr>
                  </thead>
                  <tbody>
                    {resultPayload.forecast.forecast.slice(0, 10).map((row) => (
                      <tr key={row.date} className="border-t">
                        <td className="py-2">{row.date}</td>
                        <td className="py-2 text-right">{row.predicted_mentions}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </FardoCard>

            <div className="mt-6">
              <ScenarioForecastCard
                horizonDays={resultPayload.forecast.horizon_days}
                risk={resultPayload.forecast.narrative_shift_risk}
                scenarioForecast={resultPayload.forecast.scenario_forecast}
              />
            </div>

            <FardoCard className="mt-6">
              <h2 className="mb-3 text-lg font-medium">Recomendaciones</h2>
              <div className="space-y-3">
                {resultPayload.recommendations.recommendations.map((rec: RecommendationItem, idx: number) => (
                  <div key={`${rec.title}-${idx}`} className="rounded-md border p-3">
                    <div className="mb-1 flex items-center gap-2">
                      <FardoTag tone={priorityTone(rec.priority)}>{rec.priority.toUpperCase()}</FardoTag>
                      <span className="text-xs">{rec.type}</span>
                    </div>
                    <p className="font-medium">{rec.title}</p>
                    <p className="text-sm">{rec.description}</p>
                    {rec.evidence ? (
                      <p className="mt-1 text-xs text-gray-500">
                        Evidencia: fuentes {rec.evidence.source_count ?? "-"} | narrativas{" "}
                        {rec.evidence.narrative_count ?? "-"} | tendencia{" "}
                        {rec.evidence.signal_trend ?? "-"}
                      </p>
                    ) : null}
                  </div>
                ))}
              </div>
            </FardoCard>
          </>
        ) : null}
      </main>
    </div>
  );
}

async function waitForResults(
  runId: string,
  setRun: (run: QueryRun) => void
): Promise<QueryRunResultPayload> {
  const maxAttempts = 36; // ~3 minutos con intervalo de 5s
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const statusPayload = await fetchQueryRun(runId);
    setRun(statusPayload.query_run);
    if (statusPayload.query_run.status === "completed") {
      return fetchQueryRunResults(runId);
    }
    if (statusPayload.query_run.status === "failed") {
      throw new Error(statusPayload.query_run.error || "Query run failed");
    }
    await new Promise((resolve) => setTimeout(resolve, 5000));
  }
  throw new Error("La consulta está demorando más de lo esperado. Reintentá con un tema más acotado.");
}

function priorityTone(priority: RecommendationItem["priority"]): "error" | "warning" | "info" {
  if (priority === "critical" || priority === "high") return "error";
  if (priority === "medium") return "warning";
  return "info";
}

function statusTone(status: QueryRun["status"]): "success" | "warning" | "error" | "info" {
  if (status === "completed") return "success";
  if (status === "failed") return "error";
  if (status === "running") return "warning";
  return "info";
}

function statusDescription(status: QueryRun["status"]): string {
  if (status === "queued") return "La consulta fue encolada y comenzará en breve.";
  if (status === "running") return "Recolectando y clasificando narrativas multifuente.";
  if (status === "completed") return "Análisis consolidado listo para exploración.";
  return "La ejecución falló. Podés reintentar la consulta.";
}
