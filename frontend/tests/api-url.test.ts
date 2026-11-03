import { afterEach, describe, expect, it, vi } from "vitest";

describe("apiBaseUrl", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("usa /backend si NEXT_PUBLIC_API_URL está vacío", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "");
    const { apiBaseUrl } = await import("@/lib/api-url");
    expect(apiBaseUrl()).toBe("/backend");
  });

  it("quita la barra final de la URL absoluta", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://localhost:8000/");
    const { apiBaseUrl } = await import("@/lib/api-url");
    expect(apiBaseUrl()).toBe("http://localhost:8000");
  });
});

describe("wsUrl", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("convierte http en ws cuando hay URL absoluta", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://localhost:8000");
    const { wsUrl } = await import("@/lib/api-url");
    expect(wsUrl()).toBe("ws://localhost:8000/ws");
  });

  it("arma el websocket relativo al host del browser", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "");
    const { wsUrl } = await import("@/lib/api-url");
    expect(wsUrl()).toBe("ws://localhost:3000/backend/ws");
  });
});
