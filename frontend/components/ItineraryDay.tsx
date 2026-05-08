"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Clock, Coins, IndianRupee, MapPin, Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Day, ItinerarySlot, SlotPeriod } from "@/lib/types";

const PERIOD_LABEL: Record<SlotPeriod, string> = {
  morning: "Morning",
  afternoon: "Afternoon",
  evening: "Evening",
};

const PERIOD_RANGE: Record<SlotPeriod, string> = {
  morning: "9:00 – 12:00",
  afternoon: "13:00 – 17:00",
  evening: "18:00 – 22:00",
};

export function ItineraryDay({ day, recentlyChangedIds }: { day: Day; recentlyChangedIds: Set<string> }) {
  return (
    <section aria-labelledby={`day-${day.day_index}-heading`} className="space-y-3">
      <header className="flex items-baseline justify-between">
        <h2 id={`day-${day.day_index}-heading`} className="text-2xl">
          Day {day.day_index}
        </h2>
        <span className="text-sm text-muted-foreground">{day.date_iso}</span>
      </header>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        <AnimatePresence mode="popLayout">
          {day.slots.map((slot) => (
            <SlotCard
              key={slot.slot_id}
              slot={slot}
              changed={recentlyChangedIds.has(slot.slot_id)}
            />
          ))}
        </AnimatePresence>
      </div>
    </section>
  );
}

function SlotCard({ slot, changed }: { slot: ItinerarySlot; changed: boolean }) {
  return (
    <motion.div
      layout
      key={`${slot.slot_id}-${slot.place_id}`}
      initial={{ opacity: 0, scale: 0.96, y: 8 }}
      animate={{
        opacity: 1,
        scale: 1,
        y: 0,
        boxShadow: changed
          ? "0 0 0 2px hsl(var(--success)) inset"
          : "0 0 0 0 transparent",
      }}
      exit={{ opacity: 0, scale: 0.96 }}
      transition={{ duration: 0.32, type: "spring", stiffness: 220, damping: 22 }}
    >
      <Card className="h-full">
        <CardHeader>
          <div className="flex items-center justify-between text-xs uppercase tracking-wide text-muted-foreground">
            <span>{PERIOD_LABEL[slot.period]}</span>
            <span>{PERIOD_RANGE[slot.period]}</span>
          </div>
          <CardTitle className="mt-1 text-lg">{slot.place_name}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {slot.description && (
            <p className="text-foreground/90">{slot.description}</p>
          )}
          <p className="flex items-start gap-2 text-muted-foreground">
            <Sparkles className="mt-0.5 size-4 shrink-0 text-primary" aria-hidden="true" />
            <span>{slot.rationale}</span>
          </p>
          <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-muted-foreground">
            <div className="flex items-center gap-1.5">
              <Clock className="size-3.5" aria-hidden="true" />
              <dt className="sr-only">Duration</dt>
              <dd>{slot.duration_min} min</dd>
            </div>
            <div className="flex items-center gap-1.5">
              <IndianRupee className="size-3.5" aria-hidden="true" />
              <dt className="sr-only">Estimated cost</dt>
              <dd>~{slot.estimated_cost_inr.toLocaleString("en-IN")}</dd>
            </div>
            <div className="col-span-2 flex items-center gap-1.5">
              <MapPin className="size-3.5" aria-hidden="true" />
              <dt className="sr-only">Address</dt>
              <dd className="line-clamp-1">{slot.address || `${slot.place_type}`}</dd>
            </div>
            {slot.travel_from_prev && (
              <div className="col-span-2 flex items-center gap-1.5">
                <Coins className="size-3.5" aria-hidden="true" />
                <dt className="sr-only">Travel from previous</dt>
                <dd>
                  {slot.travel_from_prev.duration_min} min by {slot.travel_from_prev.mode}
                </dd>
              </div>
            )}
          </dl>
          {slot.tags.length > 0 && (
            <ul className="flex flex-wrap gap-1.5" aria-label="Tags">
              {slot.tags.map((tag) => (
                <li
                  key={tag}
                  className="rounded-full bg-accent px-2 py-0.5 text-xs text-accent-foreground"
                >
                  {tag}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
