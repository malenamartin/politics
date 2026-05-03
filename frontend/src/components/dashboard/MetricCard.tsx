import { ReactNode } from "react";

import { FardoCard } from "@/components/ui/FardoCard";

type MetricCardProps = {
  label: string;
  value: string;
  trailing?: ReactNode;
};

export function MetricCard({ label, value, trailing }: MetricCardProps) {
  return (
    <FardoCard>
      <p className="fardo-kpi-label">{label}</p>
      <div className="mt-2 flex items-center justify-between gap-3">
        <p className="fardo-kpi-value">{value}</p>
        {trailing}
      </div>
    </FardoCard>
  );
}
