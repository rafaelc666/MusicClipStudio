import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[11px] font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-neon/40",
  {
    variants: {
      variant: {
        default:
          "border-white/10 bg-bg-3 text-fg-1",
        subtle:
          "border-white/5 bg-bg-2/60 text-fg-2",
        neon:
          "border-neon/30 bg-neon/10 text-neon shadow-[0_0_12px_-6px_rgba(34,211,238,0.5)]",
        ok:
          "border-ok/25 bg-ok/10 text-ok",
        warn:
          "border-warn/25 bg-warn/10 text-warn",
        err:
          "border-err/25 bg-err/10 text-err",
        outline:
          "border-white/10 text-fg-2",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
