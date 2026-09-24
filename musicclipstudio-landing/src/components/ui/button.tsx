import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-sm text-sm font-medium transition-all duration-150 outline-none focus-visible:ring-2 focus-visible:ring-neon/60 focus-visible:ring-offset-2 focus-visible:ring-offset-bg-0 select-none",
  {
    variants: {
      variant: {
        neon:
          "bg-gradient-to-b from-neon to-neon-3 text-[#06141a] font-semibold shadow-[0_0_0_1px_rgba(34,211,238,0.5),0_10px_30px_-12px_rgba(34,211,238,0.55)] hover:brightness-105 hover:-translate-y-0.5 hover:shadow-[0_0_0_1px_rgba(34,211,238,0.7),0_14px_36px_-14px_rgba(34,211,238,0.7)] active:translate-y-0 active:brightness-95 data-[loading=true]:cursor-progress data-[disabled=true]:pointer-events-none data-[disabled=true]:opacity-50",
        default:
          "bg-bg-3 text-fg-0 border border-white/5 hover:bg-bg-4 hover:border-neon/30 data-[loading=true]:cursor-progress data-[disabled=true]:pointer-events-none data-[disabled=true]:opacity-50",
        ghost:
          "bg-transparent text-fg-1 border border-transparent hover:bg-bg-3 hover:text-fg-0 hover:border-white/5 data-[loading=true]:cursor-progress data-[disabled=true]:pointer-events-none data-[disabled=true]:opacity-50",
        outline:
          "bg-transparent text-fg-0 border border-white/10 hover:border-neon/40 hover:bg-bg-3/60 data-[loading=true]:cursor-progress data-[disabled=true]:pointer-events-none data-[disabled=true]:opacity-50",
        subtle:
          "bg-bg-2/60 text-fg-1 border border-white/5 hover:bg-bg-3 hover:text-fg-0 data-[loading=true]:cursor-progress data-[disabled=true]:pointer-events-none data-[disabled=true]:opacity-50",
        destructive:
          "bg-err/20 text-err border border-err/30 hover:bg-err/30 data-[loading=true]:cursor-progress data-[disabled=true]:pointer-events-none data-[disabled=true]:opacity-50",
      },
      size: {
        sm: "h-8 px-3 text-xs",
        md: "h-9 px-4 text-[13px]",
        lg: "h-11 px-6 text-sm",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
}

function Spinner({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={cn("h-4 w-4 animate-spin", className)}
      fill="none"
    >
      <circle
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeOpacity="0.25"
        strokeWidth="4"
      />
      <path
        fill="currentColor"
        d="M4 12a8 8 0 0 1 8-8v4a4 4 0 0 0-4 4H4z"
      />
    </svg>
  );
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, loading = false, disabled, children, ...props }, ref) => {
    const Comp: any = asChild ? Slot : "button";
    return (
      <Comp
        ref={ref}
        className={cn(buttonVariants({ variant, size, className }))}
        data-loading={loading ? "true" : undefined}
        data-disabled={disabled || loading ? "true" : undefined}
        disabled={disabled || loading}
        {...props}
      >
        {loading && <Spinner />}
        {children}
      </Comp>
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
