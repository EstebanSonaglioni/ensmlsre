"use client";

import { useEffect, useState } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import {
  getDashboard,
  getErrorDetail,
  type DashboardDays,
  type NetProfitDay,
} from "@/lib/api";
import {
  CHART_BORDER,
  CHART_GRID,
  legendStyle,
  tickStyle,
  tooltipItemStyle,
  tooltipLabelStyle,
  tooltipStyle,
} from "@/lib/chart-theme";
import { formatPrice } from "@/lib/utils";

const RANGES: DashboardDays[] = [7, 30, 90];

function tickLabel(iso: string): string {
  const parts = iso.split("-");
  if (parts.length !== 3) {
    return iso;
  }
  return `${parts[2]}/${parts[1]}`;
}

export function NetProfitChart({
  series: seriesProp,
  loading: loadingProp,
  error: errorProp,
  showRange = true,
}: {
  series?: NetProfitDay[];
  loading?: boolean;
  error?: string;
  showRange?: boolean;
}) {
  const controlled = seriesProp !== undefined;
  const [days, setDays] = useState<DashboardDays>(30);
  const [fetched, setFetched] = useState<NetProfitDay[]>([]);
  const [loadingFetch, setLoadingFetch] = useState(!controlled);
  const [errorFetch, setErrorFetch] = useState("");

  useEffect(() => {
    if (controlled) {
      return;
    }
    let cancelled = false;
    setLoadingFetch(true);
    getDashboard(days)
      .then((result) => {
        if (!cancelled) {
          setFetched(result.net_profit_series);
          setErrorFetch("");
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setErrorFetch(getErrorDetail(err));
          setFetched([]);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoadingFetch(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [controlled, days]);

  const series = controlled ? seriesProp : fetched;
  const loading = controlled ? Boolean(loadingProp) : loadingFetch;
  const error = controlled ? errorProp || "" : errorFetch;
  const hasData = series.some(
    (row) => Number(row.net_profit) > 0 || Number(row.amount) > 0,
  );

  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <CardTitle>Monto y ganancia neta</CardTitle>
        {showRange ? (
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
        ) : null}
      </div>
      {loading ? <p className="mt-4 text-sm text-muted">Cargando...</p> : null}
      {error ? <p className="mt-4 text-sm text-destructive">{error}</p> : null}
      {!loading && !error && !hasData ? (
        <p className="mt-4 text-sm text-muted">
          No hay ventas completadas en el período.
        </p>
      ) : null}
      {!loading && !error && series.length > 0 ? (
        <div className="mt-4 h-60">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={series.map((row) => ({
                date: row.date,
                amount: Number(row.amount),
                net_profit: Number(row.net_profit),
              }))}
            >
              <CartesianGrid stroke={CHART_GRID} vertical={false} />
              <XAxis
                dataKey="date"
                tickFormatter={tickLabel}
                tick={tickStyle}
                axisLine={{ stroke: CHART_BORDER }}
                tickLine={false}
              />
              <YAxis
                tickFormatter={(value: number) => formatPrice(String(value))}
                tick={tickStyle}
                axisLine={false}
                tickLine={false}
                width={72}
              />
              <Tooltip
                contentStyle={tooltipStyle}
                itemStyle={tooltipItemStyle}
                labelStyle={tooltipLabelStyle}
                formatter={(value, name) => [
                  formatPrice(String(value ?? 0)),
                  name === "amount" ? "Monto vendido" : "Ganancia neta",
                ]}
                labelFormatter={(label) => String(label)}
              />
              <Legend
                wrapperStyle={legendStyle}
                formatter={(value) =>
                  value === "amount" ? "Monto vendido" : "Ganancia neta"
                }
              />
              <Area
                type="monotone"
                dataKey="amount"
                stroke="#6B7280"
                fill="#6B728022"
                strokeWidth={2}
                name="amount"
              />
              <Line
                type="monotone"
                dataKey="net_profit"
                stroke="#10B981"
                strokeWidth={2}
                dot={false}
                name="net_profit"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      ) : null}
    </Card>
  );
}
