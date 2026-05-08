"use client";

import { getFirebaseAuth } from "@/lib/firebase";
import type {
  Disruption,
  Preferences,
  Constraints,
  Trip,
  TripSummary,
} from "@/lib/types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8080";

export class ApiError extends Error {
  constructor(public status: number, public detail: unknown) {
    super(typeof detail === "string" ? detail : `API error ${status}`);
  }
}

async function authHeader(): Promise<Record<string, string>> {
  const user = getFirebaseAuth().currentUser;
  if (!user) return {};
  const token = await user.getIdToken();
  return { Authorization: `Bearer ${token}` };
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(await authHeader()),
    ...(init.headers ?? {}),
  };
  const response = await fetch(`${BASE_URL}${path}`, { ...init, headers });
  if (!response.ok) {
    let detail: unknown = response.statusText;
    try {
      detail = await response.json();
    } catch {
      /* non-JSON body */
    }
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export type CreateTripPayload = {
  preferences: Preferences;
  constraints: Constraints;
};

export const api = {
  health: () => apiFetch<{ status: string }>("/health"),
  me: () => apiFetch<{ uid: string; email: string; name: string }>("/me"),
  listTrips: () => apiFetch<TripSummary[]>("/trips"),
  createTrip: (payload: CreateTripPayload) =>
    apiFetch<Trip>("/trips", { method: "POST", body: JSON.stringify(payload) }),
  getTrip: (tripId: string) => apiFetch<Trip>(`/trips/${tripId}`),
  deleteTrip: (tripId: string) =>
    apiFetch<void>(`/trips/${tripId}`, { method: "DELETE" }),
  injectDisruption: (tripId: string, disruption: Disruption) =>
    apiFetch<Trip>(`/trips/${tripId}/disruptions`, {
      method: "POST",
      body: JSON.stringify(disruption),
    }),
};
