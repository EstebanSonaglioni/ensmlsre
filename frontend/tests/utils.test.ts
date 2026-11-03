import { describe, expect, it } from "vitest";

import { cn, formatDateTime, formatPrice } from "@/lib/utils";

describe("formatPrice", () => {
  it("prefija el monto con $", () => {
    expect(formatPrice("199.90")).toBe("$ 199.90");
  });
});

describe("formatDateTime", () => {
  it("formatea un ISO válido en es-AR", () => {
    const formatted = formatDateTime("2026-03-15T18:30:00.000Z");
    expect(formatted).toMatch(/\d{2}\/\d{2}\/2026/);
    expect(formatted).toMatch(/\d{2}:\d{2}/);
  });

  it("devuelve el string original si la fecha es inválida", () => {
    expect(formatDateTime("no-es-una-fecha")).toBe("no-es-una-fecha");
  });
});

describe("cn", () => {
  it("fusiona clases de Tailwind y descarta las contradictorias", () => {
    expect(cn("p-2", "p-4", "text-sm")).toBe("p-4 text-sm");
  });
});
