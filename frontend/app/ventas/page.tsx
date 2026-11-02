"use client";

import { AuthGate } from "@/components/auth-gate";

import { OrderList } from "../order-list";

export default function VentasPage() {
  return (
    <AuthGate sellerOnly>
      {() => <OrderList asSeller />}
    </AuthGate>
  );
}
