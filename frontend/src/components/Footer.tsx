import React from "react";
import { Shield, GitFork, Cpu } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-slate-900 bg-slate-950/60 mt-auto py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-sky-500" />
          <span>ZeroGate &copy; {new Date().getFullYear()} — Context-Aware Zero Trust Access Platform</span>
        </div>
        <div className="flex items-center gap-4 font-mono">
          <span className="flex items-center gap-1 text-slate-400">
            <Cpu className="w-3.5 h-3.5 text-emerald-400" />
            NIST SP 800-207 Architecture
          </span>
          <span className="text-slate-700">|</span>
          <span className="text-slate-400">PS-12 Track: Network & Perimeter Security</span>
        </div>
      </div>
    </footer>
  );
}
