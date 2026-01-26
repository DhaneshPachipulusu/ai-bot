"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

interface QAFeedback {
  question: string;
  user_answer: string;
  better_answer?: string;
  score?: number;
}

interface ReportData {
  overall_score: number | string;
  fluency: number | string;
  grammar: number | string;
  technical_depth: number | string;
  confidence: number | string;
  clarity: number | string;
  response_pace: number | string;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  job_readiness: string;
  qa_feedback?: QAFeedback[];
  conversation?: Array<{ role: string; content: string }>;
}

export default function ReportPage() {
  const router = useRouter();
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [showFeedback, setShowFeedback] = useState(false);

  // Convert text scores to numbers
  const scoreToNumber = (score: number | string): number => {
    if (typeof score === 'number') return Math.min(10, Math.max(0, score));
    const scoreMap: Record<string, number> = {
      'excellent': 9, 'very_good': 8, 'good': 7, 'above_average': 6.5,
      'average': 6, 'below_average': 5, 'fair': 4, 'poor': 3,
      'very_poor': 2, 'very_low': 2, 'inconsistent': 4, 'not_assessed': 0,
    };
    const key = String(score).toLowerCase().replace(/\s+/g, '_').replace(/[^a-z_]/g, '');
    if (scoreMap[key] !== undefined) return scoreMap[key];
    const num = parseFloat(String(score));
    return isNaN(num) ? 5 : Math.min(10, Math.max(0, num));
  };

  useEffect(() => {
    const id = sessionStorage.getItem("interviewId");
    if (!id) { router.push("/interview"); return; }

    fetch(`http://127.0.0.1:8000/api/analyze-interview?interview_id=${id}`, { method: "POST" })
      .then((res) => res.json())
      .then((data) => { setReport(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [router]);

  if (loading) {
    return (
      <div className="h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-white text-sm">Analyzing...</p>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="h-screen bg-slate-900 flex items-center justify-center">
        <p className="text-red-400">Failed to load report</p>
      </div>
    );
  }

  const overallScore = scoreToNumber(report.overall_score);
  const metrics = [
    { label: "Fluency", value: scoreToNumber(report.fluency) },
    { label: "Grammar", value: scoreToNumber(report.grammar) },
    { label: "Technical", value: scoreToNumber(report.technical_depth) },
    { label: "Confidence", value: scoreToNumber(report.confidence) },
    { label: "Clarity", value: scoreToNumber(report.clarity) },
    { label: "Pace", value: scoreToNumber(report.response_pace) },
  ];

  // Extract Q&A from conversation if available
  const qaFeedback: QAFeedback[] = report.qa_feedback || [];
  if (qaFeedback.length === 0 && report.conversation) {
    for (let i = 0; i < report.conversation.length - 1; i++) {
      if (report.conversation[i].role === 'assistant' && report.conversation[i + 1]?.role === 'user') {
        qaFeedback.push({
          question: report.conversation[i].content,
          user_answer: report.conversation[i + 1].content,
        });
      }
    }
  }

  const getColor = (s: number) => s >= 7 ? "#22c55e" : s >= 5 ? "#eab308" : "#ef4444";

  // Radar Chart Component
  const RadarChart = () => {
    const size = 200;
    const center = size / 2;
    const radius = 70;
    const levels = 5;

    const angleStep = (2 * Math.PI) / metrics.length;
    const startAngle = -Math.PI / 2;

    // Create points for each metric
    const points = metrics.map((m, i) => {
      const angle = startAngle + i * angleStep;
      const r = (m.value / 10) * radius;
      return {
        x: center + r * Math.cos(angle),
        y: center + r * Math.sin(angle),
        labelX: center + (radius + 25) * Math.cos(angle),
        labelY: center + (radius + 25) * Math.sin(angle),
        label: m.label,
        value: m.value,
      };
    });

    const polygonPoints = points.map(p => `${p.x},${p.y}`).join(' ');

    return (
      <svg width={size} height={size} className="mx-auto">
        {/* Background levels */}
        {[...Array(levels)].map((_, i) => {
          const r = ((i + 1) / levels) * radius;
          const levelPoints = metrics.map((_, j) => {
            const angle = startAngle + j * angleStep;
            return `${center + r * Math.cos(angle)},${center + r * Math.sin(angle)}`;
          }).join(' ');
          return (
            <polygon
              key={i}
              points={levelPoints}
              fill="none"
              stroke="#334155"
              strokeWidth="1"
            />
          );
        })}

        {/* Axis lines */}
        {metrics.map((_, i) => {
          const angle = startAngle + i * angleStep;
          return (
            <line
              key={i}
              x1={center}
              y1={center}
              x2={center + radius * Math.cos(angle)}
              y2={center + radius * Math.sin(angle)}
              stroke="#334155"
              strokeWidth="1"
            />
          );
        })}

        {/* Data polygon */}
        <polygon
          points={polygonPoints}
          fill="rgba(59, 130, 246, 0.3)"
          stroke="#3b82f6"
          strokeWidth="2"
        />

        {/* Data points */}
        {points.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r="4" fill={getColor(p.value)} />
        ))}

        {/* Labels */}
        {points.map((p, i) => (
          <text
            key={i}
            x={p.labelX}
            y={p.labelY}
            textAnchor="middle"
            dominantBaseline="middle"
            className="fill-gray-400 text-[10px]"
          >
            {p.label}
          </text>
        ))}
      </svg>
    );
  };

  return (
    <div className="min-h-[calc(100vh-56px)] bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h1 className="text-lg font-bold text-white">Interview Report</h1>
        <div className="flex gap-2">
          <Link href="/interview" className="px-3 py-1 bg-blue-600 text-white text-xs rounded-lg">New</Link>
          <Link href="/dashboard" className="px-3 py-1 bg-slate-700 text-white text-xs rounded-lg">Dashboard</Link>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 min-h-0">
        
        {/* Left: Radar Chart + Score */}
        <div className="lg:col-span-4 bg-slate-800/60 rounded-xl p-4 flex flex-col items-center justify-center min-h-[400px]">
          <RadarChart />
          <div className="text-center mt-2">
            <span className={`text-3xl font-bold ${overallScore >= 7 ? "text-green-400" : overallScore >= 5 ? "text-yellow-400" : "text-red-400"}`}>
              {overallScore.toFixed(1)}
            </span>
            <span className="text-gray-400 text-sm">/10</span>
          </div>
          <p className="text-gray-400 text-xs">Overall Score</p>
          <span className={`mt-1 px-2 py-0.5 rounded-full text-xs ${overallScore >= 7 ? "bg-green-500/20 text-green-400" : overallScore >= 5 ? "bg-yellow-500/20 text-yellow-400" : "bg-red-500/20 text-red-400"}`}>
            {report.job_readiness || (overallScore >= 7 ? "Ready" : overallScore >= 5 ? "Developing" : "Needs Practice")}
          </span>
        </div>

        {/* Right: Feedback */}
        <div className="lg:col-span-8 flex flex-col gap-4 min-h-[400px]">
          {/* Strengths & Weaknesses Row */}
          <div className="grid grid-cols-2 gap-3">
            {/* Strengths */}
            <div className="bg-green-500/10 rounded-xl p-3 border border-green-500/20">
              <h4 className="text-green-400 font-semibold text-xs mb-2">✓ Strengths</h4>
              <ul className="space-y-1">
                {(report.strengths || []).slice(0, 2).map((s, i) => (
                  <li key={i} className="text-gray-300 text-xs leading-tight">{s}</li>
                ))}
              </ul>
            </div>
            {/* Weaknesses */}
            <div className="bg-orange-500/10 rounded-xl p-3 border border-orange-500/20">
              <h4 className="text-orange-400 font-semibold text-xs mb-2">⚠ Improve</h4>
              <ul className="space-y-1">
                {(report.weaknesses || []).slice(0, 2).map((w, i) => (
                  <li key={i} className="text-gray-300 text-xs leading-tight">{w}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Suggestions */}
          <div className="bg-blue-500/10 rounded-xl p-3 border border-blue-500/20">
            <h4 className="text-blue-400 font-semibold text-xs mb-2">💡 Suggestions</h4>
            <div className="grid grid-cols-3 gap-2">
              {(report.recommendations || []).slice(0, 3).map((r, i) => (
                <div key={i} className="flex items-start gap-1 bg-slate-800/50 rounded p-2">
                  <span className="w-4 h-4 bg-blue-500/20 rounded-full flex items-center justify-center text-blue-400 text-[10px] flex-shrink-0">{i + 1}</span>
                  <span className="text-gray-300 text-[10px] leading-tight">{r}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Question Feedback (Collapsible) */}
          <div className="flex-1 bg-slate-800/60 rounded-xl border border-slate-700/50 flex flex-col min-h-[150px]">
            <button
              onClick={() => setShowFeedback(!showFeedback)}
              className="w-full px-3 py-2 flex items-center justify-between text-left hover:bg-slate-700/30 transition"
            >
              <span className="text-white font-semibold text-xs">📝 Question-by-Question Feedback</span>
              <span className="text-gray-400 text-xs">{showFeedback ? "▲" : "▼"}</span>
            </button>
            
            {showFeedback && (
              <div className="flex-1 overflow-y-auto p-3 pt-0 space-y-3">
                {qaFeedback.length > 0 ? qaFeedback.slice(0, 5).map((qa, i) => (
                  <div key={i} className="bg-slate-700/30 rounded-lg p-2">
                    <p className="text-blue-400 text-[10px] font-medium mb-1">Q{i + 1}: {qa.question.slice(0, 100)}...</p>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="bg-red-500/10 rounded p-1.5 border border-red-500/20">
                        <p className="text-red-400 text-[9px] font-medium mb-0.5">Your Answer:</p>
                        <p className="text-gray-300 text-[10px]">{qa.user_answer.slice(0, 80)}...</p>
                      </div>
                      <div className="bg-green-500/10 rounded p-1.5 border border-green-500/20">
                        <p className="text-green-400 text-[9px] font-medium mb-0.5">Better Answer:</p>
                        <p className="text-gray-300 text-[10px]">
                          {qa.better_answer?.slice(0, 80) || "Provide more detail using STAR method..."}
                        </p>
                      </div>
                    </div>
                  </div>
                )) : (
                  <p className="text-gray-500 text-xs text-center py-4">No Q&A feedback available</p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <p className="text-center text-gray-600 text-[10px] mt-3">AI Interview Bot • {new Date().toLocaleDateString()}</p>
    </div>
  );
}