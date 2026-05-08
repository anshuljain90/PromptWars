"use client";

import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

type AnnounceFn = (message: string) => void;

const LiveAnnouncerContext = createContext<AnnounceFn>(() => {});

export function LiveAnnouncerProvider({ children }: { children: ReactNode }) {
  const [message, setMessage] = useState("");

  const announce = useCallback<AnnounceFn>((next) => {
    setMessage("");
    window.setTimeout(() => setMessage(next), 50);
  }, []);

  return (
    <LiveAnnouncerContext.Provider value={announce}>
      {children}
      <div role="status" aria-live="polite" aria-atomic="true" className="sr-only">
        {message}
      </div>
    </LiveAnnouncerContext.Provider>
  );
}

export function useAnnouncer(): AnnounceFn {
  return useContext(LiveAnnouncerContext);
}
