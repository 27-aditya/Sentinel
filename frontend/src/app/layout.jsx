// src/app/layout.js

import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Layout/Navbar";
import Sidebar from "@/components/Layout/Sidebar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "Sentinel",
  description: "Sentinel Surveilence System",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <div className="h-screen flex">
          <Sidebar />
          <div className="flex flex-1 min-h-0 flex-col md:overflow-hidden">
            <Navbar />
            <main className="flex-1">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
