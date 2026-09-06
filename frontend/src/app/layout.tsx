import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Clearance Desk | Identity Screening",
  description: "Decision support for authorized document review.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}