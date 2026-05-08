"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/auth/AuthProvider";
import { signInWithGoogle } from "@/lib/firebase";

export default function LoginPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [signingIn, setSigningIn] = useState(false);

  useEffect(() => {
    if (!loading && user) router.replace("/trips");
  }, [loading, user, router]);

  async function handleSignIn() {
    setError(null);
    setSigningIn(true);
    try {
      await signInWithGoogle();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed");
    } finally {
      setSigningIn(false);
    }
  }

  return (
    <main
      id="main-content"
      className="mx-auto flex w-full max-w-xl flex-1 flex-col items-center justify-center gap-8 px-6 py-16"
    >
      <header className="text-center">
        <h1 className="bg-gradient-to-r from-primary to-foreground bg-clip-text text-transparent">
          PromptWars
        </h1>
        <p className="mt-3 text-balance text-lg text-muted-foreground">
          Travel Planning &amp; Experience Engine — plan trips dynamically with
          preferences, constraints, and real-time updates.
        </p>
      </header>

      <section
        aria-labelledby="signin-heading"
        className="w-full rounded-xl border border-border bg-background/60 p-8 shadow-sm"
      >
        <h2 id="signin-heading" className="text-center">
          Sign in to start planning
        </h2>
        <p className="mt-2 text-center text-sm text-muted-foreground">
          Your trips are private to your Google account.
        </p>
        <div className="mt-6 flex justify-center">
          <Button
            type="button"
            size="lg"
            onClick={handleSignIn}
            disabled={signingIn || loading}
            aria-busy={signingIn}
          >
            {signingIn ? "Signing in…" : "Continue with Google"}
          </Button>
        </div>
        {error && (
          <p role="alert" className="mt-4 text-center text-sm text-destructive">
            {error}
          </p>
        )}
      </section>
    </main>
  );
}
