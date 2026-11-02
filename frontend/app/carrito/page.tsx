"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { AuthGate } from "@/components/auth-gate";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { NativeSelect } from "@/components/ui/native-select";
import { Toast } from "@/components/ui/toast";
import {
  checkoutSells,
  getErrorDetail,
  listSells,
  patchSell,
  transitionSell,
  type PaymentMethod,
  type SellItem,
} from "@/lib/api";
import { formatPrice } from "@/lib/utils";

function CartBody() {
  const [items, setItems] = useState<SellItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [payment, setPayment] = useState<PaymentMethod>("tarjeta");
  const [toast, setToast] = useState("");

  function load() {
    setLoading(true);
    listSells({ status: "en_carrito", page_size: 100 })
      .then((result) => setItems(result.items))
      .catch((err) => {
        setError(getErrorDetail(err));
        setItems([]);
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, []);

  const total = useMemo(
    () =>
      items
        .reduce((sum, item) => sum + Number(item.subtotal), 0)
        .toFixed(2),
    [items],
  );

  async function onQty(id: number, quantity: number) {
    setError("");
    try {
      const updated = await patchSell(id, { quantity });
      setItems((current) =>
        current.map((item) => (item.id === id ? updated : item)),
      );
    } catch (err) {
      setError(getErrorDetail(err));
    }
  }

  async function onRemove(id: number) {
    setError("");
    try {
      await transitionSell(id, "cancelada");
      setItems((current) => current.filter((item) => item.id !== id));
    } catch (err) {
      setError(getErrorDetail(err));
    }
  }

  async function onCheckout(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    try {
      await checkoutSells({
        payment_method: payment,
        sell_ids: items.map((item) => item.id),
      });
      setItems([]);
      setToast("Compra confirmada");
    } catch (err) {
      setError(getErrorDetail(err));
    }
  }

  return (
    <Card className="xl:col-span-2">
      <form className="flex flex-col gap-4" onSubmit={onCheckout}>
        <CardTitle>Carrito</CardTitle>
        {loading ? <p className="text-sm text-muted">Cargando...</p> : null}
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        {!loading && items.length === 0 ? (
          <p className="text-sm text-muted">Tu carrito está vacío.</p>
        ) : null}
        <ul className="flex flex-col gap-4">
          {items.map((item) => (
            <li
              key={item.id}
              className="flex flex-col gap-2 rounded-md border border-border p-4"
            >
              <p className="font-medium">{item.product_name}</p>
              <p className="text-[13px] text-muted">{item.store_name}</p>
              <Label>
                Cantidad
                <Input
                  type="number"
                  min={1}
                  value={item.quantity}
                  onChange={(event) =>
                    void onQty(item.id, Number(event.target.value))
                  }
                />
              </Label>
              <p className="text-[13px] text-muted">
                {item.fulfillment === "envio" ? "Envío" : "Retiro"}
              </p>
              <p className="tabular-nums text-accent">
                {formatPrice(item.subtotal)}
              </p>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => void onRemove(item.id)}
              >
                Quitar
              </Button>
            </li>
          ))}
        </ul>
        {items.length > 0 ? (
          <>
            <p className="font-medium tabular-nums text-accent">
              Total {formatPrice(total)}
            </p>
            <Label>
              Medio de pago
              <NativeSelect
                value={payment}
                onChange={(event) =>
                  setPayment(event.target.value as PaymentMethod)
                }
              >
                <option value="tarjeta">Tarjeta</option>
                <option value="transferencia">Transferencia</option>
                <option value="efectivo">Efectivo</option>
              </NativeSelect>
            </Label>
            <Button type="submit">Confirmar compra</Button>
          </>
        ) : null}
      </form>
      {toast ? <Toast message={toast} onDismiss={() => setToast("")} /> : null}
    </Card>
  );
}

export default function CarritoPage() {
  return (
    <AuthGate>
      {() => <CartBody />}
    </AuthGate>
  );
}
