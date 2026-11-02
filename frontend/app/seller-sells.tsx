"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import {
  getErrorDetail,
  listSells,
  transitionSell,
  type SellItem,
  type SellStatus,
} from "@/lib/api";
import { formatPrice } from "@/lib/utils";

function actionsFor(item: SellItem): { label: string; status: SellStatus }[] {
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

export function SellerSells({ refreshKey }: { refreshKey: number }) {
  const [items, setItems] = useState<SellItem[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    listSells({ as_seller: true, page_size: 100 })
      .then((result) =>
        setItems(
          result.items.filter(
            (item) =>
              item.status !== "en_carrito" && item.status !== "cancelada",
          ),
        ),
      )
      .catch((err) => {
        setError(getErrorDetail(err));
        setItems([]);
      })
      .finally(() => setLoading(false));
  }, [refreshKey]);

  async function onTransition(id: number, status: SellStatus) {
    setError("");
    try {
      const updated = await transitionSell(id, status);
      setItems((current) =>
        current.map((item) => (item.id === id ? updated : item)),
      );
    } catch (err) {
      setError(getErrorDetail(err));
    }
  }

  return (
    <Card className="xl:col-span-2">
      <CardTitle>Ventas</CardTitle>
      {loading ? <p className="mt-4 text-sm text-muted">Cargando...</p> : null}
      {error ? <p className="mt-4 text-sm text-destructive">{error}</p> : null}
      {!loading && items.length === 0 ? (
        <p className="mt-4 text-sm text-muted">No hay ventas para mostrar.</p>
      ) : null}
      <ul className="mt-4 flex flex-col gap-3">
        {items.map((item) => (
          <li
            key={item.id}
            className="flex flex-col gap-2 rounded-md border border-border p-4"
          >
            <p className="font-medium">{item.product_name}</p>
            <p className="text-[13px] text-muted">
              {item.buyer_email} · {item.status} · {formatPrice(item.subtotal)}
            </p>
            <div className="flex flex-wrap gap-2">
              {actionsFor(item).map((action) => (
                <Button
                  key={action.status}
                  type="button"
                  size="sm"
                  variant="secondary"
                  onClick={() => void onTransition(item.id, action.status)}
                >
                  {action.label}
                </Button>
              ))}
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}
