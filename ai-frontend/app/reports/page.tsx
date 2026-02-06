"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getUser } from "@/lib/auth";
import { API_URL } from "@/lib/config";
import Link from "next/link";

interface Report {
  id: number;
  interview_id: string;
  user_id: number;
  overall_score: number | string;
  fluency?: number | string;
  grammar?: number | string;
  technical_depth?: number | string;
  confidence?: number | string;
  clarity?: number | string;
  job_readiness?: string;
  created_at?: string;
}

export default function ReportsPage() {
  const router = useRouter();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Convert text scores to numbers - returns null if missing/invalid
  const scoreToNumber = (score: number | string | undefined): number | null => {
    if (score === undefined || score === null || score === '') return null;
    if (typeof score === 'number') {
      if (score === 0) return null; // Treat 0 as missing
      return Math.min(10, Math.max(0, score));
    }
    const scoreMap: Record<string, number> = {
      'excellent': 9, 'very_good': 8, 'good': 7, 'above_average': 6.5,
      'average': 6, 'below_average': 5, 'fair': 4, 'poor': 3,
      'very_poor': 2, 'very_low': 2, 'inconsistent': 4, 'not_assessed': 0,
    };
    const key = String(score).toLowerCase().replace(/\s+/g, '_').replace(/[^a-z_]/g, '');
    if (key === 'not_assessed') return null;
    if (scoreMap[key] !== undefined) return scoreMap[key];
    const num = parseFloat(String(score));
    if (isNaN(num) || num === 0) return null;
    return Math.min(10, Math.max(0, num));
  };

  // Safe score for calculations (treats null as 0)
  const safeScore = (score: number | string | undefined): number => {
    const num = scoreToNumber(score);
    return num !== null ? num : 0;
  };

  // Check if metric data is available
  const hasMetricData = (report: Report): boolean => {
    return scoreToNumber(report.fluency) !== null ||
      scoreToNumber(report.technical_depth) !== null ||
      scoreToNumber(report.confidence) !== null;
  };

  const getScoreColor = (score: number | null) => {
    if (score === null) return "text-gray-500 bg-slate-700/30";
    if (score >= 7) return "text-green-400 bg-green-500/20";
    if (score >= 5) return "text-yellow-400 bg-yellow-500/20";
    return "text-red-400 bg-red-500/20";
  };

  const getScoreBg = (score: number) => {
    if (score >= 7) return "from-green-500 to-emerald-500";
    if (score >= 5) return "from-yellow-500 to-orange-500";
    return "from-red-500 to-pink-500";
  };

  const getScoreBarBg = (score: number) => {
    if (score >= 7) return "bg-green-500";
    if (score >= 5) return "bg-yellow-500";
    return "bg-red-500";
  };

  const getScoreTextColor = (score: number | null) => {
    if (score === null) return "text-gray-500";
    if (score >= 7) return "text-green-400";
    if (score >= 5) return "text-yellow-400";
    return "text-red-400";
  };

  // Calculate progress over last N interviews
  const calculateProgress = (reports: Report[], count: number = 5): { change: number; message: string } => {
    if (reports.length < 2) {
      return { change: 0, message: "Complete more interviews to track progress" };
    }

    const recentReports = reports.slice(0, Math.min(count, reports.length));
    const olderReports = reports.slice(Math.min(count, reports.length));

    if (olderReports.length === 0 && recentReports.length >= 2) {
      // Compare first half vs second half of recent
      const half = Math.floor(recentReports.length / 2);
      const newerHalf = recentReports.slice(0, half);
      const olderHalf = recentReports.slice(half);

      const newerAvg = newerHalf.reduce((sum, r) => sum + safeScore(r.overall_score), 0) / newerHalf.length;
      const olderAvg = olderHalf.reduce((sum, r) => sum + safeScore(r.overall_score), 0) / olderHalf.length;
      const change = newerAvg - olderAvg;

      if (change > 0.1) {
        return { change, message: `Your average score improved by +${change.toFixed(1)} over your last ${recentReports.length} interviews` };
      } else if (change < -0.1) {
        return { change, message: `Your average score decreased by ${change.toFixed(1)} over your last ${recentReports.length} interviews` };
      } else {
        return { change, message: `Your performance is consistent across your last ${recentReports.length} interviews` };
      }
    }

    const recentAvg = recentReports.reduce((sum, r) => sum + safeScore(r.overall_score), 0) / recentReports.length;
    const olderAvg = olderReports.reduce((sum, r) => sum + safeScore(r.overall_score), 0) / olderReports.length;
    const change = recentAvg - olderAvg;

    if (change > 0.1) {
      return { change, message: `Your average score improved by +${change.toFixed(1)} over the last ${recentReports.length} interviews` };
    } else if (change < -0.1) {
      return { change, message: `Your average score decreased by ${change.toFixed(1)} over the last ${recentReports.length} interviews` };
    } else {
      return { change, message: `Your performance is consistent across recent interviews` };
    }
  };

  // Get the best interview info
  const getBestInterviewInfo = (reports: Report[]): { score: number; interviewNum: number } => {
    let bestScore = 0;
    let bestIndex = 0;
    reports.forEach((r, i) => {
      const score = safeScore(r.overall_score);
      if (score > bestScore) {
        bestScore = score;
        bestIndex = i;
      }
    });
    return { score: bestScore, interviewNum: reports.length - bestIndex };
  };

  // Get overall status (only shown once)
  const getOverallStatus = (avgScore: number): { label: string; color: string } => {
    if (avgScore >= 7) return { label: "Ready for Interviews", color: "text-green-400 bg-green-500/15 border-green-500/30" };
    if (avgScore >= 5) return { label: "Developing – Keep Practicing", color: "text-yellow-400 bg-yellow-500/15 border-yellow-500/30" };
    return { label: "Needs More Practice", color: "text-red-400 bg-red-500/15 border-red-500/30" };
  };

  useEffect(() => {
    const fetchReports = async () => {
      const user = getUser();
      if (!user) {
        router.push("/login");
        return;
      }

      try {
        setLoading(true);
        const response = await fetch(`${API_URL}/api/user/${user.id}/reports`);

        if (!response.ok) {
          throw new Error("Failed to fetch reports");
        }

        const data = await response.json();
        setReports(data.reports || data || []);
      } catch (err: any) {
        console.error("Error fetching reports:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, [router]);

  const viewReport = (interviewId: string) => {
    sessionStorage.setItem("interviewId", interviewId);
    router.push("/report");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 px-6 py-8">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-white mb-2">Interview Reports</h1>
            <p className="text-gray-400">Review your past interview performance and track improvement</p>
          </div>
          <div className="flex items-center justify-center py-20">
            <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        </div>
      </div>
    );
  }

  // Calculate stats
  const avgScore = reports.length > 0
    ? reports.reduce((sum, r) => sum + safeScore(r.overall_score), 0) / reports.length
    : 0;
  const bestInfo = getBestInterviewInfo(reports);
  const progress = calculateProgress(reports);
  const overallStatus = getOverallStatus(avgScore);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 px-6 py-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Interview Reports</h1>
            <p className="text-gray-400">Review your past interview performance and track improvement</p>
          </div>
          <Link
            href="/interview"
            className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all shadow-lg shadow-blue-500/20"
          >
            Start New Interview
          </Link>
        </div>

        {reports.length === 0 ? (
          /* Empty State */
          <div className="bg-slate-800/50 rounded-2xl border border-slate-700/50 p-12 text-center">
            <div className="w-20 h-20 bg-slate-700 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-10 h-10 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">No interviews yet</h3>
            <p className="text-gray-400 mb-6">Complete your first interview to see your performance report</p>
            <Link
              href="/interview"
              className="inline-block px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all"
            >
              Start Your First Interview
            </Link>
          </div>
        ) : (
          /* Reports List */
          <div className="space-y-4">
            {/* Summary Stats with Context */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-2">
              <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
                <p className="text-gray-400 text-sm">Total Interviews</p>
                <p className="text-3xl font-bold text-white">{reports.length}</p>
              </div>
              <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
                <p className="text-gray-400 text-sm">Average Score <span className="text-gray-500 text-xs">(all time)</span></p>
                <p className="text-3xl font-bold text-blue-400">{avgScore.toFixed(1)}</p>
              </div>
              <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
                <p className="text-gray-400 text-sm">Best Score <span className="text-gray-500 text-xs">(Interview #{bestInfo.interviewNum})</span></p>
                <p className="text-3xl font-bold text-green-400">{bestInfo.score.toFixed(1)}</p>
              </div>
            </div>

            {/* Progress Indicator & Overall Status */}
            <div className="flex flex-col sm:flex-row gap-3 mb-6">
              {/* Progress Summary */}
              <div className="flex-1 bg-slate-800/30 rounded-xl px-4 py-3 border border-slate-700/30">
                <div className="flex items-center gap-2">
                  <span className={`text-lg ${progress.change > 0 ? 'text-green-400' : progress.change < 0 ? 'text-red-400' : 'text-gray-400'}`}>
                    {progress.change > 0 ? '📈' : progress.change < 0 ? '📉' : '📊'}
                  </span>
                  <p className="text-sm text-gray-300">
                    <span className="text-gray-500">Progress:</span> {progress.message}
                  </p>
                </div>
              </div>

              {/* Overall Status - shown once */}
              <div className={`shrink-0 px-4 py-3 rounded-xl border ${overallStatus.color}`}>
                <p className="text-sm font-medium">{overallStatus.label}</p>
              </div>
            </div>

            {/* Reports Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {reports.map((report, index) => {
                const score = safeScore(report.overall_score);
                const isLatest = index === 0;
                const isOlder = index >= 3; // De-emphasize after first 3

                return (
                  <div
                    key={report.id || index}
                    className={`bg-slate-800/50 rounded-xl border transition-all overflow-hidden cursor-pointer ${isLatest
                        ? 'border-blue-500/50 ring-1 ring-blue-500/20'
                        : 'border-slate-700/50 hover:border-slate-600'
                      } ${isOlder ? 'opacity-75 hover:opacity-100' : ''}`}
                    onClick={() => viewReport(report.interview_id)}
                  >
                    {/* Score Header */}
                    <div className={`bg-gradient-to-r ${getScoreBg(score)} ${isOlder ? 'p-3' : 'p-4'} text-white relative`}>
                      {/* Latest Badge */}
                      {isLatest && (
                        <span className="absolute top-2 right-2 px-2 py-0.5 bg-white/20 backdrop-blur-sm text-white text-[10px] font-medium rounded-full">
                          Latest Interview
                        </span>
                      )}
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-white/80 text-xs">Interview #{reports.length - index}</p>
                          <p className={`font-bold ${isOlder ? 'text-xl' : 'text-2xl'}`}>{score.toFixed(1)}/10</p>
                        </div>
                        <div className={`${isOlder ? 'w-10 h-10' : 'w-12 h-12'} bg-white/20 rounded-full flex items-center justify-center`}>
                          <svg className={`${isOlder ? 'w-5 h-5' : 'w-6 h-6'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                        </div>
                      </div>

                      {/* Score Progress Bar */}
                      <div className="mt-2 h-1 bg-white/20 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-white/60 rounded-full transition-all"
                          style={{ width: `${(score / 10) * 100}%` }}
                        />
                      </div>
                    </div>

                    {/* Details */}
                    <div className="p-4 bg-slate-800">
                      {/* Mini Metrics - handle missing data */}
                      {hasMetricData(report) ? (
                        <div className="grid grid-cols-3 gap-2 mb-3">
                          <div className="text-center">
                            <p className="text-xs text-gray-400">Fluency</p>
                            <p className={`text-sm font-semibold ${getScoreTextColor(scoreToNumber(report.fluency))}`}>
                              {scoreToNumber(report.fluency) !== null ? scoreToNumber(report.fluency)!.toFixed(0) : '—'}
                            </p>
                          </div>
                          <div className="text-center">
                            <p className="text-xs text-gray-400">Technical</p>
                            <p className={`text-sm font-semibold ${getScoreTextColor(scoreToNumber(report.technical_depth))}`}>
                              {scoreToNumber(report.technical_depth) !== null ? scoreToNumber(report.technical_depth)!.toFixed(0) : '—'}
                            </p>
                          </div>
                          <div className="text-center">
                            <p className="text-xs text-gray-400">Confidence</p>
                            <p className={`text-sm font-semibold ${getScoreTextColor(scoreToNumber(report.confidence))}`}>
                              {scoreToNumber(report.confidence) !== null ? scoreToNumber(report.confidence)!.toFixed(0) : '—'}
                            </p>
                          </div>
                        </div>
                      ) : (
                        <div className="mb-3 py-2 text-center">
                          <p className="text-xs text-gray-500">Detailed metrics not available</p>
                        </div>
                      )}

                      {/* Date only - no status label (shown once at top) */}
                      <div className="flex items-center justify-end">
                        <span className="text-xs text-gray-400">
                          {report.created_at ? new Date(report.created_at).toLocaleDateString() : "Recently"}
                        </span>
                      </div>

                      {/* View Button */}
                      <button className="w-full mt-3 py-2 bg-slate-700/50 hover:bg-slate-600 text-white text-sm font-medium rounded-lg transition">
                        View Report →
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}