"use client"

import { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";
import Image from "next/image";


export default function Navbar() {
  const [openSidebar, setOpenSidebar] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);
  if (!mounted) return null;

  return (
    <div className="relative">
      <nav className="fixed top-0 left-0 w-full h-16 bg-gray-50 text-foreground flex items-center justify-between px-8 md:px-16 z-50 overflow-hidden">

        {/* Background Image */}
        <div className="absolute inset-0 z-0">
          <Image 
            src="/hexagonal-bg.jpg" 
            alt="Background" 
            fill
            className="object-cover opacity-30"
          />
        </div>
    
        {/* Sidebar toggle - only visible on mobile */}
        <button onClick={() => setOpenSidebar(!openSidebar)} className="md:hidden">
          {openSidebar ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>

        {/* Logo on the right */}
        <div className="ml-auto relative z-10">
          <Image 
            src="/nitc_logo_icon.svg"
            alt="NITC Logo"
            width={40}
            height={40}
            className="object-contain"
          />
        </div>

        {/* Mobile Sidebar */}
        {openSidebar && (
          <div className="absolute top-16 left-0 w-full bg-white border-b border-gray-300 shadow-lg md:hidden">
            <ul className="flex flex-col p-4 gap-3">
              <li className="cursor-pointer hover:bg-gray-100 p-2 rounded text-sm text-gray-800">Dashboard</li>
              <li className="cursor-pointer hover:bg-gray-100 p-2 rounded text-sm text-gray-800">Live Monitoring</li>
              <li className="cursor-pointer hover:bg-gray-100 p-2 rounded text-sm text-gray-800">Search</li>
              <li className="cursor-pointer hover:bg-gray-100 p-2 rounded text-sm text-gray-800">Admin Console</li>
              <li className="cursor-pointer hover:bg-gray-100 p-2 rounded text-sm text-gray-800">About</li>
            </ul>
          </div>
        )}
        
      </nav>
    </div>
  );
}
