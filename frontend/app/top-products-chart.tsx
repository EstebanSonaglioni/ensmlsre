"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { DashboardProduct } from "@/lib/api";
import {
  CHART_GRID,
  legendStyle,
  tickStyle,
  tooltipItemStyle,
  tooltipLabelStyle,
  tooltipStyle,
} from "@/lib/chart-theme";
import { formatPrice } from "@/lib/utils";

export function TopProductsChart({ items }: { items: DashboardProduct[] }) {
  const data = items.map((item) => ({
    name: item.name,
    amount: Number(item.amount),
    net_profit: Number(item.net_profit),
  }));
  const height = Math.max(224, items.length * 44 + 56);
  return (
    <div className="mt-4" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 8, right: 12, left: 8, bottom: 8 }}
        >
          <CartesianGrid stroke={CHART_GRID} horizontal={false} />
          <XAxis
            type="number"
            tickFormatter={(value: number) => formatPrice(String(value))}
            tick={tickStyle}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={88}
            interval={0}
            tick={tickStyle}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={tooltipStyle}
            itemStyle={tooltipItemStyle}
            labelStyle={tooltipLabelStyle}
            formatter={(value, name) => [
              formatPrice(String(value ?? 0)),
              name === "amount" ? "Monto" : "Ganancia neta",
            ]}
          />
          <Legend
            wrapperStyle={legendStyle}
            formatter={(value) =>
              value === "amount" ? "Monto" : "Ganancia neta"
            }
          />
          <Bar dataKey="amount" fill="#6B7280" radius={[0, 4, 4, 0]} />
          <Bar dataKey="net_profit" fill="#10B981" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
