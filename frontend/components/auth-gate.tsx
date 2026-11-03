"use client";

import { useRouter } from "next/navigation";
import { type ReactNode, useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { listStores, logout } from "@/lib/api";
import { RealtimeProvider, useRealtime } from "@/lib/realtime";
import { useSession, type Session } from "@/lib/use-session";

export type SellerContext = {
  seller: boolean;
  reloadSeller: () => void;
  setSession: (session: Session | null) => void;
};

export function AuthGate({
  children,
  sellerOnly = false,
}: {
  children: (session: Session, ctx: SellerContext) => ReactNode;
  sellerOnly?: boolean;
}) {
  const { session, setSession, ready } = useSession();
  const router = useRouter();
  const [seller, setSeller] = useState<boolean | null>(null);

  const reloadSeller = useCallback(() => {
    listStores({ page: 1, page_size: 1 })
      .then((result) => setSeller(result.total > 0))
      .catch(() => setSeller(false));
  }, []);

  useEffect(() => {
    if (ready && !session) {
      router.replace("/");
    }
  }, [ready, session, router]);

  useEffect(() => {
    if (session) {
      reloadSeller();
    }
  }, [session, reloadSeller]);

  useEffect(() => {
    if (sellerOnly && seller === false) {
      router.replace("/");
    }
  }, [sellerOnly, seller, router]);

  if (!ready || !session || seller === null || (sellerOnly && !seller)) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background text-muted">
        Cargando...
      </main>
    );
  }

  return (
    <RealtimeProvider>
      <UnlockedShell
        email={session.email}
        displayName={session.display_name}
        hasAvatar={session.has_avatar}
        role={session.role}
        seller={seller}
        onLogout={async () => {
          await logout();
          setSession(null);
          router.replace("/");
        }}
      >
        {children(session, { seller, reloadSeller, setSession })}
      </UnlockedShell>
    </RealtimeProvider>
  );
}

function UnlockedShell({
  email,
  displayName,
  hasAvatar,
  role,
  seller,
  onLogout,
  children,
}: {
  email: string;
  displayName: string;
  hasAvatar: boolean;
  role: string;
  seller: boolean;
  onLogout: () => void;
  children: ReactNode;
}) {
  const { unlockAudio } = useRealtime();
  return (
    <div onPointerDown={unlockAudio} onKeyDown={unlockAudio}>
      <AppShell
        email={email}
        displayName={displayName}
        hasAvatar={hasAvatar}
        role={role}
        seller={seller}
        onLogout={onLogout}
      >
        {children}
      </AppShell>
    </div>
  );
}
