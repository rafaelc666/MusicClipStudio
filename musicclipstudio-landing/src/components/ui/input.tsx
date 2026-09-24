import * as React from "react";
import { cn } from "@/lib/utils";

const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        ref={ref}
        className={cn(
          "flex h-9 w-full rounded-sm border border-white/5 bg-bg-3/60 px-3 py-1.5 text-[13px] text-fg-0 placeholder:text-fg-3 shadow-inner shadow-black/20 transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-fg-1 focus-visible:outline-none focus-visible:border-neon/50 focus-visible:ring-2 focus-visible:ring-neon/20 disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "flex min-h-[100px] w-full rounded-sm border border-white/5 bg-bg-3/60 p-3 text-[13px] text-fg-0 placeholder:text-fg-3 shadow-inner shadow-black/20 transition-colors resize-y focus-visible:outline-none focus-visible:border-neon/50 focus-visible:ring-2 focus-visible:ring-neon/20 disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    />
  )
);
Textarea.displayName = "Textarea";

export { Input, Textarea };
