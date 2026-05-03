import { t } from "@multica/core/i18n";
import { cn } from "@multica/ui/lib/utils"
import { Loader2Icon } from "lucide-react"

function Spinner({ className, ...props }: React.ComponentProps<"svg">) {
  return (
    <Loader2Icon role="status" aria-label={t("Loading")} className={cn("size-4 animate-spin", className)} {...props} />
  )
}

export { Spinner }
