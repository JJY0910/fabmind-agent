"use client";

import { type FormEvent, useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { Search, Bell, ShieldCheck, LogIn, LogOut } from "lucide-react";
import {
  ApiClientError,
  clearStoredAccessToken,
  fetchCurrentUser,
  getStoredAccessToken,
  signIn,
  signOut,
  type AuthUser,
} from "@/lib/api";
import { getCurrentNavItem } from "./navigation";

export function Topbar() {
  const pathname = usePathname();
  const currentPage = getCurrentNavItem(pathname).topbarLabel;
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [isCheckingSession, setIsCheckingSession] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    if (!getStoredAccessToken()) {
      setIsCheckingSession(false);
      return;
    }

    fetchCurrentUser()
      .then((user) => {
        if (cancelled) return;
        setCurrentUser(user);
        setAuthError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiClientError && err.kind === "unauthorized") {
          clearStoredAccessToken();
        }
        setCurrentUser(null);
      })
      .finally(() => {
        if (!cancelled) setIsCheckingSession(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSignIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAuthError(null);

    const trimmedUsername = username.trim();
    if (!trimmedUsername || !password) {
      setAuthError("Enter username and password.");
      return;
    }

    setIsSubmitting(true);
    try {
      const user = await signIn({ username: trimmedUsername, password });
      setCurrentUser(user);
      setPassword("");
      setAuthError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Sign in failed.";
      setAuthError(message);
      setCurrentUser(null);
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleSignOut() {
    signOut();
    setCurrentUser(null);
    setPassword("");
    setAuthError(null);
  }

  return (
    <header className="h-16 bg-[#0a1322]/80 backdrop-blur-md border-b border-[#1a2c4d] flex items-center justify-between px-6 sticky top-0 z-10">
      <div className="flex items-center gap-3 text-sm text-slate-400">
        <span className="px-2.5 py-1 rounded bg-[#111d33] text-xs font-mono border border-[#1a2c4d] text-[#00e5ff]">SYS-OP</span>
        <span className="text-slate-600">/</span>
        <span className="text-white font-medium">{currentPage}</span>
      </div>
      
      <div className="flex items-center gap-6">
        <div className="relative group">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-[#00e5ff] transition-colors" />
          <input 
            type="text" 
            placeholder="Search Equipment ID or Alarm Code..." 
            className="bg-[#050b14] border border-[#1a2c4d] rounded-full pl-9 pr-4 py-1.5 text-sm w-80 text-slate-300 focus:outline-none focus:border-[#00e5ff] focus:ring-1 focus:ring-[#00e5ff] transition-all placeholder:text-slate-600"
          />
        </div>
        
        <div className="flex items-center gap-4 border-l border-[#1a2c4d] pl-6">
          <div className="flex items-center gap-2 px-3 py-1 bg-[#00cc66]/10 text-[#00cc66] border border-[#00cc66]/30 rounded-full text-xs font-medium shadow-[0_0_8px_rgba(0,204,102,0.15)]">
            <ShieldCheck className="w-3.5 h-3.5" />
            Agent Core Active
          </div>
          {currentUser ? (
            <div className="flex items-center gap-3">
              <div className="text-right leading-tight">
                <div className="text-xs text-white">{currentUser.username}</div>
                <div className="text-[10px] font-mono text-[#00e5ff]">{currentUser.role}</div>
              </div>
              <button
                type="button"
                onClick={handleSignOut}
                className="inline-flex items-center gap-1.5 rounded-md border border-[#1a2c4d] bg-[#111d33] px-2.5 py-1.5 text-xs font-medium text-slate-300 transition-colors hover:border-[#00e5ff]/40 hover:text-white"
              >
                <LogOut className="h-3.5 w-3.5" />
                Sign out
              </button>
            </div>
          ) : (
            <form onSubmit={handleSignIn} className="flex items-center gap-2" aria-label="Operational account sign in">
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                    placeholder="Username"
                    autoComplete="username"
                    disabled={isCheckingSession || isSubmitting}
                    className="h-8 w-28 rounded-md border border-[#1a2c4d] bg-[#050b14] px-2 text-xs text-slate-300 outline-none transition-colors placeholder:text-slate-600 focus:border-[#00e5ff] focus:ring-1 focus:ring-[#00e5ff]"
                  />
                  <input
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="Password"
                    autoComplete="current-password"
                    disabled={isCheckingSession || isSubmitting}
                    className="h-8 w-28 rounded-md border border-[#1a2c4d] bg-[#050b14] px-2 text-xs text-slate-300 outline-none transition-colors placeholder:text-slate-600 focus:border-[#00e5ff] focus:ring-1 focus:ring-[#00e5ff]"
                  />
                  <button
                    type="submit"
                    disabled={isCheckingSession || isSubmitting}
                    className="inline-flex h-8 items-center gap-1.5 rounded-md bg-[#00e5ff] px-2.5 text-xs font-bold text-[#050b14] transition-colors hover:bg-[#00e5ff]/90 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <LogIn className="h-3.5 w-3.5" />
                    {isSubmitting ? "Signing in" : "Sign in"}
                  </button>
                </div>
                {authError ? <span className="mt-1 text-[10px] text-[#ffaa00]">{authError}</span> : null}
              </div>
            </form>
          )}
          <button className="relative p-2 text-slate-400 hover:text-white hover:bg-[#111d33] rounded-full transition-all">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[#ffaa00] rounded-full border border-[#0a1322] shadow-[0_0_5px_rgba(255,170,0,0.5)]"></span>
          </button>
        </div>
      </div>
    </header>
  );
}
