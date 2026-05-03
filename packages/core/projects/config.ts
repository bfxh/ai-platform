import { t } from "@multica/core/i18n";
import type { ProjectStatus, ProjectPriority } from "../types";

export const PROJECT_STATUS_ORDER: ProjectStatus[] = [
  "planned",
  "in_progress",
  "paused",
  "completed",
  "cancelled",
];

export const PROJECT_STATUS_CONFIG: Record<
  ProjectStatus,
  { label: string; color: string; dotColor: string; badgeBg: string; badgeText: string }
> = {
  planned: { label: t("Planned"), color: "text-muted-foreground", dotColor: "bg-muted-foreground", badgeBg: "bg-muted", badgeText: "text-muted-foreground" },
  in_progress: { label: t("In Progress"), color: "text-warning", dotColor: "bg-warning", badgeBg: "bg-warning", badgeText: "text-white" },
  paused: { label: t("Paused"), color: "text-muted-foreground", dotColor: "bg-muted-foreground", badgeBg: "bg-muted", badgeText: "text-muted-foreground" },
  completed: { label: t("Completed"), color: "text-info", dotColor: "bg-info", badgeBg: "bg-info", badgeText: "text-white" },
  cancelled: { label: t("Cancelled"), color: "text-destructive", dotColor: "bg-destructive", badgeBg: "bg-muted", badgeText: "text-muted-foreground" },
};

export const PROJECT_PRIORITY_ORDER: ProjectPriority[] = [
  "urgent",
  "high",
  "medium",
  "low",
  "none",
];

export const PROJECT_PRIORITY_CONFIG: Record<
  ProjectPriority,
  { label: string; bars: number; color: string; badgeBg: string; badgeText: string }
> = {
  urgent: { label: t("Urgent"), bars: 4, color: "text-destructive", badgeBg: "bg-priority", badgeText: "text-white" },
  high: { label: t("High"), bars: 3, color: "text-warning", badgeBg: "bg-priority/80", badgeText: "text-white" },
  medium: { label: t("Medium"), bars: 2, color: "text-warning", badgeBg: "bg-priority/15", badgeText: "text-priority" },
  low: { label: t("Low"), bars: 1, color: "text-info", badgeBg: "bg-priority/10", badgeText: "text-priority" },
  none: { label: t("No priority"), bars: 0, color: "text-muted-foreground", badgeBg: "bg-muted", badgeText: "text-muted-foreground" },
};
