import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Bulwark Campus Digital Twin",
  description: "3D Campus Digital Twin with Bulwark visual theme",
};

export default function RootLayout({
  children}: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bulwark min-h-screen bg-black text-white">
        {children}
      </body>
    </html>
  );
}