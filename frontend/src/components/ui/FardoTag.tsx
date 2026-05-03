type FardoTagTone = "info" | "success" | "warning" | "error";

type FardoTagProps = {
  tone: FardoTagTone;
  children: React.ReactNode;
};

const toneClass: Record<FardoTagTone, string> = {
  info: "fardo-tag-info",
  success: "fardo-tag-success",
  warning: "fardo-tag-warning",
  error: "fardo-tag-error",
};

export function FardoTag({ tone, children }: FardoTagProps) {
  return <span className={`fardo-tag ${toneClass[tone]}`}>{children}</span>;
}
