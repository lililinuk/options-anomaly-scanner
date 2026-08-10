import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Options Anomaly Scanner",
  description: "Research and decision-support for unusual equity options positioning.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

