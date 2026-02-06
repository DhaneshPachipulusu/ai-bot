"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { API_URL } from "@/lib/config";
import Link from "next/link";

/* =======================
   Types
======================= */

interface QAFeedback {
  question: string;
  user_answer: string;
  better_answer?: string;
  score?: number;
}

interface Scores {
  communication: number;
  technical: number;
  problem_solving: number;
  clarity: number;
  confidence: number;
  pace: number;
}

interface ReportData {
  overall_score: number;
  scores: Scores;
  strengths: string[];
  improvements: string[];
  suggestions: string[];
  job_readiness: string;
  analysis_mode?: "ai" | "rule_based";
  qa_feedback: QAFeedback[];
}

/* =======================
   Helpers
======================= */

const getColor = (s: number) =>
  s >= 7 ? "#22c55e" : s >= 5 ? "#eab308" : "#ef4444";

const getReadinessInfo = (score: number) => {
  if (score >= 8) return { level: "High", color: "text-green-400", bg: "bg-green-500/15" };
  if (score >= 6.5) return { level: "Moderate", color: "text-yellow-400", bg: "bg-yellow-500/15" };
  if (score >= 5) return { level: "Developing", color: "text-orange-400", bg: "bg-orange-500/15" };
  return { level: "Needs Practice", color: "text-red-400", bg: "bg-red-500/15" };
};

/* =======================
   Small Components
======================= */

function AnswerBadge({ score }: { score?: number }) {
  if (score === undefined) return null;
  if (score >= 7) return <span className="text-green-400 text-xs">🟢 Strong</span>;
  if (score >= 5) return <span className="text-yellow-400 text-xs">🟡 Good</span>;
  return <span className="text-red-400 text-xs">🔴 Improve</span>;
}

// Score Cards Component (Right side of top row)
function ScoreCards({ scores }: { scores: Scores }) {
  const items = [
    { label: "Communication", value: scores.communication, icon: "💬" },
    { label: "Technical", value: scores.technical, icon: "⚙️" },
    { label: "Problem Solving", value: scores.problem_solving, icon: "🧩" },
    { label: "Clarity", value: scores.clarity, icon: "✨" },
    { label: "Confidence", value: scores.confidence, icon: "💪" },
    { label: "Pace", value: scores.pace, icon: "⏱️" },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
      {items.map((s, i) => (
        <div
          key={i}
          className="bg-slate-700/50 rounded-lg p-2.5 text-center border border-slate-600/50"
        >
          <div className="text-sm mb-0.5">{s.icon}</div>
          <div className="text-[9px] text-gray-400 uppercase tracking-wide">{s.label}</div>
          <div className="text-lg font-bold" style={{ color: getColor(s.value) }}>
            {s.value}<span className="text-[10px] text-gray-500">/10</span>
          </div>
        </div>
      ))}
    </div>
  );
}

// Collapsible Section Component
function CollapsibleSection({
  title,
  items,
  color,
  defaultOpen = false,
  priority = false,
  hint
}: {
  title: string;
  items: string[];
  color: string;
  defaultOpen?: boolean;
  priority?: boolean;
  hint?: string;
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  if (items.length === 0) return null;

  const colorClasses: Record<string, { bg: string; border: string; text: string }> = {
    red: { bg: "bg-red-500/10", border: "border-red-500/30", text: "text-red-400" },
    yellow: { bg: "bg-yellow-500/10", border: "border-yellow-500/20", text: "text-yellow-400" },
    blue: { bg: "bg-blue-500/10", border: "border-blue-500/20", text: "text-blue-400" },
    green: { bg: "bg-green-500/10", border: "border-green-500/20", text: "text-green-400" },
  };

  const colors = colorClasses[color] || colorClasses.blue;

  return (
    <div className={`${colors.bg} border ${colors.border} rounded-xl overflow-hidden ${priority ? 'ring-1 ring-red-500/30' : ''}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3 py-2.5 flex items-center justify-between text-left hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-2">
          <h4 className={`${colors.text} text-xs font-semibold`}>{title}</h4>
          {hint && <span className="text-[10px] text-gray-500 bg-slate-700/50 px-1.5 py-0.5 rounded">{hint}</span>}
        </div>
        <span className={`text-xs ${colors.text}`}>{isOpen ? "▲" : "▼"}</span>
      </button>

      {isOpen && (
        <div className="px-3 pb-3">
          <ul className="text-xs text-gray-300 space-y-1">
            {items.map((item, idx) => (
              <li key={idx}>• {item}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// Collapsible QA Item Component
function QAItem({ qa, index }: { qa: QAFeedback; index: number }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="bg-slate-700/40 rounded-lg border border-slate-600/30 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-3 flex items-start justify-between gap-3 text-left hover:bg-slate-700/50 transition-colors"
      >
        <div className="flex items-start gap-2 flex-1 min-w-0">
          <span className="shrink-0 bg-blue-500/20 text-blue-400 text-xs font-bold px-2 py-1 rounded">
            Q{index + 1}
          </span>
          <p className="text-gray-200 text-sm leading-relaxed line-clamp-2">{qa.question}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <AnswerBadge score={qa.score} />
          <span className="text-gray-500 text-xs">{isExpanded ? "▲" : "▼"}</span>
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 space-y-3">
          <div className="bg-slate-800/50 rounded-lg p-3 border-l-2 border-blue-500/50">
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Your Answer</p>
            <p className="text-gray-300 text-sm leading-relaxed">
              {qa.user_answer || <span className="text-gray-500 italic">No answer recorded</span>}
            </p>
          </div>

          {qa.better_answer && (
            <div className="bg-green-500/5 rounded-lg p-3 border-l-2 border-green-500/50">
              <p className="text-xs text-green-500 uppercase tracking-wide mb-1">💡 Suggested Improvement</p>
              <p className="text-gray-300 text-sm leading-relaxed">{qa.better_answer}</p>
            </div>
          )}

          {qa.score && qa.score >= 7 && !qa.better_answer && (
            <div className="bg-green-500/10 rounded-lg p-3 border-l-2 border-green-500">
              <p className="text-green-400 text-sm">✔ Strong answer!</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* =======================
   Radar Chart
======================= */

function RadarChart({ scores }: { scores: Scores }) {
  const metrics = [
    { label: "Comm.", value: scores.communication },
    { label: "Tech", value: scores.technical },
    { label: "Problem", value: scores.problem_solving },
    { label: "Clarity", value: scores.clarity },
    { label: "Confid.", value: scores.confidence },
    { label: "Pace", value: scores.pace },
  ];

  const size = 180;
  const center = size / 2;
  const radius = 65;
  const angleStep = (2 * Math.PI) / metrics.length;
  const startAngle = -Math.PI / 2;

  const points = metrics.map((m, i) => {
    const angle = startAngle + i * angleStep;
    const r = (m.value / 10) * radius;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
      lx: center + (radius + 18) * Math.cos(angle),
      ly: center + (radius + 18) * Math.sin(angle),
      label: m.label,
      value: m.value,
    };
  });

  return (
    <svg width={size} height={size} className="mx-auto">
      {[...Array(5)].map((_, i) => {
        const r = ((i + 1) / 5) * radius;
        const level = metrics
          .map((_, j) => {
            const a = startAngle + j * angleStep;
            return `${center + r * Math.cos(a)},${center + r * Math.sin(a)}`;
          })
          .join(" ");
        return <polygon key={i} points={level} fill="none" stroke="#334155" />;
      })}

      {metrics.map((_, i) => {
        const a = startAngle + i * angleStep;
        return (
          <line
            key={i}
            x1={center}
            y1={center}
            x2={center + radius * Math.cos(a)}
            y2={center + radius * Math.sin(a)}
            stroke="#334155"
          />
        );
      })}

      <polygon
        points={points.map(p => `${p.x},${p.y}`).join(" ")}
        fill="rgba(59,130,246,0.3)"
        stroke="#3b82f6"
        strokeWidth="2"
      />

      {points.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r="3" fill={getColor(p.value)} />
      ))}

      {points.map((p, i) => (
        <text
          key={i}
          x={p.lx}
          y={p.ly}
          textAnchor="middle"
          className="fill-gray-400 text-[9px]"
        >
          {p.label}
        </text>
      ))}
    </svg>
  );
}

/* =======================
   Main Page
======================= */

export default function ReportPage() {
  const router = useRouter();
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [showQA, setShowQA] = useState(false);

  useEffect(() => {
    const id = sessionStorage.getItem("interviewId");
    if (!id) {
      router.push("/interview");
      return;
    }

    fetch(`${API_URL}/api/analyze-interview?interview_id=${id}`, {
      method: "POST",
    })
      .then(res => res.json())
      .then(data => {
        setReport(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [router]);

  if (loading) {
    return (
      <div className="h-screen bg-slate-900 flex items-center justify-center text-white">
        Analyzing interview…
      </div>
    );
  }

  if (!report) {
    return (
      <div className="h-screen bg-slate-900 flex items-center justify-center text-red-400">
        Failed to load report
      </div>
    );
  }

  const mustImprove = (report.improvements || []).slice(0, 2);
  const shouldImprove = (report.improvements || []).slice(2, 4);
  const advancedImprove = (report.improvements || []).slice(4);
  const readiness = getReadinessInfo(report.overall_score);

  return (
    <div className="min-h-screen bg-slate-900 p-4 text-white">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-lg font-bold">Interview Report</h1>
        <div className="flex gap-2">
          <Link href="/interview" className="px-3 py-1.5 bg-blue-600 rounded-lg text-xs font-medium hover:bg-blue-500">New Interview</Link>
          <Link href="/reports" className="px-3 py-1.5 bg-slate-700 rounded-lg text-xs font-medium hover:bg-slate-600">All Reports</Link>
        </div>
      </div>

      {/* ==========================================
          TOP SECTION: Performance Overview
      ========================================== */}
      <div className="bg-slate-800/60 rounded-xl p-4 mb-4 border border-slate-700/50">
        {/* Radar + Score Cards Side-by-Side */}
        <div className="grid lg:grid-cols-2 gap-4 items-center">
          {/* Left: Radar Chart */}
          <div className="flex justify-center">
            <RadarChart scores={report.scores} />
          </div>

          {/* Right: Score Cards */}
          <div>
            <ScoreCards scores={report.scores} />
          </div>
        </div>

        {/* Overall Score & Readiness */}
        <div className="mt-4 pt-4 border-t border-slate-700/50 flex flex-col sm:flex-row items-center justify-center gap-4">
          <div className="text-center">
            <div className="text-4xl font-bold">
              {report.overall_score.toFixed(1)}
              <span className="text-lg text-gray-400"> /10</span>
            </div>
            <p className="text-xs text-gray-500 mt-1">Overall Score</p>
          </div>

          <div className="hidden sm:block w-px h-12 bg-slate-700"></div>

          <div className="text-center">
            <div className={`inline-block px-4 py-1.5 rounded-full text-sm font-medium ${readiness.bg} ${readiness.color}`}>
              Interview Readiness: {readiness.level}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {report.analysis_mode === "ai" ? "🧠 AI-assisted evaluation" : "⚙️ Rule-based"}
            </p>
          </div>
        </div>
      </div>

      {/* ==========================================
          MIDDLE SECTION: Strengths vs Must Improve
      ========================================== */}
      <div className="grid md:grid-cols-2 gap-4 mb-4">
        {/* Strengths - Calm styling */}
        <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-4">
          <h4 className="text-green-400 text-sm font-semibold mb-3 flex items-center gap-2">
            <span>✓</span> Strengths
          </h4>
          <ul className="text-sm text-gray-300 space-y-2">
            {(report.strengths || []).slice(0, 5).map((s, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-green-400 mt-0.5">•</span>
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Must Improve - Emphasized styling */}
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 ring-1 ring-red-500/20">
          <h4 className="text-red-400 text-sm font-semibold mb-3 flex items-center gap-2">
            <span>🔴</span> Must Improve
            <span className="text-[10px] text-gray-500 bg-slate-700/50 px-2 py-0.5 rounded ml-auto">Focus here first</span>
          </h4>
          {mustImprove.length > 0 ? (
            <ul className="text-sm text-gray-300 space-y-2">
              {mustImprove.map((s, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-red-400 mt-0.5">•</span>
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">Great job! No critical areas to improve.</p>
          )}
        </div>
      </div>

      {/* ==========================================
          BOTTOM SECTION: Secondary & Deep-Dive
      ========================================== */}
      <div className="space-y-3">
        {/* Should Improve - Collapsed */}
        <CollapsibleSection
          title="🟡 Should Improve"
          items={shouldImprove}
          color="yellow"
          defaultOpen={false}
        />

        {/* Advanced - Collapsed */}
        <CollapsibleSection
          title="🔵 Advanced"
          items={advancedImprove}
          color="blue"
          defaultOpen={false}
        />

        {/* Suggestions - Collapsed */}
        <CollapsibleSection
          title="💡 Suggestions"
          items={report.suggestions || []}
          color="blue"
          defaultOpen={false}
        />

        {/* Question-by-Question Feedback - Collapsed */}
        <div className="bg-slate-800/60 rounded-xl border border-slate-700">
          <button
            className="w-full px-4 py-3 flex justify-between items-center text-sm font-medium hover:bg-slate-700/30 transition-colors rounded-t-xl"
            onClick={() => setShowQA(!showQA)}
          >
            <span>📝 Question-by-Question Feedback ({(report.qa_feedback || []).length} questions)</span>
            <span className="text-gray-400">{showQA ? "▲" : "▼"}</span>
          </button>

          {showQA && (
            <div className="p-4 space-y-3 max-h-[500px] overflow-y-auto">
              <p className="text-xs text-gray-500 mb-2">Click a question to expand details</p>
              {(report.qa_feedback || []).map((qa, i) => (
                <QAItem key={i} qa={qa} index={i} />
              ))}
            </div>
          )}
        </div>
      </div>

      <p className="text-center text-gray-600 text-[10px] mt-6">
        AI Interview Bot • {new Date().toLocaleDateString()}
      </p>
    </div>
  );
}
