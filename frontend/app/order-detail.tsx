"use client";

import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  getErrorDetail,
  getSell,
  listSellMessages,
  sendSellMessage,
  transitionSell,
  type SellItem,
  type SellMessageItem,
  type SellStatus,
} from "@/lib/api";
import { useRealtime } from "@/lib/realtime";
import { cn, formatPrice } from "@/lib/utils";

import { formatEta, statusBadgeVariant, statusLabel } from "./order-status";

function actionsFor(item: SellItem): { label: string; status: SellStatus }[] {
  if (!item.can_manage) {
    return [];
  }
  if (item.status === "en_curso" && item.fulfillment === "envio") {
    return [{ label: "Despachar", status: "en_viaje" }];
  }
  if (item.status === "en_curso" && item.fulfillment === "retiro") {
    return [{ label: "Listo para retiro", status: "esperando_retiro" }];
  }
  if (item.status === "en_viaje") {
    return [
      { label: "Marcar entregado", status: "completada" },
      { label: "Reembolsar", status: "reembolsada" },
    ];
  }
  if (item.status === "esperando_retiro") {
    return [
      { label: "Marcar retirado", status: "completada" },
      { label: "Reembolsar", status: "reembolsada" },
    ];
  }
  if (item.status === "completada") {
    return [{ label: "Reembolsar", status: "reembolsada" }];
  }
  return [];
}

function showEta(item: SellItem): boolean {
  if (item.fulfillment !== "envio" || !item.eta_at) {
    return false;
  }
  return item.status === "en_viaje" || item.status === "completada";
}

export function OrderDetail({
  sellId,
  asSeller,
}: {
  sellId: number;
  asSeller: boolean;
}) {
  const back = asSeller ? "/ventas" : "/compras";
  const { watchSell, unwatchSell, onSellMessage, onSellStatus } = useRealtime();
  const [sell, setSell] = useState<SellItem | null>(null);
  const [messages, setMessages] = useState<SellMessageItem[]>([]);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const listRef = useRef<HTMLUListElement>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([getSell(sellId), listSellMessages(sellId, { page_size: 100 })])
      .then(([order, chat]) => {
        if (cancelled) {
          return;
        }
        setSell(order);
        setMessages(chat.items);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(getErrorDetail(err));
          setSell(null);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [sellId]);

  useEffect(() => {
    watchSell(sellId);
    const offMessage = onSellMessage(sellId, (message) => {
      setMessages((current) =>
        current.some((item) => item.id === message.id)
          ? current
          : [...current, message],
      );
    });
    const offStatus = onSellStatus(sellId, setSell);
    return () => {
      unwatchSell(sellId);
      offMessage();
      offStatus();
    };
  }, [sellId, watchSell, unwatchSell, onSellMessage, onSellStatus]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages.length]);

  async function onSend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const body = draft.trim();
    if (!body) {
      return;
    }
    try {
      const created = await sendSellMessage(sellId, body);
      setDraft("");
      setMessages((current) =>
        current.some((item) => item.id === created.id)
          ? current
          : [...current, created],
      );
    } catch (err) {
      setError(getErrorDetail(err));
    }
  }

  async function onTransition(status: SellStatus) {
    setError("");
    try {
      const updated = await transitionSell(sellId, status);
      setSell(updated);
    } catch (err) {
      setError(getErrorDetail(err));
    }
  }

  if (loading) {
    return (
      <Card className="xl:col-span-2">
        <p className="text-sm text-muted">Cargando...</p>
      </Card>
    );
  }

  if (!sell) {
    return (
      <Card className="xl:col-span-2">
        <p className="text-sm text-destructive">
          {error || "No se pudo completar la solicitud"}
        </p>
        <Link href={back} className="mt-4 inline-block text-sm text-primary">
          Volver
        </Link>
      </Card>
    );
  }

  return (
    <>
      <Card className="flex flex-col gap-4">
        <div>
          <Link href={back} className="text-sm text-primary">
            {asSeller ? "Volver a ventas" : "Volver a compras"}
          </Link>
          <CardTitle className="mt-2">{sell.product_name}</CardTitle>
          <p className="mt-1 font-medium tabular-nums text-accent">
            {formatPrice(sell.subtotal)}
          </p>
          <p className="mt-1 text-[13px] text-muted">
            #{sell.id} · {sell.store_name} · cantidad {sell.quantity}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={statusBadgeVariant(sell.status)}>
            {statusLabel(sell.status)}
          </Badge>
          <span className="text-[13px] text-muted">
            {sell.fulfillment === "envio" ? "Envío" : "Retiro"}
          </span>
        </div>
        {showEta(sell) ? (
          <p className="text-sm">
            Tiempo estimado de arribo: {formatEta(sell.eta_at!)}
          </p>
        ) : null}
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        {actionsFor(sell).length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {actionsFor(sell).map((action) => (
              <Button
                key={action.status}
                type="button"
                size="sm"
                variant="secondary"
                onClick={() => void onTransition(action.status)}
              >
                {action.label}
              </Button>
            ))}
          </div>
        ) : null}
      </Card>
      <Card className="flex min-h-80 h-full flex-col gap-3">
        <CardTitle>Mensajes</CardTitle>
        <ul
          ref={listRef}
          className="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto text-sm"
        >
          {messages.length === 0 ? (
            <li className="text-muted">Todavía no hay mensajes.</li>
          ) : null}
          {messages.map((item) => (
            <li
              key={item.id}
              className={cn(
                "max-w-[85%] rounded-md border p-2",
                item.mine
                  ? "ml-auto border-primary/30 bg-primary/15"
                  : "mr-auto border-border bg-card-hover",
              )}
            >
              <p>{item.body}</p>
              <p
                className={cn(
                  "mt-1 text-[12px] text-muted",
                  item.mine ? "text-right" : "text-left",
                )}
              >
                {formatEta(item.created_at)}
              </p>
            </li>
          ))}
        </ul>
        <form className="mt-auto flex shrink-0 gap-2" onSubmit={onSend}>
          <Input
            name="message"
            value={draft}
            maxLength={1000}
            onChange={(event) => setDraft(event.target.value)}
            aria-label="Mensaje"
          />
          <Button type="submit">Enviar</Button>
        </form>
      </Card>
    </>
  );
}
