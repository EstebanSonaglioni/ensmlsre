"use client";

import { FormEvent, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  fetchProfileImage,
  getErrorDetail,
  updateProfile,
} from "@/lib/api";
import type { Session } from "@/lib/use-session";

import { CreateStoreForm } from "./create-store-form";
import { InvitationList } from "./invitation-list";

export function UserProfile({
  session,
  seller,
  onUpdated,
  onBecameSeller,
}: {
  session: Session;
  seller: boolean;
  onUpdated: (session: Session) => void;
  onBecameSeller: () => void;
}) {
  const [name, setName] = useState(session.display_name);
  const [image, setImage] = useState<File | null>(null);
  const [preview, setPreview] = useState("");
  const [avatarKey, setAvatarKey] = useState(0);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");

  useEffect(() => {
    let cancelled = false;
    let objectUrl = "";
    if (!session.has_avatar) {
      setPreview("");
      return;
    }
    fetchProfileImage()
      .then((url) => {
        objectUrl = url;
        if (!cancelled) {
          setPreview(url);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setPreview("");
        }
      });
    return () => {
      cancelled = true;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [session.has_avatar, avatarKey]);

  async function onSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSaved("");
    try {
      const result = await updateProfile({
        display_name: name,
        image,
      });
      setImage(null);
      setAvatarKey((value) => value + 1);
      onUpdated({
        email: result.email,
        role: result.role,
        balance: result.balance,
        display_name: result.display_name,
        has_avatar: result.has_avatar,
      });
      setSaved("Se guardaron los cambios");
    } catch (err) {
      setError(getErrorDetail(err));
    }
  }

  return (
    <div className="flex flex-col gap-6 xl:col-span-2">
      <Card>
        <form className="flex flex-col gap-4" onSubmit={onSave}>
          <CardTitle>Perfil</CardTitle>
          {preview ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={preview}
              alt=""
              className="size-24 rounded-full object-cover"
            />
          ) : (
            <div className="flex size-24 items-center justify-center rounded-full bg-card-hover text-[13px] text-muted">
              Sin foto
            </div>
          )}
          <Label>
            Nombre
            <Input
              name="display_name"
              value={name}
              maxLength={80}
              onChange={(event) => setName(event.target.value)}
            />
          </Label>
          <Label>
            Foto de perfil
            <Input
              type="file"
              name="image"
              accept="image/png,image/jpeg,image/gif"
              onChange={(event) => setImage(event.target.files?.[0] ?? null)}
            />
          </Label>
          {error ? <p className="text-sm text-destructive">{error}</p> : null}
          {saved ? <p className="text-sm text-accent">{saved}</p> : null}
          <Button type="submit">Guardar</Button>
        </form>
      </Card>
      {!seller ? (
        <>
          <Card>
            <CardTitle>Ser vendedor</CardTitle>
            <p className="mt-2 text-sm text-muted">
              Unite a una tienda con una invitación o creá la tuya.
            </p>
          </Card>
          <InvitationList onAccepted={onBecameSeller} />
          <CreateStoreForm onCreated={onBecameSeller} />
        </>
      ) : (
        <p className="text-sm text-muted">
          Ya vendés en una tienda. La administración está en Tienda.
        </p>
      )}
    </div>
  );
}
