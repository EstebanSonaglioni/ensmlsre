"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardTitle } from "@/components/ui/card";
import type { MixSlice, OpenByStatus } from "@/lib/api";
import {
  CHART_GRID,
  tickStyle,
  tooltipItemStyle,
  tooltipLabelStyle,
  tooltipStyle,
} from "@/lib/chart-theme";
import { formatPrice } from "@/lib/utils";

const COLORS = ["#10B981", "#6B7280", "#60A5FA", "#FBBF24"];

const FULFILLMENT: Record<string, string> = {
  envio: "Envío",
  retiro: "Retiro",
};

const PAYMENT: Record<string, string> = {
  tarjeta: "Tarjeta",
  transferencia: "Transferencia",
  efectivo: "Efectivo",
};

const OPEN_LABELS: { key: keyof OpenByStatus; label: string }[] = [
  { key: "en_curso", label: "En curso" },
  { key: "en_viaje", label: "En viaje" },
  { key: "esperando_retiro", label: "Esperando retiro" },
];

function MixPie({
  title,
  items,
  labels,
}: {
  title: string;
  items: MixSlice[];
  labels: Record<string, string>;
}) {
  const data = items.map((item) => ({
    name: labels[item.key] || item.key,
    value: Number(item.amount),
    count: item.count,
  }));
  return (
    <div className="min-w-0 flex-1">
      <p className="text-[13px] text-muted">{title}</p>
      {data.length === 0 ? (
        <p className="mt-3 text-sm text-muted">Sin ventas completadas.</p>
      ) : (
        <div className="mt-2 h-44">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                innerRadius={36}
                outerRadius={64}
                paddingAngle={2}
              >
                {data.map((entry, index) => (
                  <Cell
                    key={entry.name}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip
                contentStyle={tooltipStyle}
                itemStyle={tooltipItemStyle}
                labelStyle={tooltipLabelStyle}
                formatter={(value, name, item) => [
                  `${formatPrice(String(value ?? 0))} · ${item.payload.count} órdenes`,
                  String(name),
                ]}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export function DashboardBreakdown({
  openByStatus,
  fulfillmentMix,
  paymentMix,
}: {
  openByStatus: OpenByStatus;
  fulfillmentMix: MixSlice[];
  paymentMix: MixSlice[];
}) {
  const openRows = OPEN_LABELS.map((item) => ({
    name: item.label,
    value: openByStatus[item.key],
  }));
  const openTotal = openRows.reduce((sum, row) => sum + row.value, 0);

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      <Card>
        <CardTitle>Órdenes abiertas</CardTitle>
        {openTotal === 0 ? (
          <p className="mt-4 text-sm text-muted">No hay órdenes en curso.</p>
        ) : (
          <div className="mt-4 h-44">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={openRows} layout="vertical" margin={{ left: 8 }}>
                <CartesianGrid stroke={CHART_GRID} horizontal={false} />
                <XAxis type="number" allowDecimals={false} hide />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={120}
                  tick={tickStyle}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={tooltipStyle}
                  itemStyle={tooltipItemStyle}
                  labelStyle={tooltipLabelStyle}
                />
                <Bar dataKey="value" fill="#10B981" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card>
      <Card>
        <CardTitle>Composición de ventas</CardTitle>
        <div className="mt-2 flex flex-col gap-4 sm:flex-row">
          <MixPie
            title="Envío vs retiro"
            items={fulfillmentMix}
            labels={FULFILLMENT}
          />
          <MixPie title="Medio de pago" items={paymentMix} labels={PAYMENT} />
        </div>
      </Card>
    </div>
  );
}
