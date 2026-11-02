"use client";

import { AuthGate } from "@/components/auth-gate";

import { SellerDashboard } from "../seller-dashboard";

export default function DashboardPage() {
  return (
    <AuthGate sellerOnly>
      {() => <SellerDashboard />}
    </AuthGate>
  );
}
