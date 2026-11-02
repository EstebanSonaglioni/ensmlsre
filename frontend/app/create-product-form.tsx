"use client";

import { FormEvent, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { NativeSelect } from "@/components/ui/native-select";
import {
  createProduct,
  getErrorDetail,
  listStores,
  type StoreItem,
} from "@/lib/api";

export function CreateProductForm({
  refreshKey,
  onCreated,
}: {
  refreshKey: number;
  onCreated?: () => void;
}) {
  const [stores, setStores] = useState<StoreItem[]>([]);
  const [storeId, setStoreId] = useState("");
  const [name, setName] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [price, setPrice] = useState("");
  const [netProfit, setNetProfit] = useState("");
  const [category, setCategory] = useState("");
  const [subcategory, setSubcategory] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [ships, setShips] = useState(true);
  const [pickup, setPickup] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    listStores({ page: 1, page_size: 100 })
      .then((result) => {
        if (cancelled) {
          return;
        }
        setStores(result.items);
        setStoreId((current) =>
          result.items.some((item) => String(item.id) === current)
            ? current
            : String(result.items[0]?.id ?? ""),
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
    if (!image || !storeId) {
      setError("No se pudo completar la solicitud");
      return;
    }
    try {
      await createProduct(Number(storeId), {
        name,
        quantity,
        price,
        net_profit: netProfit,
        category,
        subcategory,
        ships,
        pickup,
        image,
      });
      setName("");
      setQuantity("1");
      setPrice("");
      setNetProfit("");
      setCategory("");
      setSubcategory("");
      setImage(null);
      onCreated?.();
    } catch (err) {
      setError(getErrorDetail(err));
    }
  }

  return (
    <Card>
      <form className="flex flex-col gap-4" onSubmit={onSubmit}>
        <CardTitle>Publicar producto</CardTitle>
        <Label>
          Tienda
          <NativeSelect
            name="store_id"
            value={storeId}
            onChange={(event) => setStoreId(event.target.value)}
          >
            {stores.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </NativeSelect>
        </Label>
        <Label>
          Nombre
          <Input
            name="name"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </Label>
        <Label>
          Cantidad
          <Input
            type="number"
            min={0}
            name="quantity"
            value={quantity}
            onChange={(event) => setQuantity(event.target.value)}
          />
        </Label>
        <Label>
          Precio
          <Input
            name="price"
            value={price}
            onChange={(event) => setPrice(event.target.value)}
          />
        </Label>
        <Label>
          Ganancia neta (por unidad)
          <Input
            name="net_profit"
            value={netProfit}
            onChange={(event) => setNetProfit(event.target.value)}
          />
        </Label>
        <Label>
          Categoría
          <Input
            name="category"
            value={category}
            onChange={(event) => setCategory(event.target.value)}
          />
        </Label>
        <Label>
          Subcategoría
          <Input
            name="subcategory"
            value={subcategory}
            onChange={(event) => setSubcategory(event.target.value)}
          />
        </Label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={ships}
            onChange={(event) => setShips(event.target.checked)}
          />
          Envío
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={pickup}
            onChange={(event) => setPickup(event.target.checked)}
          />
          Retiro
        </label>
        <Label>
          Imagen
          <Input
            type="file"
            name="image"
            accept="image/png,image/jpeg,image/gif"
            required
            onChange={(event) => setImage(event.target.files?.[0] ?? null)}
          />
        </Label>
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        <Button type="submit">Publicar</Button>
      </form>
    </Card>
  );
}
