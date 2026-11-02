"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Toast } from "@/components/ui/toast";
import { formatPrice } from "@/lib/utils";
import {
  answerProductQuestion,
  askProductQuestion,
  deleteProduct,
  getErrorDetail,
  getProduct,
  pauseProduct,
  resumeProduct,
  updateProduct,
  type ProductDetail,
  type ProductItem,
} from "@/lib/api";
import { useRealtime } from "@/lib/realtime";

import { ProductBuy } from "./product-buy";
import { ProductImage } from "./product-image";

function mergeItem(
  current: ProductDetail,
  updated: ProductItem,
): ProductDetail {
  return { ...current, ...updated, can_manage: current.can_manage };
}

export function ProductAdmin({ productId }: { productId: number }) {
  const router = useRouter();
  const { watchProduct, unwatchProduct, onProductQuestion } = useRealtime();
  const [detail, setDetail] = useState<ProductDetail | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [question, setQuestion] = useState("");
  const [answerDrafts, setAnswerDrafts] = useState<Record<number, string>>({});
  const [name, setName] = useState("");
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");
  const [netProfit, setNetProfit] = useState("");
  const [category, setCategory] = useState("");
  const [subcategory, setSubcategory] = useState("");
  const [ships, setShips] = useState(true);
  const [pickup, setPickup] = useState(true);
  const [image, setImage] = useState<File | null>(null);
  const [imageKey, setImageKey] = useState(0);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [toast, setToast] = useState("");
  const dismissToast = useCallback(() => setToast(""), []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    getProduct(productId)
      .then((product) => {
        if (cancelled) {
          return;
        }
        setDetail(product);
        setName(product.name);
        setQuantity(String(product.quantity));
        setPrice(product.price);
        setNetProfit(product.net_profit || "0");
        setCategory(product.category);
        setSubcategory(product.subcategory);
        setShips(product.ships);
        setPickup(product.pickup);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(getErrorDetail(err));
          setDetail(null);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [productId]);

  useEffect(() => {
    watchProduct(productId);
    const offQuestion = onProductQuestion(productId, (incoming) => {
      setDetail((current) => {
        if (!current) {
          return current;
        }
        const exists = current.questions.some((item) => item.id === incoming.id);
        return {
          ...current,
          questions: exists
            ? current.questions.map((item) =>
                item.id === incoming.id ? incoming : item,
              )
            : [...current.questions, incoming],
        };
      });
    });
    return () => {
      unwatchProduct(productId);
      offQuestion();
    };
  }, [productId, watchProduct, unwatchProduct, onProductQuestion]);

  const questions = useMemo(() => {
    if (!detail) {
      return [];
    }
    return [...detail.questions].sort((left, right) => {
      if (Boolean(left.answer) === Boolean(right.answer)) {
        return left.id - right.id;
      }
      return left.answer ? 1 : -1;
    });
  }, [detail]);

  async function togglePause() {
    if (!detail) {
      return;
    }
    setError("");
    try {
      const updated = detail.paused
        ? await resumeProduct(detail.id)
        : await pauseProduct(detail.id);
      setDetail((current) =>
        current ? mergeItem(current, updated) : current,
      );
    } catch (err) {
      setError(getErrorDetail(err));
    }
  }

  async function onSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail) {
      return;
    }
    setError("");
    try {
      const updated = await updateProduct(detail.id, {
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
      setImage(null);
      setImageKey((value) => value + 1);
      setDetail((current) =>
        current ? mergeItem(current, updated) : current,
      );
      setToast("Se guardaron los cambios");
    } catch (err) {
      setError(getErrorDetail(err));
    }
  }

  async function onDelete() {
    if (!detail) {
      return;
    }
    setError("");
    try {
      await deleteProduct(detail.id);
      router.push("/productos");
    } catch (err) {
      setError(getErrorDetail(err));
      setConfirmDelete(false);
    }
  }

  async function onAsk(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail) {
      return;
    }
    setError("");
    try {
      const created = await askProductQuestion(detail.id, question);
      setQuestion("");
      setDetail((current) =>
        current
          ? { ...current, questions: [...current.questions, created] }
          : current,
      );
    } catch (err) {
      setError(getErrorDetail(err));
    }
  }

  async function onAnswer(questionId: number) {
    setError("");
    const text = answerDrafts[questionId] ?? "";
    try {
      const updated = await answerProductQuestion(questionId, text);
      setDetail((current) =>
        current
          ? {
              ...current,
              questions: current.questions.map((item) =>
                item.id === updated.id ? updated : item,
              ),
            }
          : current,
      );
    } catch (err) {
      setError(getErrorDetail(err));
    }
  }

  if (loading) {
    return (
      <Card className="xl:col-span-2">
        <p className="text-sm text-muted">Cargando...</p>
      </Card>
    );
  }

  if (!detail) {
    return (
      <Card className="xl:col-span-2">
        <p className="text-sm text-destructive">
          {error || "No se pudo completar la solicitud"}
        </p>
        <Link href="/" className="mt-4 inline-block text-sm text-primary">
          Volver a la tienda
        </Link>
      </Card>
    );
  }

  const canManage = detail.can_manage;

  return (
    <>
      <Card className="flex flex-col gap-4 xl:col-span-2">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <Link
              href={canManage ? "/productos" : "/"}
              className="text-sm text-primary"
            >
              {canManage ? "Volver a productos" : "Volver a la tienda"}
            </Link>
            <CardTitle className="mt-2">{detail.name}</CardTitle>
            <p className="mt-1 font-medium tabular-nums text-accent">
              {formatPrice(detail.price)}
            </p>
            <p className="mt-1 text-[13px] text-muted">
              {detail.store_name}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={detail.paused ? "warning" : "default"}>
              {detail.paused ? "Pausado" : "Activa"}
            </Badge>
            {canManage ? (
              <>
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={togglePause}
                >
                  {detail.paused ? "Reanudar" : "Pausar"}
                </Button>
                {confirmDelete ? (
                  <>
                    <Button
                      type="button"
                      variant="destructive"
                      size="sm"
                      onClick={() => void onDelete()}
                    >
                      Confirmar eliminar
                    </Button>
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      onClick={() => setConfirmDelete(false)}
                    >
                      Cancelar
                    </Button>
                  </>
                ) : (
                  <Button
                    type="button"
                    variant="destructive"
                    size="sm"
                    onClick={() => setConfirmDelete(true)}
                  >
                    Eliminar
                  </Button>
                )}
              </>
            ) : null}
          </div>
        </div>
        <ProductImage
          productId={detail.id}
          alt={detail.name}
          refreshKey={imageKey}
          variant="detail"
        />
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        {canManage ? (
          <form className="flex flex-col gap-4" onSubmit={onSave}>
            <CardTitle>Editar publicación</CardTitle>
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
                onChange={(event) => setImage(event.target.files?.[0] ?? null)}
              />
            </Label>
            <Button type="submit">Guardar cambios</Button>
          </form>
        ) : (
          <>
            <p className="font-medium tabular-nums text-accent">
              {formatPrice(detail.price)}
            </p>
            <p className="text-[13px] text-muted">
              {detail.category} / {detail.subcategory} · cantidad {detail.quantity}
            </p>
          </>
        )}
      </Card>
      {!canManage ? (
        <ProductBuy
          product={detail}
          onAdded={() => setToast("Agregado al carrito")}
          onBought={() => {
            setToast("Compra confirmada");
            getProduct(productId)
              .then(setDetail)
              .catch((err) => setError(getErrorDetail(err)));
          }}
        />
      ) : null}
      <Card className="xl:col-span-2">
        <CardTitle>Preguntas</CardTitle>
        <ul className="mt-4 flex flex-col gap-3">
          {questions.length === 0 ? (
            <li className="text-sm text-muted">Todavía no hay preguntas.</li>
          ) : null}
          {questions.map((item) => (
            <li key={item.id} className="rounded-md bg-card-hover p-3 text-sm">
              {!item.answer ? (
                <p className="mb-2 text-[12px] text-warning">Pendiente</p>
              ) : null}
              <p>
                <span className="text-muted">
                  {item.asker_email || item.asker_label}:{" "}
                </span>
                {item.text}
              </p>
              {item.answer ? (
                <p className="mt-2">
                  <span className="text-primary">Respuesta: </span>
                  {item.answer}
                </p>
              ) : canManage ? (
                <form
                  className="mt-2 flex flex-col gap-2 sm:flex-row"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void onAnswer(item.id);
                  }}
                >
                  <Label className="flex-1">
                    Responder
                    <Input
                      value={answerDrafts[item.id] ?? ""}
                      onChange={(event) =>
                        setAnswerDrafts((current) => ({
                          ...current,
                          [item.id]: event.target.value,
                        }))
                      }
                    />
                  </Label>
                  <Button type="submit" size="sm">
                    Responder
                  </Button>
                </form>
              ) : (
                <p className="mt-2 text-[13px] text-muted">
                  Sin respuesta todavía.
                </p>
              )}
            </li>
          ))}
        </ul>
        {!canManage ? (
          <form className="mt-4 flex flex-col gap-2" onSubmit={onAsk}>
            <Label>
              Preguntar
              <Input
                name="question"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
              />
            </Label>
            <Button type="submit" variant="secondary">
              Enviar pregunta
            </Button>
          </form>
        ) : null}
      </Card>
      {toast ? <Toast message={toast} onDismiss={dismissToast} /> : null}
    </>
  );
}
