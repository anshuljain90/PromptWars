export type Interest =
  | "culture"
  | "food"
  | "adventure"
  | "nature"
  | "nightlife"
  | "shopping"
  | "history";

export type BudgetTier = "budget" | "mid_range" | "luxury";
export type Pace = "relaxed" | "balanced" | "packed";
export type DietaryPreference = "any" | "veg" | "non_veg" | "vegan";
export type GroupComposition = "solo" | "couple" | "family" | "friends";
export type SlotPeriod = "morning" | "afternoon" | "evening";
export type DisruptionType = "closure" | "traffic" | "weather";

export type Preferences = {
  interests: Interest[];
  budget: BudgetTier;
  pace: Pace;
  dietary: DietaryPreference;
  cuisines: string[];
  group: GroupComposition;
};

export type Constraints = {
  destination: string;
  arrival_date: string;
  departure_date: string;
  travelers: number;
  mobility_notes: string;
  must_see: string[];
  must_avoid: string[];
};

export type TravelLeg = {
  duration_min: number;
  distance_km: number;
  mode: string;
};

export type ItinerarySlot = {
  slot_id: string;
  period: SlotPeriod;
  place_id: string;
  place_name: string;
  place_type: string;
  address: string;
  lat: number;
  lng: number;
  description: string;
  duration_min: number;
  estimated_cost_inr: number;
  rationale: string;
  tags: string[];
  travel_from_prev: TravelLeg | null;
};

export type Day = {
  day_index: number;
  date_iso: string;
  slots: ItinerarySlot[];
};

export type Itinerary = {
  days: Day[];
  summary: string;
};

export type ChangeLogEntry = {
  at: string;
  disruption_type: DisruptionType;
  summary: string;
  affected_slot_ids: string[];
  replaced_with: string[];
};

export type Trip = {
  trip_id: string;
  owner_uid: string;
  preferences: Preferences;
  constraints: Constraints;
  itinerary: Itinerary;
  change_log: ChangeLogEntry[];
  created_at: string;
  updated_at: string;
};

export type TripSummary = {
  trip_id: string;
  destination: string;
  arrival_date: string;
  departure_date: string;
  num_days: number;
  created_at: string;
  updated_at: string;
};

export type ClosureDisruption = {
  type: "closure";
  place_id: string;
  reason?: string;
};

export type TrafficDisruption = {
  type: "traffic";
  from_slot_id: string;
  to_slot_id: string;
  reason?: string;
};

export type WeatherDisruption = {
  type: "weather";
  day_index: number;
  period: SlotPeriod;
  condition?: string;
};

export type Disruption =
  | ClosureDisruption
  | TrafficDisruption
  | WeatherDisruption;
