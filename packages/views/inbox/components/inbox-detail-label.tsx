"use client";

import { t } from "@multica/core/i18n";
import { STATUS_CONFIG, PRIORITY_CONFIG } from "@multica/core/issues/config";
import { useActorName } from "@multica/core/workspace/hooks";
import { StatusIcon, PriorityIcon } from "../../issues/components";
import type { InboxItem, InboxItemType, IssueStatus, IssuePriority } from "@multica/core/types";

const typeLabels: Record<InboxItemType, string> = {
  issue_assigned: t("Assigned"),
  unassigned: t("Unassigned"),
  assignee_changed: t("Assignee changed"),
  status_changed: t("Status changed"),
  priority_changed: t("Priority changed"),
  due_date_changed: t("Due date changed"),
  new_comment: t("New comment"),
  mentioned: t("Mentioned"),
  review_requested: t("Review requested"),
  task_completed: t("Task completed"),
  task_failed: t("Task failed"),
  agent_blocked: t("Agent blocked"),
  agent_completed: t("Agent completed"),
  reaction_added: t("Reacted"),
};

export { typeLabels };

function shortDate(dateStr: string): string {
  if (!dateStr) return "";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

export function InboxDetailLabel({ item }: { item: InboxItem }) {
  const { getActorName } = useActorName();
  const details = item.details ?? {};

  switch (item.type) {
    case "status_changed": {
      if (!details.to) return <span>{typeLabels[item.type]}</span>;
      const label = STATUS_CONFIG[details.to as IssueStatus]?.label ?? details.to;
      return (
        <span className="inline-flex items-center gap-1">
          {t("Set status to")}
          <StatusIcon status={details.to as IssueStatus} className="h-3 w-3" />
          {label}
        </span>
      );
    }
    case "priority_changed": {
      if (!details.to) return <span>{typeLabels[item.type]}</span>;
      const label = PRIORITY_CONFIG[details.to as IssuePriority]?.label ?? details.to;
      return (
        <span className="inline-flex items-center gap-1">
          {t("Set priority to")}
          <PriorityIcon priority={details.to as IssuePriority} className="h-3 w-3" />
          {label}
        </span>
      );
    }
    case "issue_assigned": {
      if (details.new_assignee_id) {
        return <span>{t("Assigned to {{name}}", { name: getActorName(details.new_assignee_type ?? "member", details.new_assignee_id) })}</span>;
      }
      return <span>{typeLabels[item.type]}</span>;
    }
    case "unassigned":
      return <span>{t("removed assignee")}</span>;
    case "assignee_changed": {
      if (details.new_assignee_id) {
        return <span>{t("Assigned to {{name}}", { name: getActorName(details.new_assignee_type ?? "member", details.new_assignee_id) })}</span>;
      }
      return <span>{typeLabels[item.type]}</span>;
    }
    case "due_date_changed": {
      if (details.to) return <span>{t("set due date to {{date}}", { date: shortDate(details.to) })}</span>;
      return <span>{t("removed due date")}</span>;
    }
    case "new_comment": {
      if (item.body) return <span>{item.body}</span>;
      return <span>{typeLabels[item.type]}</span>;
    }
    case "reaction_added": {
      const emoji = details.emoji;
      if (emoji) return <span>{t("Reacted {{emoji}} to your comment", { emoji })}</span>;
      return <span>{typeLabels[item.type]}</span>;
    }
    default:
      return <span>{typeLabels[item.type] ?? item.type}</span>;
  }
}
