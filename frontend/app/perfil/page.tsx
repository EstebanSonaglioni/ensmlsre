"use client";

import { AuthGate } from "@/components/auth-gate";

import { UserProfile } from "../user-profile";

export default function PerfilPage() {
  return (
    <AuthGate>
      {(session, { seller, reloadSeller, setSession }) => (
        <UserProfile
          session={session}
          seller={seller}
          onUpdated={(next) => setSession(next)}
          onBecameSeller={() => {
            reloadSeller();
            setSession({ ...session, role: "vendedor" });
          }}
        />
      )}
    </AuthGate>
  );
}
