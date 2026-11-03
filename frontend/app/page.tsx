"use client";

import { FormEvent, useState } from "react";

import { AuthGate } from "@/components/auth-gate";
import { AuthScreen } from "@/components/auth-screen";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getErrorDetail, login } from "@/lib/api";
import { useSession } from "@/lib/use-session";

import { ProductList } from "./product-list";

export default function Home() {
  const { session, setSession, ready } = useSession();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    try {
      const result = await login(email, password);
      setSession({
        email: result.email,
        role: result.role,
        balance: result.balance,
        display_name: result.display_name,
        has_avatar: result.has_avatar,
      });
    } catch (err) {
      setError(getErrorDetail(err));
    }
  }

  if (!ready) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background text-muted">
        Cargando...
      </main>
    );
  }

  if (session) {
    return <AuthGate>{() => <ProductList refreshKey={0} />}</AuthGate>;
  }

  return (
    <AuthScreen
      title="Iniciar sesión"
      description="Entrá con el email y la contraseña de tu cuenta."
      submitLabel="Entrar"
      error={error}
      onSubmit={onSubmit}
      footerHref="/registro"
      footerLabel="Crear cuenta"
    >
      <Label>
        Email
        <Input
          type="email"
          name="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
      </Label>
      <Label>
        Contraseña
        <Input
          type="password"
          name="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
      </Label>
    </AuthScreen>
  );
}
