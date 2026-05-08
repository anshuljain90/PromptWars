"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/auth/AuthProvider";
import { signOut } from "@/lib/firebase";

export default function TripsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace("/");
  }, [loading, user, router]);

  if (loading || !user) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground">Loading…</p>
      </main>
    );
  }

  return (
    <>
      <header className="border-b border-border">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-6 py-4">
          <h1 className="text-xl">PromptWars</h1>
          <nav aria-label="Account">
            <Button variant="outline" size="sm" onClick={() => signOut()}>
              Sign out
            </Button>
          </nav>
        </div>
      </header>
      <main id="main-content" className="mx-auto w-full max-w-5xl flex-1 px-6 py-10">
        <h2>Welcome, {user.displayName ?? user.email}</h2>
        <p className="mt-2 text-muted-foreground">
          Trip list lands in Phase 3. Auth is wired end-to-end — backend can verify
          your ID token via <code>GET /me</code>.
        </p>
      </main>
    </>
  );
}
