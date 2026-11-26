import type { Metadata, Viewport } from "next";
import StealthInitializer from "@/components/StealthInitializer";
import "./globals.css";

export const metadata: Metadata = {
  title: "J.A.R.V.I.S. Mobile & Web HUD",
  description: "Stark Iron Man Holographic Visual HUD & Voice Assistant",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "J.A.R.V.I.S. HUD",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#030712",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <StealthInitializer />
        {children}
      </body>
    </html>
  );
}
