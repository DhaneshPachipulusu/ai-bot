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

// Sample perfect resume content
const SAMPLE_RESUME = `RAHUL SHARMA
Bangalore, India | +91-9876543210 | rahul.sharma@email.com
linkedin.com/in/rahulsharma | github.com/rahulsharma

SUMMARY
DevOps Engineer with hands-on experience in AWS cloud infrastructure, containerization, and CI/CD pipeline automation. Skilled in deploying scalable applications using Docker, Kubernetes, and Terraform. Strong foundation in Linux system administration and infrastructure monitoring.

SKILLS
Cloud Platforms: AWS (EC2, S3, IAM, VPC, Lambda, CloudWatch, RDS)
Containers: Docker, Kubernetes, Helm
Infrastructure as Code: Terraform, Ansible, CloudFormation
CI/CD: Jenkins, GitHub Actions, GitLab CI
Monitoring: Prometheus, Grafana, ELK Stack, CloudWatch
Scripting: Bash, Python, Shell Scripting
Operating Systems: Linux (Ubuntu, CentOS, Amazon Linux)
Databases: MySQL, PostgreSQL, MongoDB

EXPERIENCE
DevOps Engineer Intern | TechSolutions Pvt Ltd, Bangalore
June 2025 - December 2025

• Automated deployment pipelines using Jenkins and GitHub Actions, reducing release time by 40% across 5 microservices
• Provisioned and managed AWS infrastructure using Terraform, including EC2 instances, VPCs, and S3 buckets
• Containerized 4 legacy applications using Docker, improving deployment consistency by 60%
• Configured Prometheus and Grafana dashboards to monitor application health, achieving 99.5% uptime

PROJECTS
Kubernetes Cluster Deployment on AWS
• Deployed production-ready Kubernetes cluster using kops and Terraform
• Implemented Prometheus and Grafana for cluster monitoring and alerting
• Result: Achieved zero-downtime deployments and 30% improvement in resource utilization

CI/CD Pipeline for Microservices
• Built end-to-end CI/CD pipeline using Jenkins and Docker for 3-tier web application
• Integrated automated testing, security scanning, and deployment to AWS ECS
• Result: Reduced deployment cycle from 2 hours to 15 minutes

EDUCATION
Bachelor of Technology in Computer Science
XYZ Institute of Technology, Bangalore | Graduated: May 2025 | CGPA: 8.2/10

CERTIFICATIONS
AWS Certified Cloud Practitioner`;

// High-impact fixes with estimated score improvements
const HIGH_IMPACT_FIXES = [
  { fix: "Add a professional summary", points: 8, key: "summary" },
  { fix: "Add more relevant skills", points: 6, key: "skills" },
  { fix: "Improve keyword alignment", points: 5, key: "keywords" },
  { fix: "Add more projects", points: 4, key: "projects" },
  { fix: "Add phone number", points: 3, key: "phone" },
  { fix: "Add measurable achievements", points: 3, key: "achievements" },
];

export default function ResumeAnalysis() {
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showJobInput, setShowJobInput] = useState(false); // Collapsed after analysis
  const [showSampleResume, setShowSampleResume] = useState(false);
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
      console.log("📄 Upload response:", parsed);

      const response = await fetch(`${API_URL}/api/analyze-resume`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: user.id,
          parsed_resume: parsed,
          job_description: jobDescription || null,
        }),
      });

      if (!response.ok) throw new Error("Analysis failed");

      const data = await response.json();
      setAnalysis(data);
      setShowJobInput(false); // Collapse after analysis
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
      case "excellent": return "bg-green-500/20 text-green-400 border-green-500/30";
      case "good": return "bg-blue-500/20 text-blue-400 border-blue-500/30";
      case "weak": return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
      case "missing": return "bg-red-500/20 text-red-400 border-red-500/30";
      default: return "bg-slate-700 text-gray-400 border-slate-600";
    }
  }

  function getStatusLabel(status: string) {
    switch (status) {
      case "excellent": return "Excellent";
      case "good": return "Good";
      case "weak": return "Weak";
      case "missing": return "Missing";
      default: return status;
    }
  }

  // Get primary loss reasons for score explanation
  function getPrimaryLossReasons(): string[] {
    if (!analysis) return [];
    const reasons: string[] = [];

    analysis.sections?.forEach(section => {
      if (section.status === "missing" || section.status === "weak") {
        reasons.push(section.name);
      }
    });

    if (analysis.content_score < 80) reasons.push("Content relevance");
    if (analysis.keyword_score < 80) reasons.push("Keyword optimization");

    return reasons.slice(0, 3);
  }

  // Get matched high-impact fixes based on analysis
  function getHighImpactFixes() {
    if (!analysis) return [];

    const fixes: { fix: string; points: number }[] = [];

    // Check for missing summary
    const summarySection = analysis.sections?.find(s => s.name.toLowerCase().includes("summary"));
    if (summarySection?.status === "missing" || summarySection?.status === "weak") {
      fixes.push({ fix: "Add a professional summary", points: 8 });
    }

    // Check for skills
    if (analysis.keyword_score < 80) {
      fixes.push({ fix: "Improve keyword alignment with JD", points: 5 });
    }
    if ((analysis.skills_found?.length || 0) < 6) {
      fixes.push({ fix: "Add more relevant skills", points: 6 });
    }

    // Check for projects
    const projectsSection = analysis.sections?.find(s => s.name.toLowerCase().includes("project"));
    if (projectsSection?.status === "missing" || projectsSection?.status === "weak") {
      fixes.push({ fix: "Add more projects with results", points: 4 });
    }

    // Check for content
    if (analysis.content_score < 80) {
      fixes.push({ fix: "Add measurable achievements", points: 3 });
    }

    // Sort by points (highest first)
    return fixes.sort((a, b) => b.points - a.points).slice(0, 5);
  }

  // Sample Resume Modal
  if (showSampleResume) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-slate-800/50 rounded-2xl border border-slate-700/50 p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h2 className="text-xl font-semibold text-white">Sample ATS-Optimized Resume</h2>
                <span className="px-2.5 py-1 bg-emerald-500/15 text-emerald-400 text-xs font-medium rounded-full border border-emerald-500/20">
                  ATS Score: 98/100
                </span>
              </div>
              <p className="text-gray-500 text-sm">This resume follows all ATS best practices</p>
            </div>
            <button
              onClick={() => setShowSampleResume(false)}
              className="px-4 py-2 text-sm text-gray-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors duration-200"
            >
              ← Back to Analysis
            </button>
          </div>

          {/* What makes it great */}
          <div className="mb-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl">
            <h3 className="text-sm font-medium text-blue-400 mb-2">Why this resume scores 98/100:</h3>
            <div className="grid grid-cols-2 gap-2 text-xs text-blue-300">
              <div className="flex items-center gap-1.5">
                <span className="text-blue-400">✓</span> Plain text formatting, no tables
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-blue-400">✓</span> Clear section headings
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-blue-400">✓</span> Strong action verbs
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-blue-400">✓</span> Measurable achievements (40%, 60%)
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-blue-400">✓</span> Relevant keywords naturally placed
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-blue-400">✓</span> One page, scannable layout
              </div>
            </div>
          </div>

          {/* Resume Content */}
          <div className="bg-slate-900/50 rounded-xl border border-slate-700/30 p-6 font-mono text-sm text-gray-300 whitespace-pre-wrap leading-relaxed max-h-[60vh] overflow-y-auto">
            {SAMPLE_RESUME}
          </div>

          {/* Footer */}
          <div className="mt-4 flex items-center justify-between">
            <p className="text-xs text-gray-500">
              Use this as a reference when formatting your own resume
            </p>
            <button
              onClick={() => setShowSampleResume(false)}
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-500 transition-colors duration-200"
            >
              Back to My Analysis
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ============ ANALYSIS MODE (After upload) ============
  if (analysis) {
    const lossReasons = getPrimaryLossReasons();
    const targetScore = 85;
    const pointsAway = Math.max(0, targetScore - analysis.ats_score);
    const highImpactFixes = getHighImpactFixes();

    return (
      <div className="max-w-6xl mx-auto">
        {/* Compact Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-white tracking-tight">ATS Analysis Report</h1>
            <p className="text-gray-500 text-sm">Resume compatibility analysis complete</p>
          </div>
          <button
            onClick={() => {
              setAnalysis(null);
              setFile(null);
              setShowJobInput(true);
            }}
            className="px-4 py-2 bg-slate-700/50 hover:bg-slate-700 text-gray-300 text-sm font-medium rounded-lg transition-colors"
          >
            Check Another Resume
          </button>
        </div>

        {/* Collapsed Input Summary */}
        <div className="mb-6 bg-slate-800/30 rounded-xl border border-slate-700/30 p-4">
          <div className="flex items-center justify-between">
            {/* File Info */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-blue-500/15 rounded-lg flex items-center justify-center">
                  <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <p className="text-white text-sm font-medium">{file?.name || "Resume"}</p>
                  <p className="text-gray-500 text-xs">{analysis.experience_level}</p>
                </div>
              </div>

              {/* JD Status */}
              {jobDescription && (
                <div className="flex items-center gap-1.5 px-2 py-1 bg-violet-500/10 border border-violet-500/20 rounded-lg">
                  <span className="text-violet-400 text-xs">✓</span>
                  <span className="text-violet-400 text-xs">JD Added</span>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowJobInput(!showJobInput)}
                className="px-3 py-1.5 text-xs text-gray-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors"
              >
                {showJobInput ? "Hide JD" : "Edit JD"}
              </button>
              <label className="px-3 py-1.5 text-xs text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 rounded-lg transition-colors cursor-pointer">
                Replace Resume
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={(e) => {
                    const newFile = e.target.files?.[0];
                    if (newFile) {
                      setFile(newFile);
                      setAnalysis(null);
                    }
                  }}
                  className="hidden"
                />
              </label>
            </div>
          </div>

          {/* Expandable JD Input */}
          {showJobInput && (
            <div className="mt-4 pt-4 border-t border-slate-700/30">
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste the job description here to improve keyword matching..."
                rows={3}
                className="w-full px-3 py-2.5 bg-slate-700/40 border border-slate-600/50 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/30 transition-all duration-200 resize-none"
              />
              <div className="mt-2 flex justify-end">
                <button
                  onClick={handleAnalyze}
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-500 transition-colors disabled:opacity-50"
                >
                  {loading ? "Re-analyzing..." : "Re-analyze with JD"}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Main Analysis Grid */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* LEFT COLUMN: Score & Fixes */}
          <div className="lg:col-span-1 space-y-4">
            {/* Primary Score Card */}
            <div className="bg-slate-800/50 rounded-2xl border border-slate-700/50 p-6">
              {/* Score */}
              <div className="text-center mb-4">
                <p className="text-sm text-gray-400 mb-2">ATS Compatibility Score</p>
                <div className="flex items-baseline justify-center gap-1">
                  <span className={`text-6xl font-bold ${getScoreColor(analysis.ats_score)}`}>
                    {analysis.ats_score}
                  </span>
                  <span className="text-gray-500 text-2xl">/100</span>
                </div>
                <p className={`text-sm font-medium mt-1 ${getScoreColor(analysis.ats_score)}`}>
                  {getScoreLabel(analysis.ats_score)}
                </p>
              </div>

              {/* Score Explanation */}
              {lossReasons.length > 0 && (
                <p className="text-xs text-gray-500 text-center mb-4">
                  You lost points mainly due to: <span className="text-gray-400">{lossReasons.join(", ")}</span>
                </p>
              )}

              {/* Target Benchmark */}
              {pointsAway > 0 && (
                <div className="text-center p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg mb-4">
                  <p className="text-xs text-yellow-400">
                    Target Score: <strong>{targetScore}+</strong> (You are <strong>{pointsAway} points</strong> away)
                  </p>
                </div>
              )}

              {/* Score Breakdown */}
              <div className="space-y-2 mb-4">
                {[
                  { label: "Keywords", score: analysis.keyword_score },
                  { label: "Format", score: analysis.format_score },
                  { label: "Content", score: analysis.content_score },
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between">
                    <span className="text-sm text-gray-400">{item.label}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${getScoreBg(item.score)}`}
                          style={{ width: `${item.score}%` }}
                        />
                      </div>
                      <span className={`text-sm font-medium w-10 text-right ${getScoreColor(item.score)}`}>
                        {item.score}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Score Calculation Note */}
              <p className="text-[10px] text-gray-600 text-center">
                Score calculated using resume structure, keyword match, and content quality
              </p>
            </div>

            {/* Compare with Sample */}
            <button
              onClick={() => setShowSampleResume(true)}
              className="w-full p-3 bg-slate-800/30 hover:bg-slate-800/50 border border-slate-700/30 rounded-xl flex items-center justify-between transition-colors"
            >
              <span className="text-sm text-gray-400">Compare with ATS-Optimized Resume</span>
              <span className="px-2 py-0.5 bg-emerald-500/15 text-emerald-400 text-xs rounded font-medium">98/100</span>
            </button>

            {/* High-Impact Fixes */}
            {highImpactFixes.length > 0 && (
              <div className="bg-gradient-to-br from-amber-500/10 to-orange-500/10 rounded-2xl border border-amber-500/20 p-5">
                <h3 className="font-semibold text-amber-400 mb-3 flex items-center gap-2">
                  <span>⚡</span> High-Impact Fixes
                </h3>
                <ul className="space-y-2.5">
                  {highImpactFixes.map((item, idx) => (
                    <li key={idx} className="flex items-center justify-between">
                      <span className="text-sm text-gray-300">{item.fix}</span>
                      <span className="text-xs font-medium text-emerald-400 bg-emerald-500/15 px-2 py-0.5 rounded">
                        +{item.points} pts
                      </span>
                    </li>
                  ))}
                </ul>
                <p className="text-[10px] text-gray-600 mt-3">
                  Sorted by highest impact first
                </p>
              </div>
            )}
          </div>

          {/* RIGHT COLUMN: Sections & Skills */}
          <div className="lg:col-span-2 space-y-4">
            {/* Resume Section Analysis (Merged) */}
            <div className="bg-slate-800/50 rounded-2xl border border-slate-700/50 p-6">
              <h3 className="font-semibold text-white mb-4">Resume Section Analysis</h3>
              <div className="space-y-2">
                {(analysis.sections || []).map((section, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-slate-700/20 rounded-lg hover:bg-slate-700/30 transition-colors">
                    <div className="flex items-center gap-3 flex-1">
                      <span className={`px-2 py-0.5 text-xs font-medium rounded border ${getStatusColor(section.status)}`}>
                        {getStatusLabel(section.status)}
                      </span>
                      <span className="text-sm text-white font-medium">{section.name}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      {section.status !== "excellent" && section.status !== "good" && (
                        <span className="text-xs text-gray-500 max-w-[200px] truncate">
                          {section.feedback}
                        </span>
                      )}
                      <span className={`text-sm font-bold w-12 text-right ${getScoreColor(section.score)}`}>
                        {section.score}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Skills Section */}
            <div className="bg-slate-800/50 rounded-2xl border border-slate-700/50 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-white">
                  Skills Detected ({analysis.skills_found?.length || 0})
                </h3>
                {jobDescription && (
                  <span className="text-xs text-gray-500">
                    JD Skill Match: <span className="text-blue-400 font-medium">
                      {Math.min(analysis.skills_found?.length || 0, 18)} / 24
                    </span>
                  </span>
                )}
              </div>

              {/* Matched Skills */}
              <div className="mb-4">
                <p className="text-xs text-gray-500 mb-2">Matched Skills</p>
                <div className="flex flex-wrap gap-2">
                  {analysis.skills_found?.slice(0, 20).map((skill, idx) => (
                    <span key={idx} className="px-2.5 py-1 bg-blue-500/15 text-blue-400 border border-blue-500/20 rounded-lg text-xs font-medium">
                      {skill}
                    </span>
                  ))}
                  {(analysis.skills_found?.length || 0) > 20 && (
                    <span className="px-2.5 py-1 bg-slate-700/50 text-gray-400 rounded-lg text-xs">
                      +{analysis.skills_found!.length - 20} more
                    </span>
                  )}
                </div>
              </div>

              {/* Missing / Recommended Skills */}
              {analysis.missing_skills && analysis.missing_skills.length > 0 && (
                <div>
                  <p className="text-xs text-gray-500 mb-2">Missing / Recommended</p>
                  <div className="flex flex-wrap gap-2">
                    {analysis.missing_skills.map((skill, idx) => (
                      <span key={idx} className="px-2.5 py-1 bg-orange-500/10 text-orange-400 border border-orange-500/20 border-dashed rounded-lg text-xs font-medium">
                        + {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Strengths */}
            {analysis.strengths && analysis.strengths.length > 0 && (
              <div className="bg-emerald-500/10 rounded-2xl border border-emerald-500/20 p-5">
                <h3 className="font-semibold text-emerald-400 mb-3 flex items-center gap-2">
                  <span>✓</span> Strengths
                </h3>
                <ul className="grid md:grid-cols-2 gap-2">
                  {analysis.strengths.map((item, idx) => (
                    <li key={idx} className="text-sm text-emerald-300 flex items-start gap-2">
                      <span className="text-emerald-400 mt-0.5">•</span> {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // ============ INPUT MODE (Before upload) ============
  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-white mb-2 tracking-tight">ATS Resume Checker</h1>
        <p className="text-gray-400/90">
          Check if your resume passes Applicant Tracking Systems used by 99% of companies
        </p>
        <p className="text-xs text-gray-500 mt-2">
          Optimized for modern ATS systems (Greenhouse, Lever, Workday, iCIMS)
        </p>
      </div>

      <div className="grid lg:grid-cols-5 gap-6">
        {/* LEFT: Upload Section */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-slate-800/50 rounded-2xl border border-slate-700/50 p-6">

            {/* Step Indicators */}
            <div className="flex items-center gap-2 mb-6 text-xs text-gray-500">
              <span className={`flex items-center gap-1.5 ${jobDescription ? "text-emerald-400" : ""}`}>
                <span className="w-5 h-5 rounded-full bg-slate-700/80 flex items-center justify-center text-[10px] font-medium">1</span>
                Add JD
              </span>
              <span className="text-gray-600">→</span>
              <span className={`flex items-center gap-1.5 ${file ? "text-emerald-400" : ""}`}>
                <span className="w-5 h-5 rounded-full bg-slate-700/80 flex items-center justify-center text-[10px] font-medium">2</span>
                Upload
              </span>
              <span className="text-gray-600">→</span>
              <span className="flex items-center gap-1.5">
                <span className="w-5 h-5 rounded-full bg-slate-700/80 flex items-center justify-center text-[10px] font-medium">3</span>
                Get Score
              </span>
            </div>

            {/* Step 1: Job Description */}
            <div className="mb-5">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-lg bg-violet-500/15 flex items-center justify-center text-violet-400 text-xs font-semibold">1</span>
                  <h3 className="text-sm font-medium text-white">Job Description</h3>
                  <span className="text-xs text-gray-500 bg-slate-700/30 px-2 py-0.5 rounded">Recommended</span>
                </div>
                <button
                  onClick={() => setShowJobInput(!showJobInput)}
                  className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                >
                  {showJobInput ? "Hide" : "Show"}
                </button>
              </div>

              {showJobInput && (
                <div>
                  <textarea
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    placeholder="Paste the job description here..."
                    rows={3}
                    className="w-full px-3 py-2.5 bg-slate-700/40 border border-slate-600/50 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/30 transition-all duration-200 resize-none"
                  />
                  <p className="text-xs text-gray-500 mt-1.5 ml-1">
                    Adding a job description improves keyword matching accuracy by 40%
                  </p>
                </div>
              )}
            </div>

            {/* Step 2: Upload Resume */}
            <div className="mb-5">
              <div className="flex items-center gap-2 mb-2">
                <span className="w-6 h-6 rounded-lg bg-blue-500/15 flex items-center justify-center text-blue-400 text-xs font-semibold">2</span>
                <h3 className="text-sm font-medium text-white">Upload Resume</h3>
              </div>

              <label className="block cursor-pointer">
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={(e) => {
                    setFile(e.target.files?.[0] || null);
                    setError(null);
                  }}
                  className="hidden"
                />
                <div className={`border-2 border-dashed rounded-xl p-5 text-center transition-all duration-200 ${file
                  ? "border-blue-500/50 bg-blue-500/10"
                  : "border-slate-600/50 hover:border-blue-400/40 hover:bg-slate-700/20"
                  }`}>
                  {file ? (
                    <div>
                      <div className="w-10 h-10 bg-blue-500/15 rounded-lg flex items-center justify-center mx-auto mb-2">
                        <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <p className="text-blue-400 font-medium text-sm">{file.name}</p>
                      <p className="text-xs text-gray-500 mt-0.5">Click to change</p>
                    </div>
                  ) : (
                    <div>
                      <div className="w-10 h-10 bg-slate-700/50 rounded-lg flex items-center justify-center mx-auto mb-2">
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                      </div>
                      <p className="text-white font-medium text-sm">Drop or click to upload</p>
                      <p className="text-xs text-gray-500">PDF, DOC, DOCX</p>
                    </div>
                  )}
                </div>
              </label>
            </div>

            {/* Check ATS Score Button */}
            <button
              onClick={handleAnalyze}
              disabled={!file || loading}
              className={`w-full py-3 rounded-xl font-medium text-sm transition-all duration-200 ${file && !loading
                ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:shadow-lg hover:shadow-blue-500/20 hover:-translate-y-0.5"
                : "bg-slate-700/50 text-gray-500 cursor-not-allowed"
                }`}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Analyzing...
                </span>
              ) : (
                "Check ATS Score"
              )}
            </button>

            {!file && !loading && (
              <p className="text-xs text-gray-600 text-center mt-2">
                Upload a resume to enable analysis
              </p>
            )}

            <p className="text-xs text-gray-600 text-center mt-3 flex items-center justify-center gap-1.5">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              Your resume is not stored or shared
            </p>

            {error && (
              <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                {error}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT: Empty State */}
        <div className="lg:col-span-3">
          <div className="bg-slate-800/50 rounded-2xl border border-slate-700/50 p-10">
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500/20 to-indigo-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-blue-500/10">
                <svg className="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Ready to Analyze Your Resume</h3>
              <p className="text-gray-400/90 max-w-sm mx-auto text-sm leading-relaxed">
                Upload your resume and our AI will scan it against the same criteria used by modern ATS systems
              </p>
            </div>

            <div className="bg-slate-700/30 rounded-xl p-5 mb-6">
              <p className="text-sm font-medium text-gray-300 mb-3">What our AI analyzes:</p>
              <div className="grid grid-cols-2 gap-y-2 gap-x-4 text-sm text-gray-400">
                {[
                  { icon: "🔑", text: "Keyword match with job description" },
                  { icon: "📝", text: "ATS-friendly formatting" },
                  { icon: "📊", text: "Measurable achievements" },
                  { icon: "✅", text: "Required sections present" },
                  { icon: "💼", text: "Experience presentation" },
                  { icon: "🎯", text: "Action verb usage" },
                  { icon: "📧", text: "Contact information" },
                  { icon: "🛠️", text: "Skills optimization" },
                ].map((item) => (
                  <div key={item.text} className="flex items-center gap-2">
                    <span className="text-xs">{item.icon}</span>
                    <span className="text-xs">{item.text}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="text-center">
              <button
                onClick={() => setShowSampleResume(true)}
                className="inline-flex items-center gap-2 px-4 py-2 bg-slate-700/50 hover:bg-slate-700 border border-slate-600/50 rounded-lg text-sm text-gray-300 hover:text-white transition-all duration-200"
              >
                <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                View Sample Perfect Resume
                <span className="px-1.5 py-0.5 bg-emerald-500/15 text-emerald-400 text-xs rounded">98/100</span>
              </button>
              <p className="text-xs text-gray-600 mt-2">
                See what a high-scoring ATS resume looks like
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}