"use client";

import { ArrowDown, ArrowUp } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardTitle } from "@/components/ui/card";
import {
  getErrorDetail,
  listSells,
  type SellItem,
  type SellSort,
} from "@/lib/api";
import { formatDateTime, formatPrice } from "@/lib/utils";

import { NetProfitChart } from "./net-profit-chart";
import { statusBadgeVariant, statusLabel } from "./order-status";

type SortOrder = "asc" | "desc";

const COLUMNS: { key: SellSort; label: string; align?: "right" }[] = [
  { key: "id", label: "Orden" },
  { key: "created_at", label: "Fecha" },
  { key: "product_name", label: "Producto" },
  { key: "buyer_email", label: "Comprador" },
  { key: "fulfillment", label: "Entrega" },
  { key: "status", label: "Estado" },
  { key: "subtotal", label: "Total", align: "right" },
];

function SortHeader({
  column,
  label,
  align,
  sort,
  order,
  onSort,
}: {
  column: SellSort;
  label: string;
  align?: "right";
  sort: SellSort;
  order: SortOrder;
  onSort: (column: SellSort) => void;
}) {
  const active = sort === column;
  return (
    <th
      className={`px-3 py-2 font-medium ${align === "right" ? "text-right" : ""}`}
      aria-sort={active ? (order === "asc" ? "ascending" : "descending") : "none"}
    >
      <button
        type="button"
        onClick={() => onSort(column)}
        className={`inline-flex items-center gap-1 hover:text-foreground ${
          align === "right" ? "ml-auto" : ""
        } ${active ? "text-foreground" : "text-muted"}`}
      >
        {label}
        {active && order === "asc" ? (
          <ArrowUp className="size-3.5" />
        ) : active ? (
          <ArrowDown className="size-3.5" />
        ) : null}
      </button>
    </th>
  );
}

export function OrderList({ asSeller }: { asSeller: boolean }) {
  const [items, setItems] = useState<SellItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sort, setSort] = useState<SellSort>("created_at");
  const [order, setOrder] = useState<SortOrder>("desc");
  const base = asSeller ? "/ventas" : "/compras";

  useEffect(() => {
    setLoading(true);
    listSells({ as_seller: asSeller, page_size: 100, sort, order })
      .then((result) =>
        setItems(result.items.filter((item) => item.status !== "en_carrito")),
      )
      .catch((err) => {
        setError(getErrorDetail(err));
        setItems([]);
      })
      .finally(() => setLoading(false));
  }, [asSeller, sort, order]);

  function onSort(column: SellSort) {
    if (sort === column) {
      setOrder((current) => (current === "asc" ? "desc" : "asc"));
      return;
    }
    setSort(column);
    setOrder(column === "created_at" || column === "id" ? "desc" : "asc");
  }

  return (
    <div className="flex flex-col gap-6 xl:col-span-2">
      {asSeller ? <NetProfitChart /> : null}
      <Card>
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
                  {COLUMNS.map((column) => (
                    <SortHeader
                      key={column.key}
                      column={column.key}
                      label={column.label}
                      align={column.align}
                      sort={sort}
                      order={order}
                      onSort={onSort}
                    />
                  ))}
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
                    <td className="px-3 py-3 text-[13px] text-muted tabular-nums">
                      {item.created_at ? formatDateTime(item.created_at) : "—"}
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
    </div>
  );
}
