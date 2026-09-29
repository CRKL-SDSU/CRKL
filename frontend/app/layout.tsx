import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CRKL API Console",
  description: "A small frontend for testing the CRKL Space Exploration API"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
