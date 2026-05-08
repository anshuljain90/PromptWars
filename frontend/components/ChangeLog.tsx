"use client";

import { motion } from "framer-motion";
import { CloudRain, Construction, History, TrafficCone } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ChangeLogEntry, DisruptionType } from "@/lib/types";

const ICON: Record<DisruptionType, typeof CloudRain> = {
  closure: Construction,
  traffic: TrafficCone,
  weather: CloudRain,
};

const LABEL: Record<DisruptionType, string> = {
  closure: "Closure",
  traffic: "Traffic",
  weather: "Weather",
};

export function ChangeLog({ entries }: { entries: ChangeLogEntry[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <History className="size-5 text-primary" aria-hidden="true" />
          Change log
        </CardTitle>
      </CardHeader>
      <CardContent>
        {entries.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No disruptions yet. Your itinerary is unchanged from the original plan.
          </p>
        ) : (
          <ol className="space-y-3" aria-label="Disruptions applied to this trip">
            {[...entries]
              .reverse()
              .map((entry, idx) => {
                const Icon = ICON[entry.disruption_type];
                return (
                  <motion.li
                    key={`${entry.at}-${idx}`}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.25, delay: idx * 0.03 }}
                    className="flex items-start gap-3 rounded-md border border-border bg-background/60 p-3 text-sm"
                  >
                    <Icon className="mt-0.5 size-4 shrink-0 text-primary" aria-hidden="true" />
                    <div className="flex-1">
                      <p className="font-medium">{LABEL[entry.disruption_type]}</p>
                      <p className="mt-0.5 text-muted-foreground">{entry.summary}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {new Date(entry.at).toLocaleString()}
                        {entry.affected_slot_ids.length > 0 && (
                          <>
                            {" · affected "}
                            {entry.affected_slot_ids.join(", ")}
                          </>
                        )}
                      </p>
                    </div>
                  </motion.li>
                );
              })}
          </ol>
        )}
      </CardContent>
    </Card>
  );
}
