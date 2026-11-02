"use client";

import {
  LayoutDashboard,
  MessageCircleQuestionMark,
  Package,
  ShoppingBag,
  ShoppingCart,
  Store,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { AccountMenu } from "@/components/account-menu";
import { NotificationBell } from "@/components/notification-bell";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/tienda", label: "Tienda", icon: Store },
  { href: "/productos", label: "Productos", icon: Package },
  { href: "/preguntas", label: "Preguntas", icon: MessageCircleQuestionMark },
  { href: "/ventas", label: "Ventas", icon: ShoppingBag },
] as const;

type AppShellProps = {
  email: string;
  displayName: string;
  hasAvatar: boolean;
  role: string;
  seller: boolean;
  children: ReactNode;
  onLogout: () => void;
};

function NavLinks({ className }: { className?: string }) {
  const pathname = usePathname();

  return (
    <nav className={className}>
      {NAV_ITEMS.map((item) => {
        const active =
          pathname === item.href || pathname.startsWith(`${item.href}/`);
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium",
              active
                ? "bg-primary/15 text-primary"
                : "text-muted hover:bg-card-hover hover:text-foreground",
            )}
          >
            <Icon className="size-4" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

export function AppShell({
  email,
  displayName,
  hasAvatar,
  role,
  seller,
  children,
  onLogout,
}: AppShellProps) {
  return (
    <div className="flex min-h-screen bg-background text-foreground">
      {seller ? (
        <aside className="hidden w-[240px] shrink-0 flex-col border-r border-border bg-sidebar px-4 py-6 md:flex">
          <Link href="/" className="px-2 text-lg font-semibold text-foreground">
            MLSRE
          </Link>
          <p className="mt-1 px-2 text-[12px] text-muted">Panel seller</p>
          <NavLinks className="mt-8 flex flex-col gap-1" />
        </aside>
      ) : null}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex min-h-16 items-center justify-between gap-4 border-b border-border px-6 py-3 md:h-16 md:py-0">
          <div className="min-w-0">
            <Link
              href="/"
              className="text-lg font-semibold md:hidden"
            >
              MLSRE
            </Link>
            <p className="hidden text-lg font-semibold md:block">
              Hola{displayName ? ` ${displayName}` : ""}
            </p>
            <p className="truncate text-[13px] text-muted">
              Estás adentro como {role}.
            </p>
            {seller ? (
              <NavLinks className="mt-2 flex gap-1 md:hidden" />
            ) : null}
          </div>
          <div className="flex min-w-0 items-center gap-3">
            <Link
              href="/compras"
              className="text-sm text-muted hover:text-foreground"
            >
              Compras
            </Link>
            <Link
              href="/carrito"
              className="flex items-center gap-1 text-sm text-muted hover:text-foreground"
            >
              <ShoppingCart className="size-4" />
              Carrito
            </Link>
            <NotificationBell />
            <AccountMenu
              email={email}
              displayName={displayName}
              hasAvatar={hasAvatar}
              onLogout={onLogout}
            />
          </div>
        </header>
        <main className="grid flex-1 grid-cols-1 gap-6 p-6 xl:grid-cols-2">
          {children}
        </main>
      </div>
    </div>
  );
}
