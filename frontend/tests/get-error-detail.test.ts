import axios, { AxiosError } from "axios";
import { describe, expect, it } from "vitest";

import { getErrorDetail } from "@/lib/api";

describe("getErrorDetail", () => {
  it("muestra el detail del backend cuando viene como string", () => {
    const error = new AxiosError("fail");
    error.response = {
      data: { detail: "Credenciales inválidas" },
      status: 401,
      statusText: "Unauthorized",
      headers: {},
      config: { headers: new axios.AxiosHeaders() },
    };
    expect(getErrorDetail(error)).toBe("Credenciales inválidas");
  });

  it("usa el mensaje genérico si no hay detail", () => {
    expect(getErrorDetail(new Error("boom"))).toBe(
      "No se pudo completar la solicitud",
    );
  });

  it("no expone el body si detail no es string", () => {
    const error = new AxiosError("fail");
    error.response = {
      data: { detail: [{ loc: ["email"], msg: "invalid" }] },
      status: 422,
      statusText: "Unprocessable Entity",
      headers: {},
      config: { headers: new axios.AxiosHeaders() },
    };
    expect(getErrorDetail(error)).toBe("No se pudo completar la solicitud");
  });
});
