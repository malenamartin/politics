import { MentionsItem } from "@/lib/api";

import { FardoCard } from "@/components/ui/FardoCard";

type MentionsTableProps = {
  items: MentionsItem[];
};

export function MentionsTable({ items }: MentionsTableProps) {
  return (
    <FardoCard className="mt-6">
      <h2 className="mb-4 text-lg font-medium">Menciones por fecha y entidad</h2>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[420px] text-left text-sm">
          <thead>
            <tr style={{ color: "var(--fardo-color-text-muted)" }}>
              <th className="pb-2">Fecha</th>
              <th className="pb-2">Entidad</th>
              <th className="pb-2 text-right">Menciones</th>
            </tr>
          </thead>
          <tbody>
            {items.map((row) => (
              <tr
                key={`${row.date}-${row.entity_name}`}
                className="border-t"
                style={{ borderColor: "var(--fardo-color-border-default)" }}
              >
                <td className="py-2">{row.date}</td>
                <td className="py-2">{row.entity_name}</td>
                <td className="py-2 text-right">{row.mentions}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!items.length && (
          <p className="pt-2 text-sm" style={{ color: "var(--fardo-color-text-muted)" }}>
            Sin datos por el momento.
          </p>
        )}
      </div>
    </FardoCard>
  );
}
