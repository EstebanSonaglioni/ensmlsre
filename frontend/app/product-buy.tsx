"use client";

import { FormEvent, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { NativeSelect } from "@/components/ui/native-select";
import {
  addToCart,
  checkoutSells,
  getErrorDetail,
  type Fulfillment,
  type PaymentMethod,
  type ProductDetail,
} from "@/lib/api";
import { formatPrice } from "@/lib/utils";

export function ProductBuy({
  product,
  onBought,
  onAdded,
}: {
  product: ProductDetail;
  onBought: () => void;
  onAdded: () => void;
}) {
  const defaultFulfillment: Fulfillment = product.ships ? "envio" : "retiro";
  const [quantity, setQuantity] = useState("1");
  const [fulfillment, setFulfillment] = useState<Fulfillment>(defaultFulfillment);
  const [payment, setPayment] = useState<PaymentMethod>("tarjeta");
  const [error, setError] = useState("");

  const qty = Math.max(1, Number(quantity) || 1);
  const subtotal = useMemo(() => {
    const price = Number(product.price);
    if (Number.isNaN(price)) {
      return product.price;
    }
    return (price * qty).toFixed(2);
  }, [product.price, qty]);

  const soldOut = product.quantity < 1;

  async function onCart() {
    setError("");
    try {
      await addToCart({
        product_id: product.id,
        quantity: qty,
        fulfillment,
      });
      onAdded();
    } catch (err) {
      setError(getErrorDetail(err));
    }
  }

  async function onBuy(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    try {
      await checkoutSells({
        payment_method: payment,
        items: [
          {
            product_id: product.id,
            quantity: qty,
            fulfillment,
          },
        ],
      });
      onBought();
    } catch (err) {
      setError(getErrorDetail(err));
    }
  }

  return (
    <Card>
      <form className="flex flex-col gap-4" onSubmit={onBuy}>
        <CardTitle>Comprar</CardTitle>
        {soldOut ? (
          <p className="text-sm text-muted">Sin stock.</p>
        ) : (
          <>
            <Label>
              Cantidad
              <Input
                type="number"
                min={1}
                max={product.quantity}
                value={quantity}
                onChange={(event) => setQuantity(event.target.value)}
              />
            </Label>
            <p className="text-sm text-muted">
              Disponible: {product.quantity}
            </p>
            <p className="font-medium tabular-nums text-accent">
              Subtotal {formatPrice(subtotal)}
            </p>
            <fieldset className="flex flex-col gap-2 text-sm">
              <legend className="text-muted">Entrega</legend>
              {product.ships ? (
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="fulfillment"
                    checked={fulfillment === "envio"}
                    onChange={() => setFulfillment("envio")}
                  />
                  Envío
                </label>
              ) : null}
              {product.pickup ? (
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="fulfillment"
                    checked={fulfillment === "retiro"}
                    onChange={() => setFulfillment("retiro")}
                  />
                  Retiro
                </label>
              ) : null}
            </fieldset>
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
            {error ? <p className="text-sm text-destructive">{error}</p> : null}
            <div className="flex flex-wrap gap-2">
              <Button type="submit">Comprar ahora</Button>
              <Button type="button" variant="secondary" onClick={() => void onCart()}>
                Añadir al carrito
              </Button>
            </div>
          </>
        )}
      </form>
    </Card>
  );
}
