"use client";

import { useState } from "react";
import { uploadResume } from "@/lib/api";
import { useRouter } from "next/navigation";
import { getUser } from "@/lib/auth";
import { API_URL } from "@/lib/config";

interface ATSCheck {
  name: string;
  passed: boolean;
  message: string;
  priority: "critical" | "warning" | "info";
}

interface SectionScore {
  name: string;
  score: number;
  status: "missing" | "weak" | "good" | "excellent";
  feedback: string;
}

interface AnalysisResult {
  ats_score: number;
  keyword_score: number;
  format_score: number;
  content_score: number;
  sections: SectionScore[];
  ats_checks: ATSCheck[];
  skills_found: string[];
  missing_skills: string[];
  strengths: string[];
  critical_issues: string[];
  improvements: string[];
  experience_level: string;
}

export default function ResumeAnalysis() {
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showJobInput, setShowJobInput] = useState(false);
  const router = useRouter();

  async function handleAnalyze() {
    if (!file) return;

    const user = getUser();
    if (!user) {
      alert("Please login first");
      router.push("/login");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const parsed = await uploadResume(file);
      
      console.log("📄 Upload response:", parsed);  // Debug log

      const response = await fetch(`${API_URL}/api/analyze-resume`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: user.id,
          parsed_resume: parsed,  // Send the whole response, not parsed.parsed_resume
          job_description: jobDescription || null,
        }),
      });

      if (!response.ok) throw new Error("Analysis failed");

      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      console.error("Analysis failed:", err);
      setError("Failed to analyze resume. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  function getScoreColor(score: number) {
    if (score >= 80) return "text-green-400";
    if (score >= 60) return "text-yellow-400";
    return "text-red-400";
  }

  function getScoreBg(score: number) {
    if (score >= 80) return "bg-green-500";
    if (score >= 60) return "bg-yellow-500";
    return "bg-red-500";
  }

  function getScoreLabel(score: number) {
    if (score >= 90) return "Excellent";
    if (score >= 80) return "Good";
    if (score >= 70) return "Fair";
    if (score >= 60) return "Needs Work";
    return "Poor";
  }

  function getStatusColor(status: string) {
    switch (status) {
      case "excellent": return "bg-green-500/20 text-green-400";
      case "good": return "bg-blue-500/20 text-blue-400";
      case "weak": return "bg-yellow-500/20 text-yellow-400";
      case "missing": return "bg-red-500/20 text-red-400";
      default: return "bg-slate-700 text-gray-400";
    }
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">ATS Resume Checker</h1>
        <p className="text-gray-400">
          Check if your resume passes Applicant Tracking Systems used by 99% of companies
        </p>
      </div>

      <div className="grid lg:grid-cols-5 gap-6">
        {/* LEFT: Upload Section */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-slate-800/50 rounded-2xl border border-slate-700/50 p-6">
            <h2 className="text-lg font-bold text-white mb-4">Upload Resume</h2>

            <label className="block cursor-pointer mb-4">
              <input
                type="file"
                accept=".pdf,.doc,.docx"
                onChange={(e) => {
                  setFile(e.target.files?.[0] || null);
                  setAnalysis(null);
                  setError(null);
                }}
                className="hidden"
              />
              <div className={`border-2 border-dashed rounded-xl p-6 text-center transition-all ${
                file ? "border-blue-500 bg-blue-500/10" : "border-slate-600 hover:border-blue-400 hover:bg-slate-700/30"
              }`}>
                {file ? (
                  <div>
                    <span className="text-2xl">📄</span>
                    <p className="text-blue-400 font-medium mt-2">{file.name}</p>
                    <p className="text-xs text-gray-500 mt-1">Click to change</p>
                  </div>
                ) : (
                  <div>
                    <span className="text-2xl">⬆️</span>
                    <p className="text-white font-medium mt-2">Upload Resume</p>
                    <p className="text-xs text-gray-500">PDF, DOC, DOCX</p>
                  </div>
                )}
              </div>
            </label>

            {/* Optional Job Description */}
            <div className="mb-4">
              <button
                onClick={() => setShowJobInput(!showJobInput)}
                className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
              >
                {showJobInput ? "▼" : "▶"} Add job description for keyword matching
              </button>
              
              {showJobInput && (
                <textarea
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste the job description here to check keyword match..."
                  rows={4}
                  className="mt-2 w-full px-3 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                />
              )}
            </div>

            <button
              onClick={handleAnalyze}
              disabled={!file || loading}
              className={`w-full py-3 rounded-xl font-semibold transition-all ${
                file && !loading
                  ? "bg-blue-600 text-white hover:bg-blue-700"
                  : "bg-slate-700 text-gray-500 cursor-not-allowed"
              }`}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Scanning...
                </span>
              ) : (
                "Check ATS Score"
              )}
            </button>

            {error && (
              <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                {error}
              </div>
            )}
          </div>

          {/* Score Breakdown */}
          {analysis && (
            <div className="bg-slate-800/50 rounded-2xl border border-slate-700/50 p-6">
              <h3 className="font-bold text-white mb-4">Score Breakdown</h3>
              
              <div className="space-y-3">
                {[
                  { label: "Keywords", score: analysis.keyword_score, weight: "40%" },
                  { label: "Format", score: analysis.format_score, weight: "35%" },
                  { label: "Content", score: analysis.content_score, weight: "25%" },
                ].map((item) => (
                  <div key={item.label}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-400">{item.label} <span className="text-gray-500">({item.weight})</span></span>
                      <span className={`font-semibold ${getScoreColor(item.score)}`}>{item.score}%</span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${getScoreBg(item.score)}`}
                        style={{ width: `${item.score}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Experience Level */}
              <div className="mt-4 pt-4 border-t border-slate-700">
                <p className="text-sm text-gray-500">Detected Level</p>
                <p className="font-semibold text-white">{analysis.experience_level}</p>
              </div>
            </div>
          )}
        </div>

        {/* RIGHT: Results */}
        <div className="lg:col-span-3">
          {!analysis ? (
            <div className="bg-slate-800/50 rounded-2xl border border-slate-700/50 p-12 text-center">
              <div className="text-6xl mb-4">📋</div>
              <h3 className="text-xl font-bold text-white mb-2">No Analysis Yet</h3>
              <p className="text-gray-400">Upload your resume to check ATS compatibility</p>
              
              <div className="mt-8 text-left max-w-md mx-auto">
                <p className="text-sm font-semibold text-gray-300 mb-3">We check for:</p>
                <div className="grid grid-cols-2 gap-2 text-sm text-gray-400">
                  {["Keyword Match", "Contact Info", "Work Experience", "Education Section", "Skills Section", "Formatting", "Measurable Results", "Action Verbs"].map((item) => (
                    <div key={item} className="flex items-center gap-2">
                      <span className="text-blue-400">✓</span> {item}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Main Score */}
              <div className="bg-slate-800/50 rounded-2xl border border-slate-700/50 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400 mb-1">ATS Compatibility Score</p>
                    <div className="flex items-baseline gap-2">
                      <span className={`text-5xl font-bold ${getScoreColor(analysis.ats_score)}`}>
                        {analysis.ats_score}
                      </span>
                      <span className="text-gray-500 text-xl">/100</span>
                    </div>
                    <p className={`text-sm font-medium mt-1 ${getScoreColor(analysis.ats_score)}`}>
                      {getScoreLabel(analysis.ats_score)}
                    </p>
                  </div>
                  
                  <div className={`w-24 h-24 rounded-full flex items-center justify-center ${
                    analysis.ats_score >= 80 ? "bg-green-500/20" : 
                    analysis.ats_score >= 60 ? "bg-yellow-500/20" : "bg-red-500/20"
                  }`}>
                    <span className="text-4xl">
                      {analysis.ats_score >= 80 ? "✅" : analysis.ats_score >= 60 ? "⚠️" : "❌"}
                    </span>
                  </div>
                </div>

                {analysis.ats_score < 80 && (
                  <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                    <p className="text-sm text-yellow-400">
                      <strong>Tip:</strong> Aim for 80+ to pass most ATS filters. Fix critical issues below.
                    </p>
                  </div>
                )}
              </div>

              {/* Critical Issues */}
              {analysis.critical_issues && analysis.critical_issues.length > 0 && (
                <div className="bg-red-500/10 rounded-2xl border border-red-500/30 p-6">
                  <h3 className="font-bold text-red-400 mb-3 flex items-center gap-2">
                    🚨 Critical Issues ({analysis.critical_issues.length})
                  </h3>
                  <ul className="space-y-2">
                    {(analysis.critical_issues || []).map((issue, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-red-300">
                        <span className="mt-0.5">✗</span>
                        <span>{issue}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* ATS Checks */}
              {analysis.ats_checks && analysis.ats_checks.length > 0 && (
                <div className="bg-slate-800/50 rounded-2xl border border-slate-700/50 p-6">
                  <h3 className="font-bold text-white mb-4">ATS Compatibility Checks</h3>
                  <div className="space-y-2">
                    {(analysis.ats_checks || []).map((check, idx) => (
                      <div
                        key={idx}
                        className={`flex items-center justify-between p-3 rounded-lg ${
                          check.passed ? "bg-green-500/10" : 
                          check.priority === "critical" ? "bg-red-500/10" : "bg-yellow-500/10"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <span className={check.passed ? "text-green-400" : "text-red-400"}>
                            {check.passed ? "✓" : "✗"}
                          </span>
                          <div>
                            <p className={`font-medium text-sm ${check.passed ? "text-green-400" : "text-white"}`}>
                              {check.name}
                            </p>
                            {!check.passed && (
                              <p className="text-xs text-gray-400">{check.message}</p>
                            )}
                          </div>
                        </div>
                        {!check.passed && (
                          <span className={`text-xs px-2 py-0.5 rounded ${
                            check.priority === "critical" ? "bg-red-500/20 text-red-400" : "bg-yellow-500/20 text-yellow-400"
                          }`}>
                            {check.priority}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Section Scores */}
              <div className="bg-slate-800/50 rounded-2xl border border-slate-700/50 p-6">
                <h3 className="font-bold text-white mb-4">Resume Sections</h3>
                <div className="space-y-3">
                  {(analysis.sections || []).map((section, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-white">{section.name}</span>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(section.status)}`}>
                            {section.status}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">{section.feedback}</p>
                      </div>
                      <span className={`font-bold ${getScoreColor(section.score)}`}>
                        {section.score}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Skills */}
              <div className="grid md:grid-cols-2 gap-4">
                {/* Found Skills */}
                <div className="bg-slate-800/50 rounded-2xl border border-slate-700/50 p-6">
                  <h3 className="font-bold text-white mb-3">
                    Skills Detected ({analysis.skills_found?.length || 0})
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {analysis.skills_found?.slice(0, 15).map((skill, idx) => (
                      <span key={idx} className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs font-medium">
                        {skill}
                      </span>
                    ))}
                    {(analysis.skills_found?.length || 0) > 15 && (
                      <span className="px-2 py-1 bg-slate-700 text-gray-400 rounded text-xs">
                        +{analysis.skills_found.length - 15} more
                      </span>
                    )}
                  </div>
                </div>

                {/* Missing Skills */}
                <div className="bg-slate-800/50 rounded-2xl border border-slate-700/50 p-6">
                  <h3 className="font-bold text-white mb-3">
                    Recommended to Add
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {analysis.missing_skills?.map((skill, idx) => (
                      <span key={idx} className="px-2 py-1 bg-orange-500/20 text-orange-400 rounded text-xs font-medium">
                        + {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Improvements */}
              <div className="grid md:grid-cols-2 gap-4">
                {/* Strengths */}
                <div className="bg-green-500/10 rounded-2xl border border-green-500/30 p-6">
                  <h3 className="font-bold text-green-400 mb-3">✓ Strengths</h3>
                  <ul className="space-y-2">
                    {analysis.strengths?.map((item, idx) => (
                      <li key={idx} className="text-sm text-green-300 flex items-start gap-2">
                        <span>•</span> {item}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* To Improve */}
                <div className="bg-yellow-500/10 rounded-2xl border border-yellow-500/30 p-6">
                  <h3 className="font-bold text-yellow-400 mb-3">⚡ Quick Fixes</h3>
                  <ul className="space-y-2">
                    {analysis.improvements?.map((item, idx) => (
                      <li key={idx} className="text-sm text-yellow-300 flex items-start gap-2">
                        <span>•</span> {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      
    </div>
  );
}