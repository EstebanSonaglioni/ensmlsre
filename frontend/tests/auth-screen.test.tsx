import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AuthScreen } from "@/components/auth-screen";

describe("AuthScreen", () => {
  it("muestra título, acción y enlace de pie", () => {
    render(
      <AuthScreen
        title="Iniciar sesión"
        description="Entrá con tu cuenta."
        submitLabel="Entrar"
        error=""
        onSubmit={vi.fn()}
        footerHref="/registro"
        footerLabel="Crear cuenta"
      >
        <input aria-label="Email" />
      </AuthScreen>,
    );

    expect(
      screen.getByRole("heading", { name: "Iniciar sesión" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Entrar" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Crear cuenta" })).toHaveAttribute(
      "href",
      "/registro",
    );
    expect(screen.queryByText(/error/i)).not.toBeInTheDocument();
  });

  it("muestra el error y dispara onSubmit", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn((event: { preventDefault: () => void }) => {
      event.preventDefault();
    });

    render(
      <AuthScreen
        title="Iniciar sesión"
        description="Entrá con tu cuenta."
        submitLabel="Entrar"
        error="Credenciales inválidas"
        onSubmit={onSubmit}
        footerHref="/registro"
        footerLabel="Crear cuenta"
      >
        <input aria-label="Email" />
      </AuthScreen>,
    );

    expect(screen.getByText("Credenciales inválidas")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Entrar" }));
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });
});
