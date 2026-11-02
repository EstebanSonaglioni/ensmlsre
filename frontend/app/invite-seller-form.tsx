"use client";

import { FormEvent, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { NativeSelect } from "@/components/ui/native-select";
import {
  createInvitation,
  getErrorDetail,
  listStores,
  type StoreItem,
} from "@/lib/api";

type InviteSellerFormProps = {
  refreshKey: number;
};

export function InviteSellerForm({ refreshKey }: InviteSellerFormProps) {
  const [stores, setStores] = useState<StoreItem[]>([]);
  const [store, setStore] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState("");

  useEffect(() => {
    let cancelled = false;
    listStores({ page: 1, page_size: 100 })
      .then((result) => {
        if (cancelled) {
          return;
        }
        const adminStores = result.items.filter((item) => item.role === "admin");
        setStores(adminStores);
        setStore((current) =>
          adminStores.some((item) => item.name === current)
            ? current
            : (adminStores[0]?.name ?? ""),
        );
      })
      .catch(() => {
        if (!cancelled) {
          setStores([]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  if (stores.length === 0) {
    return null;
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setDone("");
    try {
      await createInvitation(email, store);
      setEmail("");
      setDone("Invitación creada.");
    } catch (err) {
      setError(getErrorDetail(err));
    }
  }

  return (
    <Card>
      <form className="flex flex-col gap-4" onSubmit={onSubmit}>
        <CardTitle>Invitar a una tienda</CardTitle>
        <Label>
          Tienda
          <NativeSelect
            name="store"
            value={store}
            onChange={(event) => setStore(event.target.value)}
          >
            {stores.map((item) => (
              <option key={item.name} value={item.name}>
                {item.name}
              </option>
            ))}
          </NativeSelect>
        </Label>
        <Label>
          Email
          <Input
            type="text"
            name="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </Label>
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        {done ? <p className="text-sm text-accent">{done}</p> : null}
        <Button type="submit">Invitar</Button>
      </form>
    </Card>
  );
}
