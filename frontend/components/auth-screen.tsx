import Link from "next/link";
import type { FormEvent, ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";

type AuthScreenProps = {
  title: string;
  description: string;
  submitLabel: string;
  error: string;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  children: ReactNode;
  footerHref: string;
  footerLabel: string;
};

export function AuthScreen({
  title,
  description,
  submitLabel,
  error,
  onSubmit,
  children,
  footerHref,
  footerLabel,
}: AuthScreenProps) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-6">
      <Card className="w-full max-w-md">
        <CardTitle className="text-[26px]">{title}</CardTitle>
        <CardDescription className="mt-2">{description}</CardDescription>
        <form className="mt-6 flex flex-col gap-4" onSubmit={onSubmit}>
          {children}
          {error ? (
            <p className="text-sm text-destructive">{error}</p>
          ) : null}
          <Button type="submit">{submitLabel}</Button>
        </form>
        <Link
          href={footerHref}
          className="mt-4 inline-block text-sm text-primary hover:text-primary-muted"
        >
          {footerLabel}
        </Link>
      </Card>
    </main>
  );
}
