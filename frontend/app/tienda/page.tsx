"use client";

import { useState } from "react";

import { AuthGate } from "@/components/auth-gate";
import { formatPrice } from "@/lib/utils";

import { CreateStoreForm } from "../create-store-form";
import { InviteSellerForm } from "../invite-seller-form";
import { StoreList } from "../store-list";

export default function TiendaPage() {
  const [listVersion, setListVersion] = useState(0);

  return (
    <AuthGate sellerOnly>
      {(session) => (
        <>
          <p className="text-sm text-muted xl:col-span-2">
            Saldo {formatPrice(session.balance ?? "0")}
          </p>
          <StoreList refreshKey={listVersion} />
          <InviteSellerForm refreshKey={listVersion} />
          <CreateStoreForm
            onCreated={() => setListVersion((value) => value + 1)}
          />
        </>
      )}
    </AuthGate>
  );
}
