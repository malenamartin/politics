import { ReactNode } from "react";

type FardoCardProps = {
  children: ReactNode;
  className?: string;
};

export function FardoCard({ children, className }: FardoCardProps) {
  return <article className={`fardo-card p-5 ${className || ""}`.trim()}>{children}</article>;
}
