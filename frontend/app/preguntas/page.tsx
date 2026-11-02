"use client";

import { AuthGate } from "@/components/auth-gate";

import { SellerQuestions } from "../seller-questions";

export default function PreguntasPage() {
  return (
    <AuthGate sellerOnly>
      {() => <SellerQuestions />}
    </AuthGate>
  );
}
