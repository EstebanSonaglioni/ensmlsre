"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import {
  getDashboard,
  getErrorDetail,
  type DashboardDays,
  type DashboardResult,
} from "@/lib/api";
import { formatPrice } from "@/lib/utils";

import { DashboardBreakdown } from "./dashboard-breakdown";
import { NetProfitChart } from "./net-profit-chart";
import { TopProductsChart } from "./top-products-chart";

const RANGES: DashboardDays[] = [7, 30, 90];

function formatDelta(pct: string): string {
  const n = Number(pct);
  const sign = n > 0 ? "+" : "";
  return `${sign}${pct}% vs período anterior`;
}

function Kpi({
  label,
  value,
  money = false,
  deltaPct,
  worseWhenUp = false,
}: {
  label: string;
  value: string | number;
  money?: boolean;
  deltaPct?: string | null;
  worseWhenUp?: boolean;
}) {
  let deltaClass = "text-muted";
  if (deltaPct !== undefined && deltaPct !== null) {
    const n = Number(deltaPct);
    if (n > 0) {
      deltaClass = worseWhenUp ? "text-destructive" : "text-accent";
    } else if (n < 0) {
      deltaClass = worseWhenUp ? "text-accent" : "text-destructive";
    }
  }
  return (
    <Card>
      <p className="text-[13px] text-muted">{label}</p>
      <p
        className={`mt-2 text-2xl font-semibold tabular-nums ${
          money ? "text-accent" : "text-foreground"
        }`}
      >
        {money ? formatPrice(String(value)) : value}
      </p>
      {deltaPct ? (
        <p className={`mt-1 text-[13px] tabular-nums ${deltaClass}`}>
          {formatDelta(deltaPct)}
        </p>
      ) : null}
    </Card>
  );
}

export function SellerDashboard() {
  const [days, setDays] = useState<DashboardDays>(30);
  const [data, setData] = useState<DashboardResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getDashboard(days)
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setError("");
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(getErrorDetail(err));
          setData(null);
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
  }, [days]);

  return (
    <div className="flex flex-col gap-6 xl:col-span-2">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <div className="flex gap-2">
          {RANGES.map((range) => (
            <Button
              key={range}
              type="button"
              size="sm"
              variant={days === range ? "default" : "secondary"}
              onClick={() => setDays(range)}
            >
              {range} días
            </Button>
          ))}
        </div>
      </div>
      {loading ? <p className="text-sm text-muted">Cargando...</p> : null}
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      {data ? (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <Kpi
              label="Ventas realizadas"
              value={data.sales_count}
              deltaPct={data.delta.sales_count_pct}
            />
            <Kpi
              label="Monto vendido"
              value={data.total_amount}
              money
              deltaPct={data.delta.total_amount_pct}
            />
            <Kpi
              label="Ganancia neta"
              value={data.net_profit_total}
              money
              deltaPct={data.delta.net_profit_total_pct}
            />
            <Kpi
              label="Unidades"
              value={data.units_sold}
              deltaPct={data.delta.units_sold_pct}
            />
            <Kpi
              label="Ticket promedio"
              value={data.average_ticket}
              money
              deltaPct={data.delta.average_ticket_pct}
            />
            <Kpi
              label="Ventas canceladas"
              value={data.cancelled_count}
              deltaPct={data.delta.cancelled_count_pct}
              worseWhenUp
            />
          </div>
          <NetProfitChart
            series={data.net_profit_series}
            showRange={false}
          />
          <DashboardBreakdown
            openByStatus={data.open_by_status}
            fulfillmentMix={data.fulfillment_mix}
            paymentMix={data.payment_mix}
          />
          <p className="text-[13px] text-muted">
            Órdenes abiertas: {data.open_orders}. Canceladas del período:{" "}
            {data.cancelled_count}. Reembolsos del período:{" "}
            {data.refunded_count} ({formatPrice(data.refunded_amount)}).
          </p>
          <Card>
            <CardTitle>Más vendidos</CardTitle>
            {data.top_products.length === 0 ? (
              <p className="mt-4 text-sm text-muted">
                No hay ventas completadas en este período.
              </p>
            ) : (
              <>
                <TopProductsChart items={data.top_products} />
                <div className="mt-4 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="text-[13px] text-muted">
                    <tr className="border-b border-border">
                      <th className="px-3 py-2 font-medium">Producto</th>
                      <th className="px-3 py-2 text-right font-medium">
                        Unidades
                      </th>
                      <th className="px-3 py-2 text-right font-medium">
                        Monto
                      </th>
                      <th className="px-3 py-2 text-right font-medium">
                        Ganancia neta
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.top_products.map((item) => (
                      <tr
                        key={item.product_id}
                        className="border-b border-border last:border-0 hover:bg-card-hover"
                      >
                        <td className="px-3 py-3">{item.name}</td>
                        <td className="px-3 py-3 text-right tabular-nums">
                          {item.units}
                        </td>
                        <td className="px-3 py-3 text-right tabular-nums text-accent">
                          {formatPrice(item.amount)}
                        </td>
                        <td className="px-3 py-3 text-right tabular-nums text-accent">
                          {formatPrice(item.net_profit)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                </div>
              </>
            )}
          </Card>
          {data.sellers.length > 0 ? (
            <Card>
              <CardTitle>Vendedores</CardTitle>
              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="text-[13px] text-muted">
                    <tr className="border-b border-border">
                      <th className="px-3 py-2 font-medium">Email</th>
                      <th className="px-3 py-2 text-right font-medium">
                        Ventas
                      </th>
                      <th className="px-3 py-2 text-right font-medium">
                        Monto
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.sellers.map((item) => (
                      <tr
                        key={item.email}
                        className="border-b border-border last:border-0 hover:bg-card-hover"
                      >
                        <td className="px-3 py-3">{item.email}</td>
                        <td className="px-3 py-3 text-right tabular-nums">
                          {item.sales_count}
                        </td>
                        <td className="px-3 py-3 text-right tabular-nums text-accent">
                          {formatPrice(item.amount)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
