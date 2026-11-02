"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardTitle } from "@/components/ui/card";
import { getErrorDetail, listSells, type SellItem } from "@/lib/api";
import { formatPrice } from "@/lib/utils";

import { statusBadgeVariant, statusLabel } from "./order-status";

export function OrderList({ asSeller }: { asSeller: boolean }) {
  const [items, setItems] = useState<SellItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const base = asSeller ? "/ventas" : "/compras";

  useEffect(() => {
    setLoading(true);
    listSells({ as_seller: asSeller, page_size: 100 })
      .then((result) =>
        setItems(
          result.items.filter((item) => item.status !== "en_carrito"),
        ),
      )
      .catch((err) => {
        setError(getErrorDetail(err));
        setItems([]);
      })
      .finally(() => setLoading(false));
  }, [asSeller]);

  return (
    <Card className="xl:col-span-2">
      <CardTitle>{asSeller ? "Ventas" : "Compras"}</CardTitle>
      {loading ? <p className="mt-4 text-sm text-muted">Cargando...</p> : null}
      {error ? <p className="mt-4 text-sm text-destructive">{error}</p> : null}
      {!loading && items.length === 0 ? (
        <p className="mt-4 text-sm text-muted">
          {asSeller
            ? "No hay ventas para mostrar."
            : "No hay compras para mostrar."}
        </p>
      ) : null}
      {asSeller && items.length > 0 ? (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-[13px] text-muted">
              <tr className="border-b border-border">
                <th className="px-3 py-2 font-medium">Orden</th>
                <th className="px-3 py-2 font-medium">Producto</th>
                <th className="px-3 py-2 font-medium">Comprador</th>
                <th className="px-3 py-2 font-medium">Entrega</th>
                <th className="px-3 py-2 font-medium">Estado</th>
                <th className="px-3 py-2 text-right font-medium">Total</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr
                  key={item.id}
                  className="border-b border-border last:border-0 hover:bg-card-hover"
                >
                  <td className="px-3 py-3">
                    <Link href={`${base}/${item.id}`} className="text-primary">
                      #{item.id}
                    </Link>
                  </td>
                  <td className="px-3 py-3">{item.product_name}</td>
                  <td className="px-3 py-3 text-[13px] text-muted">
                    {item.buyer_email}
                  </td>
                  <td className="px-3 py-3 text-[13px] text-muted">
                    {item.fulfillment === "envio" ? "Envío" : "Retiro"}
                  </td>
                  <td className="px-3 py-3">
                    <Badge variant={statusBadgeVariant(item.status)}>
                      {statusLabel(item.status)}
                    </Badge>
                  </td>
                  <td className="px-3 py-3 text-right font-medium tabular-nums text-accent">
                    {formatPrice(item.subtotal)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
      {!asSeller && items.length > 0 ? (
        <ul className="mt-4 flex flex-col gap-3">
          {items.map((item) => (
            <li key={item.id}>
              <Link
                href={`${base}/${item.id}`}
                className="block rounded-md border border-border p-4 hover:bg-card-hover"
              >
                <p className="font-medium">{item.product_name}</p>
                <p className="text-[13px] text-muted">
                  {item.store_name} · {statusLabel(item.status)} ·{" "}
                  {formatPrice(item.subtotal)}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      ) : null}
    </Card>
  );
}
