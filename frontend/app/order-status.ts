import type { SellStatus } from "@/lib/api";

export function statusLabel(status: SellStatus): string {
  const labels: Record<SellStatus, string> = {
    en_carrito: "En carrito",
    en_curso: "En curso",
    en_viaje: "En viaje",
    esperando_retiro: "Esperando retiro",
    completada: "Completada",
    cancelada: "Cancelada",
    reembolsada: "Reembolsada",
  };
  return labels[status];
}

export function statusBadgeVariant(
  status: SellStatus,
): "default" | "warning" | "info" | "accent" | "destructive" {
  if (status === "en_viaje") {
    return "info";
  }
  if (status === "completada") {
    return "accent";
  }
  if (status === "cancelada" || status === "reembolsada") {
    return "destructive";
  }
  if (status === "en_curso" || status === "esperando_retiro") {
    return "warning";
  }
  return "default";
}

export function formatEta(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }
  return date.toLocaleString("es-AR");
}
