"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { AppHeader } from "@/components/AppHeader";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/auth/AuthProvider";
import { api, ApiError } from "@/lib/api";
import type { Trip } from "@/lib/types";

export default function TripPageWrapper() {
  return (
    <Suspense fallback={<LoadingShell />}>
      <TripPage />
    </Suspense>
  );
}

function TripPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const params = useSearchParams();
  const tripId = params.get("id");
  const [trip, setTrip] = useState<Trip | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/");
      return;
    }
    if (!user || !tripId) return;
    let cancelled = false;
    (async () => {
      try {
        const fetched = await api.getTrip(tripId);
        if (!cancelled) setTrip(fetched);
      } catch (err) {
        if (cancelled) return;
        setError(
          err instanceof ApiError ? `Failed to load trip (${err.status})` : "Failed to load trip",
        );
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [loading, user, tripId, router]);

  if (loading || !user) return <LoadingShell />;
  if (!tripId) {
    return (
      <>
        <AppHeader />
        <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-12">
          <p role="alert">Missing trip id.</p>
          <Button asChild className="mt-4">
            <Link href="/trips">Back to trips</Link>
          </Button>
        </main>
      </>
    );
  }
  if (error) {
    return (
      <>
        <AppHeader />
        <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-12">
          <p role="alert" className="text-destructive">
            {error}
          </p>
          <Button asChild className="mt-4" variant="outline">
            <Link href="/trips">Back to trips</Link>
          </Button>
        </main>
      </>
    );
  }
  if (!trip) return <LoadingShell />;

  return (
    <>
      <AppHeader />
      <main id="main-content" className="mx-auto w-full max-w-6xl flex-1 px-6 py-10">
        <div className="mb-8 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm text-muted-foreground">
              {trip.constraints.arrival_date} → {trip.constraints.departure_date}
            </p>
            <h1 className="bg-gradient-to-r from-primary to-foreground bg-clip-text text-transparent">
              {trip.constraints.destination}
            </h1>
            {trip.itinerary.summary && (
              <p className="mt-1 max-w-2xl text-muted-foreground">
                {trip.itinerary.summary}
              </p>
            )}
          </div>
        </div>

        <p className="rounded-md border border-dashed border-border bg-background/60 p-6 text-sm text-muted-foreground">
          Itinerary cards, animated map, and the disruption-injection panel land in Phase 4.
          For now, here is the raw count of slots:{" "}
          <strong className="text-foreground">
            {trip.itinerary.days.reduce((acc, d) => acc + d.slots.length, 0)}
          </strong>{" "}
          across {trip.itinerary.days.length} days.
        </p>
      </main>
    </>
  );
}

function LoadingShell() {
  return (
    <main className="flex flex-1 items-center justify-center" aria-busy>
      <p className="text-muted-foreground">Loading…</p>
    </main>
  );
}
