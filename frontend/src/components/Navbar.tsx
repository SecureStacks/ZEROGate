"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { 
  ShieldCheck, 
  LayoutDashboard, 
  Sliders, 
  FileText, 
  Network, 
  ScrollText,
  LogOut,
  User as UserIcon
} from "lucide-react";
import { fetchCurrentUser, UserItem, logout } from "@/lib/api";

const navItems = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Simulator", href: "/simulator", icon: Sliders },
  { name: "Policies", href: "/policies", icon: FileText, adminOnly: true },
  { name: "Topology", href: "/topology", icon: Network },
  { name: "Audit Logs", href: "/logs", icon: ScrollText },
];

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<UserItem | null>(null);

  useEffect(() => {
    async function loadUser() {
      const currentUser = await fetchCurrentUser();
      setUser(currentUser);
    }
    loadUser();
  }, [pathname]); // Refresh user on navigation to handle auth state changes simply

  const handleLogout = async () => {
    await logout();
    setUser(null);
    router.push("/login");
  };

  // Don't show navbar on login page
  if (pathname === "/login") return null;

  return (
    <header className="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo & Name */}
          <div className="flex items-center gap-3">
            <Link href="/dashboard" className="flex items-center gap-2.5 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 via-sky-500 to-emerald-500 p-0.5 flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:shadow-indigo-500/40 transition-all">
                <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                  <ShieldCheck className="w-5 h-5 text-sky-400 group-hover:scale-110 transition-transform" />
                </div>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                    ZeroGate
                  </span>
                  <span className="text-[10px] uppercase font-mono tracking-widest px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20 font-semibold">
                    ZTNA
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 -mt-0.5">PS-12 Context-Aware Simulator</p>
              </div>
            </Link>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-1 flex-1 justify-center">
            {navItems.map((item) => {
              if (item.adminOnly && user?.role !== "Admin") return null;
              
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href));
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? "bg-slate-800 text-sky-400 shadow-sm border border-slate-700/80"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-sky-400" : "text-slate-400"}`} />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* User Profile & Logout */}
          <div className="flex items-center gap-4">
            {user && (
              <div className="flex items-center gap-3">
                <div className="flex flex-col items-end hidden md:flex">
                  <span className="text-sm font-medium text-slate-200">{user.display_name}</span>
                  <span className="text-xs text-sky-400 font-medium">{user.role}</span>
                </div>
                <button
                  onClick={handleLogout}
                  className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
                  title="Logout"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
