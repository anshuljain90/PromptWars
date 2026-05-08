"use client";

import { useEffect, useState } from "react";
import { doc, onSnapshot } from "firebase/firestore";
import { getFirebaseAuth, getFirebaseFirestore } from "@/lib/firebase";
import type { Trip } from "@/lib/types";

type UseTripState = {
  trip: Trip | null;
  loading: boolean;
  error: string | null;
};

/**
 * Subscribes to the Firestore document for a single trip via onSnapshot.
 * Updates land in the UI within ~200ms of any backend write — including
 * disruption-injection writes from the API. No polling.
 */
export function useTrip(tripId: string | null): UseTripState {
  const [state, setState] = useState<UseTripState>({
    trip: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    if (!tripId) {
      setState({ trip: null, loading: false, error: null });
      return;
    }
    const auth = getFirebaseAuth();
    const uid = auth.currentUser?.uid;
    if (!uid) {
      setState({ trip: null, loading: false, error: "Not signed in" });
      return;
    }
    const ref = doc(getFirebaseFirestore(), "users", uid, "trips", tripId);
    const unsub = onSnapshot(
      ref,
      (snap) => {
        if (!snap.exists()) {
          setState({ trip: null, loading: false, error: "Trip not found" });
          return;
        }
        setState({
          trip: snap.data() as Trip,
          loading: false,
          error: null,
        });
      },
      (err) => {
        setState({ trip: null, loading: false, error: err.message });
      },
    );
    return () => unsub();
  }, [tripId]);

  return state;
}
