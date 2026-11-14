import type { Metadata } from "next";
import "cesium/Build/Cesium/Widgets/widgets.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "DeKUT Digital Twin | Indoor Navigation",
  description:
    "3D Web-GIS campus digital twin with BIM, CesiumJS and Dijkstra indoor routing.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bulwark min-h-screen bg-black text-white">{children}</body>
    </html>
  );
}
