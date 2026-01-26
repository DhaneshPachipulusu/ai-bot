"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getUser } from "@/lib/auth";
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

  // Convert text scores to numbers
  const scoreToNumber = (score: number | string | undefined): number => {
    if (score === undefined || score === null) return 0;
    if (typeof score === 'number') return Math.min(10, Math.max(0, score));
    const scoreMap: Record<string, number> = {
      'excellent': 9, 'very_good': 8, 'good': 7, 'above_average': 6.5,
      'average': 6, 'below_average': 5, 'fair': 4, 'poor': 3,
      'very_poor': 2, 'very_low': 2, 'inconsistent': 4, 'not_assessed': 0,
    };
    const key = String(score).toLowerCase().replace(/\s+/g, '_').replace(/[^a-z_]/g, '');
    if (scoreMap[key] !== undefined) return scoreMap[key];
    const num = parseFloat(String(score));
    return isNaN(num) ? 0 : Math.min(10, Math.max(0, num));
  };

  const getScoreColor = (score: number) => {
    if (score >= 7) return "text-green-400 bg-green-500/20";
    if (score >= 5) return "text-yellow-400 bg-yellow-500/20";
    return "text-red-400 bg-red-500/20";
  };

  const getScoreBg = (score: number) => {
    if (score >= 7) return "from-green-500 to-emerald-500";
    if (score >= 5) return "from-yellow-500 to-orange-500";
    return "from-red-500 to-pink-500";
  };

  const getScoreTextColor = (score: number) => {
    if (score >= 7) return "text-green-400";
    if (score >= 5) return "text-yellow-400";
    return "text-red-400";
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
        const response = await fetch(`http://127.0.0.1:8000/api/user/${user.id}/reports`);
        
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
          className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all"
        >
          New Interview
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
          {/* Summary Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
              <p className="text-gray-400 text-sm">Total Interviews</p>
              <p className="text-3xl font-bold text-white">{reports.length}</p>
            </div>
            <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
              <p className="text-gray-400 text-sm">Average Score</p>
              <p className="text-3xl font-bold text-blue-400">
                {(reports.reduce((sum, r) => sum + scoreToNumber(r.overall_score), 0) / reports.length).toFixed(1)}
              </p>
            </div>
            <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
              <p className="text-gray-400 text-sm">Best Score</p>
              <p className="text-3xl font-bold text-green-400">
                {Math.max(...reports.map(r => scoreToNumber(r.overall_score))).toFixed(1)}
              </p>
            </div>
          </div>

          {/* Reports Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {reports.map((report, index) => {
              const score = scoreToNumber(report.overall_score);
              return (
                <div
                  key={report.id || index}
                  className="bg-slate-800/50 rounded-xl border border-slate-700/50 hover:border-slate-600 transition-all overflow-hidden cursor-pointer"
                  onClick={() => viewReport(report.interview_id)}
                >
                  {/* Score Header */}
                  <div className={`bg-gradient-to-r ${getScoreBg(score)} p-4 text-white`}>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-white/80 text-xs">Interview #{reports.length - index}</p>
                        <p className="text-2xl font-bold">{score.toFixed(1)}/10</p>
                      </div>
                      <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                    </div>
                  </div>

                  {/* Details */}
                  <div className="p-4 bg-slate-800">
                    {/* Mini Metrics */}
                    <div className="grid grid-cols-3 gap-2 mb-3">
                      <div className="text-center">
                        <p className="text-xs text-gray-400">Fluency</p>
                        <p className={`text-sm font-semibold ${getScoreTextColor(scoreToNumber(report.fluency))}`}>
                          {scoreToNumber(report.fluency).toFixed(0)}
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-xs text-gray-400">Technical</p>
                        <p className={`text-sm font-semibold ${getScoreTextColor(scoreToNumber(report.technical_depth))}`}>
                          {scoreToNumber(report.technical_depth).toFixed(0)}
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-xs text-gray-400">Confidence</p>
                        <p className={`text-sm font-semibold ${getScoreTextColor(scoreToNumber(report.confidence))}`}>
                          {scoreToNumber(report.confidence).toFixed(0)}
                        </p>
                      </div>
                    </div>

                    {/* Status */}
                    <div className="flex items-center justify-between">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getScoreColor(score)}`}>
                        {report.job_readiness || (score >= 7 ? "Ready" : score >= 5 ? "Developing" : "Needs Practice")}
                      </span>
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