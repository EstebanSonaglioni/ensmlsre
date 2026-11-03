import { describe, expect, it } from "vitest";

import {
  formatEta,
  statusBadgeVariant,
  statusLabel,
} from "@/app/order-status";

describe("statusLabel", () => {
  it("traduce cada estado de venta", () => {
    expect(statusLabel("en_carrito")).toBe("En carrito");
    expect(statusLabel("en_curso")).toBe("En curso");
    expect(statusLabel("completada")).toBe("Completada");
    expect(statusLabel("cancelada")).toBe("Cancelada");
  });
});

describe("statusBadgeVariant", () => {
  it("usa acento para completada y destructive para cancelada", () => {
    expect(statusBadgeVariant("completada")).toBe("accent");
    expect(statusBadgeVariant("cancelada")).toBe("destructive");
    expect(statusBadgeVariant("reembolsada")).toBe("destructive");
  });

  it("usa warning para estados abiertos e info para en viaje", () => {
    expect(statusBadgeVariant("en_curso")).toBe("warning");
    expect(statusBadgeVariant("esperando_retiro")).toBe("warning");
    expect(statusBadgeVariant("en_viaje")).toBe("info");
    expect(statusBadgeVariant("en_carrito")).toBe("default");
  });
});

describe("formatEta", () => {
  it("devuelve el original si el ISO no es válido", () => {
    expect(formatEta("ayer")).toBe("ayer");
  });
});
