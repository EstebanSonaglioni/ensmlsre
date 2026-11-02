import { type HTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/utils";

const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "rounded-md border border-border bg-card p-6 text-card-foreground shadow-[0_1px_0_#0006]",
        className,
      )}
      {...props}
    />
  ),
);
Card.displayName = "Card";

function CardTitle({
  className,
  ...props
}: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h2
      className={cn("text-lg font-semibold text-foreground", className)}
      {...props}
    />
  );
}

function CardDescription({
  className,
  ...props
}: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn("text-[13px] text-muted", className)} {...props} />
  );
}

export { Card, CardDescription, CardTitle };
