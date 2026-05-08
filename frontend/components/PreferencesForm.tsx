"use client";

import { useState, type FormEvent } from "react";
import { motion } from "framer-motion";
import {
  Calendar,
  Compass,
  CookingPot,
  Heart,
  MapPin,
  Sparkles,
  Users,
  Wallet,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/cn";
import type {
  BudgetTier,
  Constraints,
  DietaryPreference,
  GroupComposition,
  Interest,
  Pace,
  Preferences,
} from "@/lib/types";

type FormState = {
  destination: string;
  arrivalDate: string;
  departureDate: string;
  travelers: number;
  mobilityNotes: string;
  mustSee: string;
  mustAvoid: string;
  interests: Set<Interest>;
  budget: BudgetTier;
  pace: Pace;
  dietary: DietaryPreference;
  cuisines: string;
  group: GroupComposition;
};

const DEFAULTS: FormState = {
  destination: "Jaipur",
  arrivalDate: "",
  departureDate: "",
  travelers: 2,
  mobilityNotes: "",
  mustSee: "",
  mustAvoid: "",
  interests: new Set<Interest>(["history", "food"]),
  budget: "mid_range",
  pace: "balanced",
  dietary: "any",
  cuisines: "",
  group: "couple",
};

const INTEREST_OPTIONS: { value: Interest; label: string }[] = [
  { value: "culture", label: "Culture" },
  { value: "food", label: "Food" },
  { value: "adventure", label: "Adventure" },
  { value: "nature", label: "Nature" },
  { value: "nightlife", label: "Nightlife" },
  { value: "shopping", label: "Shopping" },
  { value: "history", label: "History" },
];

const BUDGET_OPTIONS: { value: BudgetTier; label: string; hint: string }[] = [
  { value: "budget", label: "Budget", hint: "Keep things lean" },
  { value: "mid_range", label: "Mid-range", hint: "Comfort + value" },
  { value: "luxury", label: "Luxury", hint: "Premium experiences" },
];

const PACE_OPTIONS: { value: Pace; label: string }[] = [
  { value: "relaxed", label: "Relaxed" },
  { value: "balanced", label: "Balanced" },
  { value: "packed", label: "Packed" },
];

const DIET_OPTIONS: { value: DietaryPreference; label: string }[] = [
  { value: "any", label: "No restriction" },
  { value: "veg", label: "Vegetarian" },
  { value: "non_veg", label: "Non-veg" },
  { value: "vegan", label: "Vegan" },
];

const GROUP_OPTIONS: { value: GroupComposition; label: string }[] = [
  { value: "solo", label: "Solo" },
  { value: "couple", label: "Couple" },
  { value: "family", label: "Family" },
  { value: "friends", label: "Friends" },
];

export type PreferencesFormProps = {
  onSubmit: (preferences: Preferences, constraints: Constraints) => Promise<void>;
  submitting: boolean;
  error?: string | null;
};

export function PreferencesForm({ onSubmit, submitting, error }: PreferencesFormProps) {
  const [state, setState] = useState<FormState>(DEFAULTS);

  function setField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setState((prev) => ({ ...prev, [key]: value }));
  }

  function toggleInterest(interest: Interest) {
    setState((prev) => {
      const next = new Set(prev.interests);
      if (next.has(interest)) {
        next.delete(interest);
      } else {
        next.add(interest);
      }
      return { ...prev, interests: next };
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (state.interests.size === 0) return;

    const preferences: Preferences = {
      interests: Array.from(state.interests),
      budget: state.budget,
      pace: state.pace,
      dietary: state.dietary,
      cuisines: state.cuisines
        .split(",")
        .map((c) => c.trim())
        .filter(Boolean),
      group: state.group,
    };
    const constraints: Constraints = {
      destination: state.destination.trim(),
      arrival_date: state.arrivalDate,
      departure_date: state.departureDate,
      travelers: state.travelers,
      mobility_notes: state.mobilityNotes.trim(),
      must_see: state.mustSee
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      must_avoid: state.mustAvoid
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
    };
    await onSubmit(preferences, constraints);
  }

  return (
    <motion.form
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="grid grid-cols-1 gap-6 lg:grid-cols-2"
      onSubmit={handleSubmit}
      aria-label="Trip preferences and constraints"
      noValidate
    >
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="size-5 text-primary" aria-hidden="true" />
            Destination &amp; dates
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="destination">Destination</Label>
            <Input
              id="destination"
              required
              value={state.destination}
              onChange={(e) => setField("destination", e.target.value)}
              placeholder="Jaipur, Goa, Bangalore…"
              autoComplete="off"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label htmlFor="arrival_date">Arrival</Label>
              <Input
                id="arrival_date"
                type="date"
                required
                value={state.arrivalDate}
                onChange={(e) => setField("arrivalDate", e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="departure_date">Departure</Label>
              <Input
                id="departure_date"
                type="date"
                required
                value={state.departureDate}
                onChange={(e) => setField("departureDate", e.target.value)}
              />
            </div>
          </div>
          <div>
            <Label htmlFor="travelers">Number of travelers</Label>
            <Input
              id="travelers"
              type="number"
              min={1}
              max={20}
              required
              value={state.travelers}
              onChange={(e) =>
                setField("travelers", Number.parseInt(e.target.value, 10) || 1)
              }
            />
          </div>
          <div>
            <Label htmlFor="mobility">Mobility / accessibility notes</Label>
            <Textarea
              id="mobility"
              value={state.mobilityNotes}
              onChange={(e) => setField("mobilityNotes", e.target.value)}
              placeholder="Wheelchair access, avoid stairs, etc."
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="size-5 text-primary" aria-hidden="true" />
            Interests
          </CardTitle>
        </CardHeader>
        <CardContent>
          <fieldset>
            <legend className="sr-only">Interests</legend>
            <div className="flex flex-wrap gap-2" role="group" aria-label="Trip interests">
              {INTEREST_OPTIONS.map((opt) => {
                const active = state.interests.has(opt.value);
                return (
                  <label
                    key={opt.value}
                    className={cn(
                      "cursor-pointer rounded-full border px-4 py-2 text-sm transition-colors",
                      active
                        ? "border-primary bg-primary text-primary-foreground"
                        : "border-border bg-background hover:bg-accent",
                    )}
                  >
                    <input
                      type="checkbox"
                      className="sr-only"
                      checked={active}
                      onChange={() => toggleInterest(opt.value)}
                    />
                    {opt.label}
                  </label>
                );
              })}
            </div>
            {state.interests.size === 0 && (
              <p className="mt-2 text-xs text-destructive" role="alert">
                Select at least one interest
              </p>
            )}
          </fieldset>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wallet className="size-5 text-primary" aria-hidden="true" />
            Budget &amp; pace
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <RadioCardGroup
            legend="Budget tier"
            name="budget"
            value={state.budget}
            options={BUDGET_OPTIONS}
            onChange={(v) => setField("budget", v as BudgetTier)}
          />
          <RadioCardGroup
            legend="Pace"
            name="pace"
            value={state.pace}
            options={PACE_OPTIONS}
            onChange={(v) => setField("pace", v as Pace)}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CookingPot className="size-5 text-primary" aria-hidden="true" />
            Dietary preferences
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <RadioCardGroup
            legend="Diet"
            name="diet"
            value={state.dietary}
            options={DIET_OPTIONS}
            onChange={(v) => setField("dietary", v as DietaryPreference)}
          />
          <div>
            <Label htmlFor="cuisines">Favorite cuisines (comma-separated)</Label>
            <Input
              id="cuisines"
              value={state.cuisines}
              onChange={(e) => setField("cuisines", e.target.value)}
              placeholder="rajasthani, south indian, italian"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="size-5 text-primary" aria-hidden="true" />
            Group composition
          </CardTitle>
        </CardHeader>
        <CardContent>
          <RadioCardGroup
            legend="Group"
            name="group"
            value={state.group}
            options={GROUP_OPTIONS}
            onChange={(v) => setField("group", v as GroupComposition)}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Heart className="size-5 text-primary" aria-hidden="true" />
            Must-see &amp; must-avoid
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="must_see">Must-see places</Label>
            <Input
              id="must_see"
              value={state.mustSee}
              onChange={(e) => setField("mustSee", e.target.value)}
              placeholder="Hawa Mahal, Amber Fort"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              Comma-separated. The planner will guarantee these appear in your trip.
            </p>
          </div>
          <div>
            <Label htmlFor="must_avoid">Must-avoid places or categories</Label>
            <Input
              id="must_avoid"
              value={state.mustAvoid}
              onChange={(e) => setField("mustAvoid", e.target.value)}
              placeholder="Crowded markets, late-night spots"
            />
          </div>
        </CardContent>
      </Card>

      <div className="lg:col-span-2 flex flex-col items-end gap-3">
        {error && (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        )}
        <Button
          type="submit"
          size="lg"
          disabled={submitting || state.interests.size === 0}
          aria-busy={submitting}
          className="min-w-48"
        >
          {submitting ? (
            <span className="flex items-center gap-2">
              <Compass className="size-4 animate-spin" aria-hidden="true" />
              Crafting your trip…
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <Calendar className="size-4" aria-hidden="true" />
              Generate itinerary
            </span>
          )}
        </Button>
      </div>
    </motion.form>
  );
}

type RadioCardGroupProps<T extends string> = {
  legend: string;
  name: string;
  value: T;
  options: { value: T; label: string; hint?: string }[];
  onChange: (value: T) => void;
};

function RadioCardGroup<T extends string>({
  legend,
  name,
  value,
  options,
  onChange,
}: RadioCardGroupProps<T>) {
  return (
    <fieldset>
      <legend className="mb-2 text-sm font-medium text-foreground">{legend}</legend>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {options.map((opt) => {
          const active = opt.value === value;
          return (
            <label
              key={opt.value}
              className={cn(
                "flex cursor-pointer flex-col rounded-lg border px-4 py-3 text-sm transition-colors",
                active
                  ? "border-primary bg-primary/10 text-foreground"
                  : "border-border bg-background hover:bg-accent",
              )}
            >
              <input
                type="radio"
                name={name}
                value={opt.value}
                checked={active}
                onChange={() => onChange(opt.value)}
                className="sr-only"
              />
              <span className="font-medium">{opt.label}</span>
              {opt.hint && (
                <span className="text-xs text-muted-foreground">{opt.hint}</span>
              )}
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
