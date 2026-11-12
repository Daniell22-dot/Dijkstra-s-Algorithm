import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Campus Digital Twin",
  description: "3D Campus Digital Twin with indoor navigation",
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