import { type HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  variant?: "default" | "warning" | "info" | "accent" | "destructive";
};

const variants: Record<NonNullable<BadgeProps["variant"]>, string> = {
  default: "bg-primary/20 text-primary",
  warning: "bg-warning/20 text-warning",
  info: "bg-info/20 text-info",
  accent: "bg-accent/20 text-accent",
  destructive: "bg-destructive/20 text-destructive",
};

export function Badge({
  className,
  variant = "default",
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2.5 py-0.5 text-[12px] font-medium",
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}
