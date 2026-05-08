"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { LogOut, Plane } from "lucide-react";
import { Button } from "@/components/ui/button";
import { signOut } from "@/lib/firebase";
import { useAuth } from "@/components/auth/AuthProvider";

export function AppHeader() {
  const { user } = useAuth();
  const router = useRouter();

  async function handleSignOut() {
    await signOut();
    router.replace("/");
  }

  return (
    <header className="border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
        <Link
          href="/trips"
          className="flex items-center gap-2 text-lg font-semibold tracking-tight"
          aria-label="PromptWars home"
        >
          <Plane className="size-5 text-primary" aria-hidden="true" />
          PromptWars
        </Link>
        <nav aria-label="Account" className="flex items-center gap-3">
          {user && (
            <span className="hidden text-sm text-muted-foreground sm:inline">
              {user.email}
            </span>
          )}
          <Button variant="outline" size="sm" onClick={handleSignOut}>
            <LogOut className="size-4" aria-hidden="true" />
            Sign out
          </Button>
        </nav>
      </div>
    </header>
  );
}
