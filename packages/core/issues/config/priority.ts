import { t } from "@multica/core/i18n";
import type { IssuePriority } from "../../types";

export const PRIORITY_ORDER: IssuePriority[] = [
  "urgent",
  "high",
  "medium",
  "low",
  "none",
];

export const PRIORITY_CONFIG: Record<
  IssuePriority,
  { label: string; bars: number; color: string; badgeBg: string; badgeText: string }
> = {
  urgent: { label: t("Urgent"), bars: 4, color: "text-destructive", badgeBg: "bg-priority", badgeText: "text-white" },
  high: { label: t("High"), bars: 3, color: "text-warning", badgeBg: "bg-priority/80", badgeText: "text-white" },
  medium: { label: t("Medium"), bars: 2, color: "text-warning", badgeBg: "bg-priority/15", badgeText: "text-priority" },
  low: { label: t("Low"), bars: 1, color: "text-info", badgeBg: "bg-priority/10", badgeText: "text-priority" },
  none: { label: t("No priority"), bars: 0, color: "text-muted-foreground", badgeBg: "bg-muted", badgeText: "text-muted-foreground" },
};
