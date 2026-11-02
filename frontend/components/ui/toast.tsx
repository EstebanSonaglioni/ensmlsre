"use client";

import { useEffect } from "react";
import { createPortal } from "react-dom";

export function Toast({
  message,
  onDismiss,
}: {
  message: string;
  onDismiss: () => void;
}) {
  useEffect(() => {
    const timer = window.setTimeout(onDismiss, 4000);
    return () => window.clearTimeout(timer);
  }, [message, onDismiss]);

  return createPortal(
    <div
      role="status"
      className="fixed bottom-6 right-6 z-50 rounded-md border border-border bg-card px-4 py-3 text-sm text-foreground shadow-[0_1px_0_#0006]"
    >
      {message}
    </div>,
    document.body,
  );
}
