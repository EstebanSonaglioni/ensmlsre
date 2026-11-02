"use client";

import { FormEvent, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getErrorDetail, listStores, type StoreItem } from "@/lib/api";

const PAGE_SIZE = 10;

type StoreListProps = {
  refreshKey: number;
};

export function StoreList({ refreshKey }: StoreListProps) {
  const [q, setQ] = useState("");
  const [appliedQ, setAppliedQ] = useState("");
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<StoreItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    listStores({ q: appliedQ, page, page_size: PAGE_SIZE })
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
  }, [appliedQ, page, refreshKey]);

  function onSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(1);
    setAppliedQ(q);
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <Card className="flex flex-col gap-4">
      <CardTitle>Tus tiendas</CardTitle>
      <form className="flex flex-col items-stretch gap-2 sm:flex-row sm:items-end" onSubmit={onSearch}>
        <Label className="flex-1">
          Buscar
          <Input
            type="search"
            name="q"
            placeholder="Nombre de tienda"
            value={q}
            onChange={(event) => setQ(event.target.value)}
          />
        </Label>
        <Button type="submit" variant="secondary">
          Buscar
        </Button>
      </form>
      {loading ? <p className="text-sm text-muted">Cargando...</p> : null}
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      {!loading && !error && items.length === 0 ? (
        <p className="text-sm text-muted">No tenés tiendas asociadas.</p>
      ) : null}
      {!loading && !error && items.length > 0 ? (
        <ul className="divide-y divide-border">
          {items.map((item) => (
            <li
              key={item.id}
              className="flex items-center justify-between py-3 text-sm hover:bg-card-hover"
            >
              <span>{item.name}</span>
              <Badge>{item.role}</Badge>
            </li>
          ))}
        </ul>
      ) : null}
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
