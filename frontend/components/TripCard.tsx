"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, CalendarDays, MapPin } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import type { TripSummary } from "@/lib/types";

export function TripCard({ trip, index = 0 }: { trip: TripSummary; index?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.04 }}
    >
      <Link
        href={`/trip?id=${encodeURIComponent(trip.trip_id)}`}
        aria-label={`Open trip to ${trip.destination}`}
        className="block focus-visible:outline-none"
      >
        <Card className="transition-shadow hover:shadow-md focus-visible:shadow-md">
          <CardContent className="flex items-center justify-between gap-4 p-5">
            <div>
              <p className="flex items-center gap-2 text-sm text-muted-foreground">
                <MapPin className="size-4" aria-hidden="true" />
                Destination
              </p>
              <h3 className="mt-1 text-xl font-semibold">{trip.destination}</h3>
              <p className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
                <CalendarDays className="size-4" aria-hidden="true" />
                {trip.arrival_date} → {trip.departure_date} ({trip.num_days} days)
              </p>
            </div>
            <ArrowRight
              className="size-5 text-muted-foreground transition-transform group-hover:translate-x-1"
              aria-hidden="true"
            />
          </CardContent>
        </Card>
      </Link>
    </motion.div>
  );
}
