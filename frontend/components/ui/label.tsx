import { type LabelHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/utils";

const Label = forwardRef<HTMLLabelElement, LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, ...props }, ref) => (
    <label
      ref={ref}
      className={cn(
        "flex flex-col gap-2 text-[12px] leading-none text-muted",
        className,
      )}
      {...props}
    />
  ),
);
Label.displayName = "Label";

export { Label };
