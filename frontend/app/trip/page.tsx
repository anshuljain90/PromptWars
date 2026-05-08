"use client";

import { Suspense, useEffect, useMemo } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { AppHeader } from "@/components/AppHeader";
import { Button } from "@/components/ui/button";
import { ChangeLog } from "@/components/ChangeLog";
import { DisruptionPanel } from "@/components/DisruptionPanel";
import { ItineraryDay } from "@/components/ItineraryDay";
import { useAuth } from "@/components/auth/AuthProvider";
import { useTrip } from "@/lib/useTrip";

export default function TripPageWrapper() {
  return (
    <Suspense fallback={<LoadingShell />}>
      <TripPage />
    </Suspense>
  );
}

function TripPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const params = useSearchParams();
  const tripId = params.get("id");
  const { trip, loading, error } = useTrip(tripId);

  useEffect(() => {
    if (!authLoading && !user) router.replace("/");
  }, [authLoading, user, router]);

  const recentlyChangedIds = useMemo<Set<string>>(() => {
    if (!trip || trip.change_log.length === 0) return new Set();
    const last = trip.change_log[trip.change_log.length - 1];
    return new Set(last.affected_slot_ids);
  }, [trip]);

  if (authLoading || !user) return <LoadingShell />;
  if (!tripId) return <ErrorShell message="Missing trip id." />;
  if (loading) return <LoadingShell />;
  if (error) return <ErrorShell message={error} />;
  if (!trip) return <ErrorShell message="Trip not found." />;

  return (
    <>
      <AppHeader />
      <main id="main-content" className="mx-auto w-full max-w-7xl flex-1 px-6 py-8">
        <div className="mb-6">
          <Button asChild variant="ghost" size="sm" className="-ml-2">
            <Link href="/trips">
              <ArrowLeft className="size-4" aria-hidden="true" />
              All trips
            </Link>
          </Button>
        </div>
        <header className="mb-8">
          <p className="text-sm text-muted-foreground">
            {trip.constraints.arrival_date} → {trip.constraints.departure_date} ·{" "}
            {trip.constraints.travelers} traveler
            {trip.constraints.travelers === 1 ? "" : "s"}
          </p>
          <h1 className="bg-gradient-to-r from-primary to-foreground bg-clip-text text-transparent">
            {trip.constraints.destination}
          </h1>
          {trip.itinerary.summary && (
            <p className="mt-2 max-w-3xl text-muted-foreground">
              {trip.itinerary.summary}
            </p>
          )}
        </header>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="space-y-8">
            {trip.itinerary.days.map((day) => (
              <ItineraryDay
                key={day.day_index}
                day={day}
                recentlyChangedIds={recentlyChangedIds}
              />
            ))}
          </div>
          <aside className="space-y-6">
            <DisruptionPanel trip={trip} />
            <ChangeLog entries={trip.change_log} />
          </aside>
        </div>
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

function ErrorShell({ message }: { message: string }) {
  return (
    <>
      <AppHeader />
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-12">
        <p role="alert" className="text-destructive">
          {message}
        </p>
        <Button asChild className="mt-4" variant="outline">
          <Link href="/trips">Back to trips</Link>
        </Button>
      </main>
    </>
  );
}
