"use client";

import { useEffect, useState } from "react";

import { fetchProductImage } from "@/lib/api";
import { cn } from "@/lib/utils";

export function ProductImage({
  productId,
  alt,
  refreshKey = 0,
  variant = "list",
}: {
  productId: number;
  alt: string;
  refreshKey?: number;
  variant?: "list" | "detail";
}) {
  const [src, setSrc] = useState("");

  useEffect(() => {
    let cancelled = false;
    let objectUrl = "";
    fetchProductImage(productId)
      .then((url) => {
        objectUrl = url;
        if (!cancelled) {
          setSrc(url);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setSrc("");
        }
      });
    return () => {
      cancelled = true;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [productId, refreshKey]);

  const frame = cn(
    "overflow-hidden bg-card-hover",
    variant === "detail"
      ? "aspect-square size-[min(100%,50vh)] max-h-[50vh] max-w-[50vh] shrink-0 rounded-md border border-border"
      : "mx-auto aspect-square w-full rounded-sm",
  );

  if (!src) {
    return (
      <div className={cn(frame, "flex items-center justify-center text-[13px] text-muted")}>
        Sin imagen
      </div>
    );
  }

  return (
    <div className={frame}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={src} alt={alt} className="size-full object-cover" />
    </div>
  );
}
