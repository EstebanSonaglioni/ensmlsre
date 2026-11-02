"use client";

import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createStore, getErrorDetail } from "@/lib/api";

export function CreateStoreForm({ onCreated }: { onCreated?: () => void }) {
  const [name, setName] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    try {
      await createStore(name);
      setName("");
      onCreated?.();
    } catch (err) {
      setError(getErrorDetail(err));
    }
  }

  return (
    <Card>
      <form className="flex flex-col gap-4" onSubmit={onSubmit}>
        <CardTitle>Crear tienda</CardTitle>
        <Label>
          Nombre
          <Input
            type="text"
            name="name"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </Label>
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        <Button type="submit">Crear tienda</Button>
      </form>
    </Card>
  );
}
