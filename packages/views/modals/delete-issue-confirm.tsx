"use client";

import { t } from "@multica/core/i18n";
import { useState } from "react";
import { toast } from "sonner";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@multica/ui/components/ui/alert-dialog";
import { useDeleteIssue } from "@multica/core/issues/mutations";
import { useNavigation } from "../navigation";

export function DeleteIssueConfirmModal({
  onClose,
  data,
}: {
  onClose: () => void;
  data: Record<string, unknown> | null;
}) {
  const issueId = (data?.issueId as string) || "";
  const navigateTo = (data?.onDeletedNavigateTo as string | undefined) || undefined;
  const [deleting, setDeleting] = useState(false);
  const deleteIssue = useDeleteIssue();
  const navigation = useNavigation();

  const handleDelete = async () => {
    if (!issueId) return;
    setDeleting(true);
    try {
      await deleteIssue.mutateAsync(issueId);
      toast.success(t("Issue deleted"));
      onClose();
      if (navigateTo) navigation.push(navigateTo);
    } catch {
      toast.error(t("Failed to delete issue"));
      setDeleting(false);
    }
  };

  return (
    <AlertDialog open onOpenChange={(v) => { if (!v && !deleting) onClose(); }}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{t("Delete issue")}</AlertDialogTitle>
          <AlertDialogDescription>
            {t("This will permanently delete this issue and all its comments. This action cannot be undone.")}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={deleting}>{t("Cancel")}</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={deleting}
            className="bg-destructive text-white hover:bg-destructive/90"
          >
            {deleting ? t("Deleting...") : t("Delete")}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
