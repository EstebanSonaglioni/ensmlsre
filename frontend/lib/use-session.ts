"use client";

import { useEffect, useState } from "react";

import { restoreSession } from "./api";

export type Session = {
  email: string;
  role: string;
  balance: string;
  display_name: string;
  has_avatar: boolean;
};

export function useSession() {
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    restoreSession()
      .then((result) => {
        if (result) {
          setSession({
            email: result.email,
            role: result.role,
            balance: result.balance,
            display_name: result.display_name,
            has_avatar: result.has_avatar,
          });
        }
      })
      .finally(() => setReady(true));
  }, []);

  return { session, setSession, ready };
}
