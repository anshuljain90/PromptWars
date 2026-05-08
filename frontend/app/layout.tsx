import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { LiveAnnouncerProvider } from "@/components/LiveAnnouncer";

export const metadata: Metadata = {
  title: "PromptWars — Travel Planning & Experience Engine",
  description:
    "Plan trips dynamically with preferences, constraints, and real-time updates.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground"
        >
          Skip to main content
        </a>
        <AuthProvider>
          <LiveAnnouncerProvider>
            <div className="flex min-h-screen flex-col">{children}</div>
          </LiveAnnouncerProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
