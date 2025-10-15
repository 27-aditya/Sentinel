// components/Sidebar/Sidebar.jsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Video, Search, Settings } from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();

  const menuItems = [
    { name: "Dashboard", icon: LayoutDashboard, href: "/" },
    { name: "Live Monitoring", icon: Video, href: "/live" },
    { name: "Search", icon: Search, href: "/search" },
  ];

  return (
    <aside className="w-[200px] h-screen bg-gradient-to-b from-gray-50 to-gray-100 flex flex-col py-8 fixed left-0 top-0 shadow-[4px_0_12px_rgba(0,0,0,0.08)] z-[1000]">
      {/* Logo Section */}
      <div className="mx-auto pb-6 border-b border-black/8 mb-2">
        <h1 className="text-3xl font-black text-black tracking-[0.1em]">
          SENTINEL
        </h1>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 px-6 flex flex-col gap-2">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={`
                flex items-center gap-4 px-5 py-4 rounded-xl
                text-base font-medium transition-all duration-200
                ${
                  isActive
                    ? "bg-white text-black font-semibold shadow-md"
                    : "text-gray-600 hover:bg-black/5 hover:text-gray-900"
                }
              `}
            >
              <Icon className="w-5 h-5" />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Bottom Section - Settings */}
      <div className="px-6 pt-6 border-t border-black/8 mt-auto">
        <Link
          href="/settings"
          className="flex items-center gap-4 px-5 py-4 rounded-xl text-base font-medium text-gray-600 hover:bg-black/5 hover:text-gray-900 transition-all duration-200"
        >
          <Settings className="w-5 h-5" />
          <span>Settings</span>
        </Link>
      </div>
    </aside>
  );
}
