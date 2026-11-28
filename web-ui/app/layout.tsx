import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { UiAudioBoundary } from "@/components/audio/UiAudioBoundary";
import { SoundPreferenceProvider } from "@/components/audio/SoundPreferenceProvider";
import { PublicSessionProvider } from "@/components/session/PublicSessionProvider";
import { TelemetryProvider } from "@/components/telemetry/TelemetryProvider";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Legends of Champions Tactics",
  description: "A dark fantasy tactical battle interface.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        <PublicSessionProvider>
          <TelemetryProvider>
            <SoundPreferenceProvider>
              <UiAudioBoundary>{children}</UiAudioBoundary>
            </SoundPreferenceProvider>
          </TelemetryProvider>
        </PublicSessionProvider>
      </body>
    </html>
  );
}
