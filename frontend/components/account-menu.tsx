"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { fetchProfileImage } from "@/lib/api";
import { cn } from "@/lib/utils";

const AVATAR_COLORS = [
  "bg-primary text-primary-foreground",
  "bg-accent text-primary-foreground",
  "bg-warning text-primary-foreground",
  "bg-info text-primary-foreground",
  "bg-destructive text-primary-foreground",
] as const;

function colorForEmail(email: string): string {
  let hash = 0;
  for (const char of email) {
    hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
  }
  return AVATAR_COLORS[hash % AVATAR_COLORS.length];
}

function AvatarFace({
  email,
  src,
}: {
  email: string;
  src: string;
}) {
  const letter = (email.trim().charAt(0) || "?").toUpperCase();
  if (src) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img src={src} alt="" className="size-9 rounded-full object-cover" />
    );
  }
  return (
    <span
      className={cn(
        "flex size-9 items-center justify-center rounded-full text-sm font-semibold",
        colorForEmail(email),
      )}
    >
      {letter}
    </span>
  );
}

export function AccountMenu({
  email,
  displayName,
  hasAvatar,
  onLogout,
}: {
  email: string;
  displayName: string;
  hasAvatar: boolean;
  onLogout: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [src, setSrc] = useState("");
  const root = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!hasAvatar) {
      setSrc("");
      return;
    }
    let cancelled = false;
    let objectUrl = "";
    fetchProfileImage()
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
  }, [hasAvatar]);

  useEffect(() => {
    function onPointer(event: MouseEvent) {
      if (!root.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, []);

  return (
    <div className="relative" ref={root}>
      <button
        type="button"
        className="rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        aria-label="Cuenta"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <AvatarFace email={email} src={src} />
      </button>
      {open ? (
        <div className="absolute right-0 z-20 mt-2 w-64 rounded-md border border-border bg-card p-2 shadow-[0_1px_0_#0006]">
          <div className="border-b border-border px-3 py-2">
            {displayName ? (
              <p className="truncate text-sm font-medium">{displayName}</p>
            ) : null}
            <p className="truncate text-[13px] text-muted">{email}</p>
          </div>
          <Link
            href="/perfil"
            className="mt-1 block rounded-md px-3 py-2 text-sm hover:bg-card-hover"
          >
            Perfil
          </Link>
          <button
            type="button"
            className="w-full rounded-md px-3 py-2 text-left text-sm hover:bg-card-hover"
            onClick={onLogout}
          >
            Cerrar sesión
          </button>
        </div>
      ) : null}
    </div>
  );
}
