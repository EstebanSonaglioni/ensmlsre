import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axios, { AxiosError } from "axios";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Home from "@/app/page";
import type { Session } from "@/lib/use-session";

const { login, setSession } = vi.hoisted(() => ({
  login: vi.fn(),
  setSession: vi.fn(),
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return { ...actual, login };
});

vi.mock("@/lib/use-session", () => ({
  useSession: () => ({
    session: null as Session | null,
    setSession,
    ready: true,
  }),
}));

describe("Home login", () => {
  beforeEach(() => {
    login.mockReset();
    setSession.mockReset();
  });

  it("envía email y contraseña y guarda la sesión", async () => {
    const user = userEvent.setup();
    login.mockResolvedValue({
      email: "boss@mail.com",
      role: "user",
      access_token: "token",
      csrf_token: "csrf",
      balance: "0.00",
      display_name: "Boss",
      has_avatar: false,
    });

    render(<Home />);

    await user.type(screen.getByLabelText("Email"), "boss@mail.com");
    await user.type(screen.getByLabelText("Contraseña"), "mlsre-demo");
    await user.click(screen.getByRole("button", { name: "Entrar" }));

    expect(login).toHaveBeenCalledWith("boss@mail.com", "mlsre-demo");
    expect(setSession).toHaveBeenCalledWith({
      email: "boss@mail.com",
      role: "user",
      balance: "0.00",
      display_name: "Boss",
      has_avatar: false,
    });
  });

  it("muestra el detail si el login falla", async () => {
    const user = userEvent.setup();
    const error = new AxiosError("fail");
    error.response = {
      data: { detail: "Credenciales inválidas" },
      status: 401,
      statusText: "Unauthorized",
      headers: {},
      config: { headers: new axios.AxiosHeaders() },
    };
    login.mockRejectedValue(error);

    render(<Home />);

    await user.type(screen.getByLabelText("Email"), "x@mail.com");
    await user.type(screen.getByLabelText("Contraseña"), "mala");
    await user.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByText("Credenciales inválidas")).toBeInTheDocument();
    expect(setSession).not.toHaveBeenCalled();
  });
});
