type StatusBadgeProps = {
  value: string | null | undefined;
};

export function StatusBadge({ value }: StatusBadgeProps) {
  const safeValue = value ?? "unknown";
  return <span className={`status-badge status-${safeValue}`}>{safeValue}</span>;
}
