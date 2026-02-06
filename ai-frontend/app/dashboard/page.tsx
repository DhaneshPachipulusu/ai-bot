"use client";

import { useEffect, useState, useMemo } from "react";
import { getUser } from "@/lib/auth";
import { API_URL } from "@/lib/config";
import Link from "next/link";
import dynamic from "next/dynamic";

// Dynamically import ParticleBackground to avoid SSR issues
const ParticleBackground = dynamic(() => import("@/components/ParticleBackground"), {
  ssr: false,
});

// Professional, encouraging subtexts
const motivationalTexts = [
  "Ready to sharpen your skills?",
  "Your preparation starts here",
  "Build confidence, one interview at a time",
  "Practice with purpose",
  "Every session counts",
];

// Feedback categories for interview cards
const feedbackCategories = [
  { label: "Communication", color: "blue" },
  { label: "Technical Depth", color: "purple" },
  { label: "Problem Solving", color: "green" },
  { label: "Confidence", color: "amber" },
];

export default function DashboardPage() {
  const [user, setUser] = useState<any>(null);
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [motivationIndex, setMotivationIndex] = useState(0);

  // Rotate motivational text with fade
  useEffect(() => {
    const interval = setInterval(() => {
      setMotivationIndex((prev) => (prev + 1) % motivationalTexts.length);
    }, 6000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const currentUser = getUser();
    setUser(currentUser);

    if (currentUser) {
      fetch(`${API_URL}/api/user/${currentUser.id}/reports`)
        .then((res) => res.json())
        .then((data) => {
          setReports(data.reports || []);
          setLoading(false);
        })
        .catch((err) => {
          console.error("Failed to fetch reports:", err);
          setLoading(false);
        });
    }
  }, []);

  // Calculate stats and trends
  const stats = useMemo(() => {
    if (reports.length === 0) {
      return {
        total: 0,
        avgScore: 0,
        minutesPracticed: 0,
        weeklyCount: 0,
        scoreTrend: 0,
      };
    }

    const getScore = (score: any): number => {
      if (score === null || score === undefined) return 0;
      const num = Number(score);
      return isNaN(num) ? 0 : num;
    };

    const total = reports.length;
    const avgScore = reports.reduce((sum, r) => sum + getScore(r.overall_score), 0) / reports.length;
    const minutesPracticed = reports.length * 15;

    // Calculate weekly interviews (last 7 days)
    const oneWeekAgo = new Date();
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
    const weeklyCount = reports.filter(
      (r) => new Date(r.created_at) >= oneWeekAgo
    ).length;

    // Calculate score trend
    let scoreTrend = 0;
    if (reports.length >= 2) {
      const sortedReports = [...reports].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      scoreTrend = getScore(sortedReports[0].overall_score) - getScore(sortedReports[1].overall_score);
    }

    return { total, avgScore, minutesPracticed, weeklyCount, scoreTrend };
  }, [reports]);

  const getScore = (score: any): number => {
    if (score === null || score === undefined) return 0;
    const num = Number(score);
    return isNaN(num) ? 0 : num;
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  // Get feedback chips based on score
  const getFeedbackChips = (score: number) => {
    const chips = [];
    if (score >= 7) {
      chips.push(feedbackCategories[0]); // Communication
      chips.push(feedbackCategories[2]); // Problem Solving
    } else if (score >= 5) {
      chips.push(feedbackCategories[1]); // Technical Depth
      chips.push(feedbackCategories[3]); // Confidence
    } else {
      chips.push(feedbackCategories[0]); // Communication
      chips.push(feedbackCategories[1]); // Technical Depth
    }
    return chips.slice(0, 2);
  };

  return (
    <div className="w-full mx-auto relative">
      {/* Animated Particle Background */}
      <ParticleBackground />

      {/* Content wrapper */}
      <div className="relative z-10">
        {/* Welcome Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-semibold text-white mb-3 tracking-tight">
            Welcome back, <span className="text-blue-400">{user.username}</span>
          </h1>
          <p
            key={motivationIndex}
            className="text-lg text-gray-400/90 transition-all duration-500 ease-out"
          >
            {motivationalTexts[motivationIndex]}
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid md:grid-cols-3 gap-5 mb-12">
          {/* Interviews Completed */}
          <div className="stat-card">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-md shadow-blue-500/15">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h3 className="text-3xl font-semibold text-white tracking-tight">{stats.total}</h3>
                <p className="text-sm text-gray-400/80">Interviews Completed</p>
                <p className="trend-indicator trend-up">
                  {stats.weeklyCount > 0 ? `+${stats.weeklyCount} this week` : "Get started"}
                </p>
              </div>
            </div>
          </div>

          {/* Average Score */}
          <div className="stat-card">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-md shadow-emerald-500/15">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <div>
                <h3 className="text-3xl font-semibold text-white tracking-tight">
                  {stats.total > 0 ? stats.avgScore.toFixed(1) : "—"}
                </h3>
                <p className="text-sm text-gray-400/80">Average Score</p>
                <p className={`trend-indicator ${stats.scoreTrend >= 0 ? "trend-up" : "text-red-400/90"}`}>
                  {stats.total >= 2
                    ? `${stats.scoreTrend >= 0 ? "↑" : "↓"} ${Math.abs(stats.scoreTrend).toFixed(1)} from last`
                    : "Keep going"}
                </p>
              </div>
            </div>
          </div>

          {/* Minutes Practiced */}
          <div className="stat-card">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-violet-500 to-violet-600 rounded-xl flex items-center justify-center shadow-md shadow-violet-500/15">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h3 className="text-3xl font-semibold text-white tracking-tight">{stats.minutesPracticed}</h3>
                <p className="text-sm text-gray-400/80">Minutes Practiced</p>
                <p className="trend-indicator trend-neutral">Past 7 days</p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-2 gap-5 mb-12">
          {/* Primary CTA - Start AI Interview */}
          <Link
            href="/interview"
            className="group bg-gradient-to-r from-blue-600 via-blue-500 to-indigo-600 rounded-2xl p-7 text-white transition-all duration-300 ease-out shadow-lg shadow-blue-500/20 hover:shadow-xl hover:shadow-blue-500/25 transform hover:-translate-y-0.5 hover:scale-[1.01] relative overflow-hidden"
          >
            {/* Subtle shimmer overlay */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-out"></div>

            <div className="flex items-center justify-between relative z-10">
              <div>
                <h3 className="text-xl font-semibold mb-1.5 tracking-tight">Start AI Interview</h3>
                <p className="text-blue-100/90 text-sm">Upload your resume and practice</p>
              </div>
              <div className="w-12 h-12 bg-white/15 rounded-xl flex items-center justify-center group-hover:bg-white/20 transition-colors duration-300">
                <svg className="w-6 h-6 group-hover:translate-x-0.5 transition-transform duration-300 ease-out" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </div>
            </div>
          </Link>

          {/* Learning Hub Card */}
          <Link
            href="/learn"
            className="group bg-slate-800/40 backdrop-blur-sm rounded-2xl p-7 border border-slate-700/40 transition-all duration-300 ease-out hover:border-slate-600/60 hover:bg-slate-800/60 hover:-translate-y-0.5"
          >
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-xl font-semibold text-white mb-1.5 tracking-tight">Learning Hub</h3>
                <p className="text-gray-400/80 text-sm">Interview prep resources</p>
              </div>
              <div className="w-12 h-12 bg-slate-700/40 rounded-xl flex items-center justify-center group-hover:bg-blue-500/15 transition-colors duration-300">
                <svg className="w-6 h-6 text-blue-400 group-hover:translate-x-0.5 transition-transform duration-300 ease-out" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
            </div>
            {/* Topic Tags */}
            <div className="flex flex-wrap gap-2">
              <span className="topic-tag">HR Questions</span>
              <span className="topic-tag">System Design</span>
              <span className="topic-tag">Behavioral</span>
            </div>
          </Link>
        </div>

        {/* Recent Interviews */}
        <div>
          <div className="flex items-center justify-between mb-5">
            <h2 className="section-title">Recent Interviews</h2>
            <Link href="/reports" className="text-blue-400/90 hover:text-blue-300 font-medium text-sm flex items-center gap-1.5 group transition-colors duration-200">
              View All
              <svg className="w-4 h-4 group-hover:translate-x-0.5 transition-transform duration-200 ease-out" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>

          {loading ? (
            <div className="interview-card p-12 text-center">
              <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-gray-400/80 text-sm">Loading...</p>
            </div>
          ) : reports.length === 0 ? (
            <div className="interview-card p-12 text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-slate-700/80 to-slate-800 rounded-2xl flex items-center justify-center mx-auto mb-5">
                <svg className="w-8 h-8 text-gray-500" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-white mb-2">No interviews yet</h3>
              <p className="text-gray-400/80 mb-6 max-w-sm mx-auto text-sm">Start your first session to track progress and receive feedback</p>
              <Link
                href="/interview"
                className="inline-block px-6 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium text-sm rounded-xl transition-all duration-300 ease-out shadow-md shadow-blue-500/20 hover:shadow-lg hover:shadow-blue-500/25 hover:-translate-y-0.5"
              >
                Start Interview
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {reports.slice(0, 5).map((report) => {
                const score = getScore(report.overall_score);
                const progressPercent = (score / 10) * 100;
                const chips = getFeedbackChips(score);

                return (
                  <div
                    key={report.id}
                    className="interview-card"
                  >
                    <div className="flex items-center justify-between gap-6">
                      {/* Left: Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-medium text-white truncate">
                            Interview #{report.id}
                          </h3>
                          <span className="px-2 py-0.5 bg-emerald-500/15 text-emerald-400 text-xs font-medium rounded-full shrink-0">
                            Completed
                          </span>
                        </div>
                        <p className="text-sm text-gray-500 mb-3">
                          {new Date(report.created_at).toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </p>
                        {/* Feedback Chips */}
                        <div className="flex flex-wrap gap-2">
                          {chips.map((chip, idx) => (
                            <span
                              key={idx}
                              className={`feedback-chip ${chip.color === "blue"
                                ? "bg-blue-500/10 text-blue-400/90 border-blue-500/25"
                                : chip.color === "purple"
                                  ? "bg-purple-500/10 text-purple-400/90 border-purple-500/25"
                                  : chip.color === "green"
                                    ? "bg-emerald-500/10 text-emerald-400/90 border-emerald-500/25"
                                    : "bg-amber-500/10 text-amber-400/90 border-amber-500/25"
                                }`}
                            >
                              {chip.label}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Right: Score + Action */}
                      <div className="flex items-center gap-5 shrink-0">
                        {/* Score Circle */}
                        <div className="text-center">
                          <div
                            className={`w-14 h-14 rounded-full flex items-center justify-center text-xl font-semibold border-2 ${score >= 7
                              ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-400"
                              : score >= 5
                                ? "bg-amber-500/10 border-amber-500/40 text-amber-400"
                                : "bg-red-500/10 border-red-500/40 text-red-400"
                              }`}
                          >
                            {score > 0 ? score.toFixed(1) : "—"}
                          </div>
                          <div className="text-[11px] text-gray-500 mt-1.5 font-medium uppercase tracking-wider">Score</div>
                          {/* Progress Bar */}
                          <div className="progress-bar-bg w-14 mt-1.5">
                            <div
                              className={`progress-bar-fill ${score >= 7
                                ? "bg-emerald-500"
                                : score >= 5
                                  ? "bg-amber-500"
                                  : "bg-red-500"
                                }`}
                              style={{ width: `${progressPercent}%` }}
                            ></div>
                          </div>
                        </div>

                        <Link
                          href={`/reports/${report.interview_id}`}
                          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-all duration-200 ease-out text-sm font-medium"
                        >
                          View
                        </Link>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}