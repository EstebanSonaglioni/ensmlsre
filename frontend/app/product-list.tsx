"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  getErrorDetail,
  listMyProducts,
  listProducts,
  type ProductItem,
} from "@/lib/api";
import { formatPrice } from "@/lib/utils";

import { ProductImage } from "./product-image";

const PAGE_SIZE = 10;

export function ProductList({
  refreshKey,
  mine = false,
}: {
  refreshKey: number;
  mine?: boolean;
}) {
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [debouncedQ, setDebouncedQ] = useState("");
  const [items, setItems] = useState<ProductItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (mine) {
      return;
    }
    const handle = window.setTimeout(() => {
      setDebouncedQ(q.trim());
      setPage(1);
    }, 300);
    return () => window.clearTimeout(handle);
  }, [q, mine]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const load = mine
      ? listMyProducts({ page, page_size: PAGE_SIZE })
      : listProducts({
          page,
          page_size: PAGE_SIZE,
          ...(debouncedQ ? { q: debouncedQ } : {}),
        });
    load
      .then((result) => {
        if (cancelled) {
          return;
        }
        setItems(result.items);
        setTotal(result.total);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(getErrorDetail(err));
          setItems([]);
          setTotal(0);
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
  }, [page, refreshKey, mine, debouncedQ]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <Card className="flex flex-col gap-4 xl:col-span-2">
      <CardTitle>{mine ? "Tus publicaciones" : "Productos"}</CardTitle>
      {!mine ? (
        <Input
          type="search"
          name="q"
          value={q}
          placeholder="Buscar por nombre"
          aria-label="Buscar por nombre"
          onChange={(event) => setQ(event.target.value)}
        />
      ) : null}
      {loading ? <p className="text-sm text-muted">Cargando...</p> : null}
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      {!loading && items.length === 0 ? (
        <p className="text-sm text-muted">No hay publicaciones para mostrar.</p>
      ) : null}
      <ul className="grid grid-cols-[repeat(auto-fill,calc(25vh+12px))] gap-4">
        {items.map((item) => (
          <li
            key={item.id}
            className="flex h-full w-full flex-col rounded-md border border-border p-[5px] hover:bg-card-hover"
          >
            <Link href={`/productos/${item.id}`} className="flex min-h-0 flex-1 flex-col">
              <ProductImage productId={item.id} alt={item.name} />
              <div className="mt-2 flex min-h-[7.5rem] flex-1 flex-col">
                <p className="line-clamp-2 font-medium">{item.name}</p>
                <p className="line-clamp-2 text-[13px] text-muted">
                  {item.store_name} · {item.category} / {item.subcategory}
                </p>
                <p className="mt-1 font-medium tabular-nums text-accent">
                  {formatPrice(item.price)}
                </p>
                <p className="text-[13px] text-muted">
                  Cantidad: {item.quantity}
                </p>
              </div>
            </Link>
            {mine ? (
              <div className="mt-3">
                <Badge variant={item.paused ? "warning" : "default"}>
                  {item.paused ? "Pausado" : "Activa"}
                </Badge>
              </div>
            ) : null}
          </li>
        ))}
      </ul>
      {total > PAGE_SIZE ? (
        <div className="flex items-center gap-3 text-[13px] text-muted">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((current) => current - 1)}
          >
            Anterior
          </Button>
          {page} / {totalPages}
          <Button
            type="button"
            variant="secondary"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage((current) => current + 1)}
          >
            Siguiente
          </Button>
        </div>
      ) : null}
    </Card>
  );
}
