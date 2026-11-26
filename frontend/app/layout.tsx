import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "API Console · CRKL-Space", template: "%s · CRKL-Space" },
  description: "Search and explore space missions, agencies, spacecraft, and launches"
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
