"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import { PreferencesForm } from "@/components/PreferencesForm";
import { useAuth } from "@/components/auth/AuthProvider";
import { useAnnouncer } from "@/components/LiveAnnouncer";
import { api, ApiError } from "@/lib/api";
import type { Constraints, Preferences } from "@/lib/types";

export default function NewTripPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const announce = useAnnouncer();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !user) router.replace("/");
  }, [loading, user, router]);

  async function handleSubmit(preferences: Preferences, constraints: Constraints) {
    setSubmitting(true);
    setError(null);
    announce("Generating your itinerary, this can take a few seconds.");
    try {
      const trip = await api.createTrip({ preferences, constraints });
      announce(`Itinerary ready for ${trip.constraints.destination}`);
      router.push(`/trip?id=${encodeURIComponent(trip.trip_id)}`);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? typeof err.detail === "object" && err.detail && "detail" in err.detail
            ? String((err.detail as { detail: unknown }).detail)
            : `Request failed (${err.status})`
          : "Could not create the trip";
      setError(message);
      announce(`Trip generation failed: ${message}`);
      setSubmitting(false);
    }
  }

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
        <div className="mb-8">
          <h1 className="bg-gradient-to-r from-primary to-foreground bg-clip-text text-transparent">
            Plan a new trip
          </h1>
          <p className="mt-1 text-muted-foreground">
            Tell us your preferences and constraints — we&apos;ll plan the rest.
          </p>
        </div>
        <PreferencesForm onSubmit={handleSubmit} submitting={submitting} error={error} />
      </main>
    </>
  );
}
