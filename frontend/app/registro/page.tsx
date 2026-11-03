"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { AuthScreen } from "@/components/auth-screen";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getErrorDetail, register } from "@/lib/api";
import { useSession } from "@/lib/use-session";

export default function RegisterPage() {
  const { session, setSession, ready } = useSession();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (ready && session) {
      router.replace("/");
    }
  }, [ready, session, router]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    try {
      const result = await register(email, password);
      setSession({
        email: result.email,
        role: result.role,
        balance: result.balance,
        display_name: result.display_name,
        has_avatar: result.has_avatar,
      });
      router.replace("/");
    } catch (err) {
      setError(getErrorDetail(err));
    }
  }

  if (!ready || session) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background text-muted">
        Cargando...
      </main>
    );
  }

  return (
    <AuthScreen
      title="Registro"
      description="Creá tu cuenta para entrar a la tienda."
      submitLabel="Registrarme"
      error={error}
      onSubmit={onSubmit}
      footerHref="/"
      footerLabel="Ya tengo cuenta"
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
