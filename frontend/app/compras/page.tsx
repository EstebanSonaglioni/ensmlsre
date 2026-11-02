"use client";

import { AuthGate } from "@/components/auth-gate";

import { OrderList } from "../order-list";

export default function ComprasPage() {
  return (
    <AuthGate>
      {() => <OrderList asSeller={false} />}
    </AuthGate>
  );
}
