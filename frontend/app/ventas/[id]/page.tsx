"use client";

import { useParams } from "next/navigation";

import { AuthGate } from "@/components/auth-gate";
import { Card } from "@/components/ui/card";

import { OrderDetail } from "../../order-detail";

export default function VentaPage() {
  const params = useParams<{ id: string }>();
  const sellId = Number(params.id);

  if (!Number.isInteger(sellId) || sellId < 1) {
    return (
      <AuthGate sellerOnly>
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
    <AuthGate sellerOnly>
      {() => <OrderDetail sellId={sellId} asSeller />}
    </AuthGate>
  );
}
