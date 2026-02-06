"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { getUser, logout } from "@/lib/auth";
import { useFresherJobs } from "@/lib/JobNotificationContext";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showJobDropdown, setShowJobDropdown] = useState(false);

  const user = getUser();
  const { jobs, hasJobs, jobCount, dismissed, dismissJobs } = useFresherJobs();

  // Fullscreen pages (no navbar)
  const fullscreenPages = ["/login", "/interview", "/report", "/reports"];
  const isFullscreen = fullscreenPages.some(page => pathname === page || pathname?.startsWith(page + "/"));

  if (isFullscreen) {
    return <>{children}</>;
  }

  const navItems = [
    { href: "/", label: "Home" },
    { href: "/learn", label: "Learning" },
    { href: "/interview", label: "Interview" },
    { href: "/resume-analysis", label: "Resume AI" },
    { href: "/reports", label: "Reports" },
    { href: "/practice", label: "Practice" },
    { href: "/settings", label: "Settings" },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">

      {/* DARK NAVBAR */}
      <nav className="sticky top-0 z-50 bg-slate-900/80 backdrop-blur-xl border-b border-slate-700/50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex items-center justify-between h-14">

            {/* Logo */}
            <Link href="/" className="flex items-center gap-3 group">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-lg group-hover:scale-105 transition-transform">
                AI
              </div>
              <span className="text-xl font-bold text-white hidden sm:block">
                Interview Bot
              </span>
            </Link>

            {/* Navigation Links */}
            <div className="flex items-center gap-0.5">
              {navItems.map((item) => {
                const isActive = pathname === item.href || (item.href === "/" && pathname === "/dashboard");
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-200 ease-out relative ${isActive
                      ? "bg-blue-500/15 text-blue-400"
                      : "text-gray-400 hover:bg-slate-800/80 hover:text-gray-200"
                      }`}
                  >
                    {item.label}
                    {isActive && (
                      <span
                        className="absolute bottom-0.5 left-3 right-3 h-0.5 bg-blue-400 rounded-full"
                        style={{ boxShadow: '0 0 6px rgba(96, 165, 250, 0.4)' }}
                      ></span>
                    )}
                  </Link>
                );
              })}
            </div>

            {/* User Profile & Notifications */}
            <div className="flex items-center gap-4">
              {/* Notification Bell with Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setShowJobDropdown(!showJobDropdown)}
                  className="relative text-gray-400 hover:text-white p-2 rounded-lg hover:bg-slate-800/50 transition-colors"
                >
                  {/* Notification Indicator - show if has jobs and not dismissed */}
                  {hasJobs && !dismissed && (
                    <div className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full flex items-center justify-center">
                      <span className="text-[10px] font-bold text-white">{jobCount}</span>
                    </div>
                  )}
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                </button>

                {/* Fresher Opportunities Dropdown */}
                {showJobDropdown && (
                  <>
                    <div
                      className="fixed inset-0 z-40"
                      onClick={() => setShowJobDropdown(false)}
                    ></div>

                    <div className="absolute right-0 mt-2 w-80 bg-slate-800 rounded-xl shadow-xl border border-slate-700 z-50 overflow-hidden">
                      {/* Header */}
                      <div className="px-4 py-3 bg-slate-800/80 border-b border-slate-700 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-lg">💼</span>
                          <h3 className="font-semibold text-white text-sm">Fresher Opportunities</h3>
                        </div>
                        {hasJobs && !dismissed && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              dismissJobs();
                            }}
                            className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
                          >
                            Clear
                          </button>
                        )}
                      </div>

                      {/* Content */}
                      <div className="max-h-[350px] overflow-y-auto">
                        {hasJobs ? (
                          <div className="py-2">
                            {jobs.map((job) => (
                              <div
                                key={job.id}
                                className="px-4 py-3 hover:bg-slate-700/30 transition-colors border-b border-slate-700/30 last:border-b-0"
                              >
                                <div className="flex items-start justify-between gap-3">
                                  <div className="flex-1 min-w-0">
                                    <h4 className="font-medium text-white text-sm truncate">{job.title}</h4>
                                    <p className="text-gray-400 text-xs mt-0.5">{job.company}</p>
                                    <div className="flex items-center gap-1.5 mt-1.5">
                                      <svg className="w-3 h-3 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                                      </svg>
                                      <span className="text-gray-500 text-xs">{job.location}</span>
                                    </div>
                                  </div>

                                  <a
                                    href={job.apply_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="shrink-0 px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded-lg hover:bg-blue-500 transition-colors"
                                  >
                                    Apply
                                  </a>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="p-6 text-center">
                            <div className="w-12 h-12 bg-slate-700/50 rounded-xl flex items-center justify-center mx-auto mb-3">
                              <svg className="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                              </svg>
                            </div>
                            <p className="text-gray-400 text-sm">No opportunities available</p>
                            <p className="text-gray-500 text-xs mt-1">Check back later</p>
                          </div>
                        )}
                      </div>

                      {/* Footer */}
                      {hasJobs && (
                        <div className="px-4 py-2.5 bg-slate-800/50 border-t border-slate-700">
                          <p className="text-[10px] text-gray-600 text-center">
                            Opportunities shared by your college / placement cell
                          </p>
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>

              {/* User Menu */}
              <div className="relative">
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center gap-2 hover:bg-slate-800 rounded-xl px-3 py-2 transition-colors"
                >
                  <div className="w-9 h-9 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-semibold">
                    {user?.username?.charAt(0).toUpperCase() || "U"}
                  </div>
                  <div className="text-left hidden sm:block">
                    <p className="text-sm font-semibold text-white">{user?.username || "User"}</p>
                  </div>
                  <svg
                    className={`w-4 h-4 text-gray-400 transition-transform ${showUserMenu ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {/* Dropdown Menu */}
                {showUserMenu && (
                  <>
                    <div
                      className="fixed inset-0 z-40"
                      onClick={() => setShowUserMenu(false)}
                    ></div>

                    <div className="absolute right-0 mt-2 w-56 bg-slate-800 rounded-xl shadow-xl border border-slate-700 py-2 z-50">
                      <div className="px-4 py-3 border-b border-slate-700">
                        <p className="text-sm font-semibold text-white">{user?.username}</p>
                        <p className="text-xs text-gray-400">{user?.college}</p>
                        <p className="text-xs text-gray-500 mt-1">ID: {user?.id}</p>
                      </div>

                      <Link
                        href="/dashboard"
                        onClick={() => setShowUserMenu(false)}
                        className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-slate-700 flex items-center gap-2"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                        </svg>
                        Dashboard
                      </Link>

                      <Link
                        href="/settings"
                        onClick={() => setShowUserMenu(false)}
                        className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-slate-700 flex items-center gap-2"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        Settings
                      </Link>

                      <div className="border-t border-slate-700 mt-2 pt-2">
                        <button
                          onClick={logout}
                          className="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-red-500/10 flex items-center gap-2"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                          </svg>
                          Logout
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>

          </div>
        </div>
      </nav>

      {/* MAIN CONTENT */}
      <main className="max-w-7xl mx-auto px-6 py-8 animate-page-in">
        {children}
      </main>

      {/* FOOTER */}
      <footer className="mt-auto py-6 border-t border-slate-700/50">
        <div className="max-w-7xl mx-auto px-6 text-center text-sm text-gray-500">
          AI Interview Bot © {new Date().getFullYear()}
        </div>
      </footer>

    </div>
  );
}