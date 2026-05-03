import { QualityMetadata } from "@/lib/api";
import { FardoTag } from "@/components/ui/FardoTag";

type SampleQualityBannerProps = {
  quality?: QualityMetadata;
};

export function SampleQualityBanner({ quality }: SampleQualityBannerProps) {
  if (!quality) return null;
  const tone = quality.is_significant ? "success" : "warning";
  const threshold = quality.adaptive_threshold ?? quality.minimum_significant_sample ?? 0;
  return (
    <div className="fardo-card mb-6 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="fardo-kpi-label">Calidad de muestra</p>
          <p className="text-sm" style={{ color: "var(--fardo-color-text-secondary)" }}>
            Muestra actual: {quality.sample_size} observaciones | Mínimo requerido:{" "}
            {threshold}
          </p>
        </div>
        <FardoTag tone={tone}>
          {quality.is_significant
            ? "Muestra significativa"
            : `Faltan ${quality.missing_to_significant} para significancia`}
        </FardoTag>
      </div>
      {quality.confidence_band ? (
        <p className="mt-2 text-xs" style={{ color: "var(--fardo-color-text-muted)" }}>
          Banda de confianza: {quality.confidence_band}
        </p>
      ) : null}
    </div>
  );
}
