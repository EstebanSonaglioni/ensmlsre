"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import {
  getErrorDetail,
  listSellerQuestions,
  type SellerQuestionSort,
  type SellerQuestionStatus,
} from "@/lib/api";
import { formatPrice } from "@/lib/utils";

const FILTERS: { id: SellerQuestionStatus; label: string }[] = [
  { id: "pending", label: "Pendientes" },
  { id: "answered", label: "Respondidas" },
  { id: "all", label: "Todas" },
];

const COLUMNS: { id: SellerQuestionSort; label: string; align?: "right" }[] = [
  { id: "name", label: "Producto" },
  { id: "created_at", label: "Desde" },
  { id: "wait", label: "Espera", align: "right" },
  { id: "net_profit", label: "Ganancia neta", align: "right" },
  { id: "score", label: "Criticidad", align: "right" },
];

function formatWhen(iso: string): string {
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) {
    return iso;
  }
  return parsed.toLocaleString("es-AR", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

export function SellerQuestions() {
  const [status, setStatus] = useState<SellerQuestionStatus>("pending");
  const [sort, setSort] = useState<SellerQuestionSort>("score");
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [items, setItems] = useState<
    Awaited<ReturnType<typeof listSellerQuestions>>["items"]
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const pageSize = 100;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listSellerQuestions({
      status,
      sort,
      order,
      page,
      page_size: pageSize,
    })
      .then((result) => {
        if (!cancelled) {
          setItems(result.items);
          setTotal(result.total);
          setError("");
        }
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
  }, [status, sort, order, page]);

  function onSort(column: SellerQuestionSort) {
    if (sort === column) {
      setOrder((current) => (current === "desc" ? "asc" : "desc"));
    } else {
      setSort(column);
      setOrder(column === "name" ? "asc" : "desc");
    }
    setPage(1);
  }

  const pages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="flex flex-col gap-6 xl:col-span-2">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Preguntas</h1>
        <div className="flex gap-2">
          {FILTERS.map((filter) => (
            <Button
              key={filter.id}
              type="button"
              size="sm"
              variant={status === filter.id ? "default" : "secondary"}
              onClick={() => {
                setStatus(filter.id);
                setPage(1);
              }}
            >
              {filter.label}
            </Button>
          ))}
        </div>
      </div>
      <Card>
        <CardTitle>Bandeja</CardTitle>
        {loading ? <p className="mt-4 text-sm text-muted">Cargando...</p> : null}
        {error ? <p className="mt-4 text-sm text-destructive">{error}</p> : null}
        {!loading && items.length === 0 ? (
          <p className="mt-4 text-sm text-muted">
            No hay preguntas para mostrar.
          </p>
        ) : null}
        {items.length > 0 ? (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-[13px] text-muted">
                <tr className="border-b border-border">
                  {COLUMNS.map((column) => (
                    <th
                      key={column.id}
                      className={`px-3 py-2 font-medium ${
                        column.align === "right" ? "text-right" : ""
                      }`}
                    >
                      <button
                        type="button"
                        className="hover:text-foreground"
                        onClick={() => onSort(column.id)}
                      >
                        {column.label}
                        {sort === column.id ? (order === "desc" ? " ↓" : " ↑") : ""}
                      </button>
                    </th>
                  ))}
                  <th className="px-3 py-2 font-medium">Pregunta</th>
                  <th className="px-3 py-2 font-medium">Estado</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr
                    key={item.id}
                    className="border-b border-border last:border-0 hover:bg-card-hover"
                  >
                    <td className="px-3 py-3">
                      <Link
                        href={`/productos/${item.product_id}`}
                        className="text-primary"
                      >
                        {item.product_name}
                      </Link>
                    </td>
                    <td className="px-3 py-3 text-[13px] text-muted">
                      {formatWhen(item.created_at)}
                    </td>
                    <td className="px-3 py-3 text-right tabular-nums">
                      {item.wait_hours}
                    </td>
                    <td className="px-3 py-3 text-right tabular-nums text-accent">
                      {formatPrice(item.net_profit)}
                    </td>
                    <td className="px-3 py-3 text-right tabular-nums font-medium">
                      {item.score}
                    </td>
                    <td className="px-3 py-3">{item.text}</td>
                    <td className="px-3 py-3">
                      {item.answer ? (
                        <Badge variant="accent">Respondida</Badge>
                      ) : (
                        <Badge variant="warning">Pendiente</Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
        {total > pageSize ? (
          <div className="mt-4 flex gap-2">
            <Button
              type="button"
              size="sm"
              variant="secondary"
              disabled={page <= 1}
              onClick={() => setPage((current) => current - 1)}
            >
              Anterior
            </Button>
            <Button
              type="button"
              size="sm"
              variant="secondary"
              disabled={page >= pages}
              onClick={() => setPage((current) => current + 1)}
            >
              Siguiente
            </Button>
          </div>
        ) : null}
      </Card>
    </div>
  );
}
