"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Plus } from "lucide-react";
import { AppHeader } from "@/components/AppHeader";
import { Button } from "@/components/ui/button";
import { TripCard } from "@/components/TripCard";
import { useAuth } from "@/components/auth/AuthProvider";
import { api, ApiError } from "@/lib/api";
import type { TripSummary } from "@/lib/types";

export default function TripsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [trips, setTrips] = useState<TripSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/");
      return;
    }
    if (!user) return;
    let cancelled = false;
    (async () => {
      try {
        const list = await api.listTrips();
        if (!cancelled) setTrips(list);
      } catch (err) {
        if (cancelled) return;
        setError(
          err instanceof ApiError
            ? `Failed to load trips (${err.status})`
            : "Failed to load trips",
        );
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [loading, user, router]);

  if (loading || !user) {
    return (
      <main className="flex flex-1 items-center justify-center" aria-busy>
        <p className="text-muted-foreground">Loading…</p>
      </main>
    );
  }

  return (
    <>
      <AppHeader />
      <main id="main-content" className="mx-auto w-full max-w-6xl flex-1 px-6 py-10">
        <div className="mb-8 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="bg-gradient-to-r from-primary to-foreground bg-clip-text text-transparent">
              Your trips
            </h1>
            <p className="mt-1 text-muted-foreground">
              Pick up where you left off, or plan something new.
            </p>
          </div>
          <Button asChild size="lg">
            <Link href="/trips/new">
              <Plus className="size-4" aria-hidden="true" />
              Plan a new trip
            </Link>
          </Button>
        </div>

        {error && (
          <p role="alert" className="mb-6 rounded-md bg-destructive/10 p-4 text-sm text-destructive">
            {error}
          </p>
        )}

        {trips === null ? (
          <p className="text-muted-foreground">Loading trips…</p>
        ) : trips.length === 0 ? (
          <EmptyState />
        ) : (
          <ul className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3" role="list">
            {trips.map((trip, idx) => (
              <li key={trip.trip_id}>
                <TripCard trip={trip} index={idx} />
              </li>
            ))}
          </ul>
        )}
      </main>
    </>
  );
}

function EmptyState() {
  return (
    <section
      aria-labelledby="empty-heading"
      className="rounded-xl border border-dashed border-border bg-background/60 p-12 text-center"
    >
      <h2 id="empty-heading" className="text-xl">
        No trips yet
      </h2>
      <p className="mt-2 text-muted-foreground">
        Plan your first multi-day adventure with personalized preferences.
      </p>
      <div className="mt-6 flex justify-center">
        <Button asChild>
          <Link href="/trips/new">
            <Plus className="size-4" aria-hidden="true" />
            Plan a new trip
          </Link>
        </Button>
      </div>
    </section>
  );
}
