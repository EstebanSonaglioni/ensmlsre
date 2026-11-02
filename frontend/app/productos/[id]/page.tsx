"use client";

import { useParams } from "next/navigation";

import { AuthGate } from "@/components/auth-gate";
import { Card } from "@/components/ui/card";

import { ProductAdmin } from "../../product-admin";

export default function ProductoPage() {
  const params = useParams<{ id: string }>();
  const productId = Number(params.id);

  if (!Number.isInteger(productId) || productId < 1) {
    return (
      <AuthGate>
        {() => (
          <Card className="xl:col-span-2">
            <p className="text-sm text-destructive">
              No se pudo completar la solicitud
            </p>
          </Card>
        )}
      </AuthGate>
    );
  }

  return (
    <AuthGate>
      {() => <ProductAdmin productId={productId} />}
    </AuthGate>
  );
}
