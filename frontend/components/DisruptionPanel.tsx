"use client";

import { useMemo, useState } from "react";
import { CloudRain, Construction, TrafficCone, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAnnouncer } from "@/components/LiveAnnouncer";
import { api, ApiError } from "@/lib/api";
import type { Day, Disruption, ItinerarySlot, Trip } from "@/lib/types";

type Preset = {
  key: string;
  label: string;
  description: string;
  icon: typeof CloudRain;
  build: (trip: Trip) => Disruption | null;
};

const PRESETS: Preset[] = [
  {
    key: "closure-first-outdoor",
    label: "Close iconic outdoor stop",
    description: "Closes the first outdoor place in your trip.",
    icon: Construction,
    build: (trip) => {
      const target = findFirstSlot(trip, (s) => s.tags.includes("outdoor"));
      if (!target) return null;
      return {
        type: "closure",
        place_id: target.place_id,
        reason: "venue closed for maintenance",
      };
    },
  },
  {
    key: "weather-day1-afternoon",
    label: "Heavy rain, Day 1 afternoon",
    description: "Forces an indoor swap if you have outdoor afternoon plans.",
    icon: CloudRain,
    build: (trip) => {
      const day = trip.itinerary.days[0];
      if (!day) return null;
      return {
        type: "weather",
        day_index: day.day_index,
        period: "afternoon",
        condition: "thunderstorm",
      };
    },
  },
  {
    key: "traffic-d1-mtoa",
    label: "Highway shutdown",
    description: "Reroutes between morning and afternoon on Day 1.",
    icon: TrafficCone,
    build: (trip) => {
      const day = trip.itinerary.days[0];
      const morning = day?.slots.find((s) => s.period === "morning");
      const afternoon = day?.slots.find((s) => s.period === "afternoon");
      if (!morning || !afternoon) return null;
      return {
        type: "traffic",
        from_slot_id: morning.slot_id,
        to_slot_id: afternoon.slot_id,
        reason: "highway shutdown",
      };
    },
  },
];

export function DisruptionPanel({ trip }: { trip: Trip }) {
  const announce = useAnnouncer();
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const buildableKeys = useMemo(
    () => new Set(PRESETS.filter((p) => p.build(trip) !== null).map((p) => p.key)),
    [trip],
  );

  async function fire(preset: Preset) {
    const disruption = preset.build(trip);
    if (!disruption) return;
    setBusyKey(preset.key);
    setError(null);
    announce(`Injecting disruption: ${preset.label}`);
    try {
      const updated = await api.injectDisruption(trip.trip_id, disruption);
      const last = updated.change_log.at(-1);
      const replaced = last?.affected_slot_ids ?? [];
      if (replaced.length === 0) {
        announce("Disruption logged but did not affect your itinerary.");
      } else {
        announce(
          `Plan updated. ${replaced.length} slot${replaced.length === 1 ? "" : "s"} replaced.`,
        );
      }
    } catch (err) {
      const message =
        err instanceof ApiError
          ? typeof err.detail === "object" && err.detail && "detail" in err.detail
            ? String((err.detail as { detail: unknown }).detail)
            : `Request failed (${err.status})`
          : "Could not apply disruption";
      setError(message);
      announce(`Disruption failed: ${message}`);
    } finally {
      setBusyKey(null);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="size-5 text-primary" aria-hidden="true" />
          Real-time disruption demo
        </CardTitle>
        <p className="mt-1 text-sm text-muted-foreground">
          Trigger a disruption to see your itinerary adapt in real time. The change log
          on the right will record what happened.
        </p>
      </CardHeader>
      <CardContent>
        <ul className="grid grid-cols-1 gap-2 sm:grid-cols-3" role="list">
          {PRESETS.map((preset) => {
            const Icon = preset.icon;
            const buildable = buildableKeys.has(preset.key);
            return (
              <li key={preset.key}>
                <Button
                  type="button"
                  variant="outline"
                  className="h-auto w-full flex-col items-start whitespace-normal py-3 text-left"
                  onClick={() => fire(preset)}
                  disabled={!buildable || busyKey !== null}
                  aria-busy={busyKey === preset.key}
                >
                  <span className="flex w-full items-center gap-2 font-medium">
                    <Icon className="size-4 text-primary" aria-hidden="true" />
                    {preset.label}
                  </span>
                  <span className="mt-1 text-xs text-muted-foreground">
                    {preset.description}
                    {!buildable && " · n/a for this trip"}
                  </span>
                </Button>
              </li>
            );
          })}
        </ul>
        {error && (
          <p role="alert" className="mt-3 text-sm text-destructive">
            {error}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function findFirstSlot(
  trip: Trip,
  predicate: (slot: ItinerarySlot) => boolean,
): ItinerarySlot | null {
  for (const day of trip.itinerary.days as Day[]) {
    for (const slot of day.slots) {
      if (predicate(slot)) return slot;
    }
  }
  return null;
}
