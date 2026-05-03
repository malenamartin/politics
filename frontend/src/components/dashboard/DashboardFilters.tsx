type DashboardFiltersProps = {
  defaultEntities: string;
  defaultDays: number;
  defaultHorizon: number;
  defaultProKey?: string;
};

export function DashboardFilters({
  defaultEntities,
  defaultDays,
  defaultHorizon,
  defaultProKey,
}: DashboardFiltersProps) {
  return (
    <form className="fardo-card mb-6 grid gap-4 p-5 md:grid-cols-2 xl:grid-cols-[1fr_180px_200px_1fr_auto] xl:items-end">
      <label className="flex flex-col gap-2">
        <span className="fardo-kpi-label">Entidades (1 a 5)</span>
        <input
          name="entities"
          defaultValue={defaultEntities}
          placeholder="Javier Milei,Axel Kicillof"
          className="fardo-input"
        />
      </label>

      <label className="flex flex-col gap-2">
        <span className="fardo-kpi-label">Ventana (días)</span>
        <select name="days" defaultValue={String(defaultDays)} className="fardo-input fardo-select">
          <option value="3">3 días</option>
          <option value="7">7 días</option>
          <option value="14">14 días</option>
          <option value="30">30 días</option>
        </select>
      </label>

      <label className="flex flex-col gap-2">
        <span className="fardo-kpi-label">Horizonte predicción</span>
        <select
          name="horizon"
          defaultValue={String(defaultHorizon)}
          className="fardo-input fardo-select"
        >
          <option value="7">7 días</option>
          <option value="14">14 días</option>
          <option value="30">30 días</option>
        </select>
      </label>

      <label className="flex flex-col gap-2">
        <span className="fardo-kpi-label">Clave Pro (opcional)</span>
        <input
          type="password"
          name="proKey"
          defaultValue={defaultProKey || ""}
          placeholder="x-pro-key"
          className="fardo-input"
        />
      </label>

      <button type="submit" className="fardo-button fardo-button-primary">
        Aplicar filtros
      </button>
    </form>
  );
}
