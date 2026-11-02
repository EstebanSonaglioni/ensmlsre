"use client";

import { Bell } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import type { NotificationItem } from "@/lib/api";
import { useRealtime } from "@/lib/realtime";
import { cn } from "@/lib/utils";

function notificationHref(item: NotificationItem): string {
  if (
    (item.kind === "pregunta" || item.kind === "respuesta") &&
    item.product_id
  ) {
    return `/productos/${item.product_id}`;
  }
  if (!item.sell_id) {
    return "/";
  }
  return item.as_seller ? `/ventas/${item.sell_id}` : `/compras/${item.sell_id}`;
}

export function NotificationBell() {
  const { notifications, unread, markRead, markAllRead } = useRealtime();
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <button
        type="button"
        className="relative rounded-md p-2 text-muted hover:bg-card-hover hover:text-foreground"
        aria-label="Notificaciones"
        onClick={() => setOpen((current) => !current)}
      >
        <Bell className="size-4" />
        {unread > 0 ? (
          <span className="absolute top-1 right-1 inline-flex min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] text-primary-foreground">
            {unread > 9 ? "9+" : unread}
          </span>
        ) : null}
      </button>
      {open ? (
        <div className="absolute right-0 z-20 mt-2 w-72 rounded-md border border-border bg-card p-2 shadow-[0_1px_0_#0006]">
          <div className="mb-2 flex items-center justify-between px-1">
            <p className="text-[13px] font-medium">Notificaciones</p>
            {unread > 0 ? (
              <button
                type="button"
                className="text-[12px] text-primary"
                onClick={() => void markAllRead()}
              >
                Marcar leídas
              </button>
            ) : null}
          </div>
          {notifications.length === 0 ? (
            <p className="px-1 py-3 text-[13px] text-muted">
              No hay notificaciones.
            </p>
          ) : (
            <ul className="flex max-h-72 flex-col gap-1 overflow-y-auto">
              {notifications.map((item) => {
                const href = notificationHref(item);
                return (
                  <li key={item.id}>
                    <Link
                      href={href}
                      className={cn(
                        "block rounded-md px-2 py-2 text-[13px] hover:bg-card-hover",
                        item.read_at ? "text-muted" : "text-foreground",
                      )}
                      onClick={() => {
                        setOpen(false);
                        if (!item.read_at) {
                          void markRead(item.id);
                        }
                      }}
                    >
                      <p className="font-medium">{item.title}</p>
                      <p className="text-muted">{item.body}</p>
                    </Link>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      ) : null}
    </div>
  );
}
