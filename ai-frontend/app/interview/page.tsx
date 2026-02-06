"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { getUser } from "@/lib/auth";
import { API_URL } from "@/lib/config";
import dynamic from "next/dynamic";

// Dynamically import ParticleBackground for consistency with dashboard
const ParticleBackground = dynamic(() => import("@/components/ParticleBackground"), {
  ssr: false,
});

export default function InterviewSetupPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [parsedResume, setParsedResume] = useState<any>(null);
  const [uploading, setUploading] = useState(false);
  const [mode, setMode] = useState<"resume" | "career">("resume");
  const [targetRole, setTargetRole] = useState("Software Engineer");
  const [difficulty, setDifficulty] = useState("auto");
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const roles = [
    "Software Engineer",
    "Data Engineer",
    "Data Scientist",
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "DevOps Engineer",
    "Product Manager",
    "Business Analyst",
    "Other"
  ];

  const handleFileSelect = async (selectedFile: File) => {
    if (!selectedFile) return;

    const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!validTypes.includes(selectedFile.type)) {
      setError("Please upload a PDF or DOC/DOCX file");
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setError("File size must be less than 10MB");
      return;
    }

    setFile(selectedFile);
    setError(null);
    setUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch(`${API_URL}/api/upload-resume`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Failed to parse resume");

      const data = await response.json();
      setParsedResume(data);
      setMode("resume");

      if (data.target_role) {
        setTargetRole(data.target_role);
      }
    } catch (err: any) {
      setError(err.message || "Failed to parse resume");
      setFile(null);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) handleFileSelect(droppedFile);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  const removeFile = () => {
    setFile(null);
    setParsedResume(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const startInterview = async () => {
    const user = getUser();
    if (!user) {
      router.push("/login");
      return;
    }

    if (mode === "resume" && !parsedResume) {
      setError("Please upload a resume for resume-based interview");
      return;
    }

    setStarting(true);
    setError(null);

    try {
      if (parsedResume) {
        sessionStorage.setItem("parsed_resume", JSON.stringify(parsedResume));
      } else {
        sessionStorage.removeItem("parsed_resume");
      }
      sessionStorage.setItem("interview_role", targetRole);
      sessionStorage.setItem("interview_difficulty", difficulty);
      sessionStorage.setItem("interview_mode", mode);

      router.push("/interview/live");
    } catch (err: any) {
      setError(err.message || "Failed to start interview");
      setStarting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col relative">
      {/* Particle Background - matches dashboard */}
      <ParticleBackground />

      {/* Header */}
      <header className="px-6 py-5 relative z-10">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center text-white font-semibold text-sm shadow-lg shadow-blue-500/20">
              AI
            </div>
            <div>
              <h1 className="text-base font-semibold text-white tracking-tight">AI Interview</h1>
              <p className="text-xs text-gray-500">Setup Session</p>
            </div>
          </div>
          <button
            onClick={() => router.push("/")}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm text-gray-400 hover:text-white hover:bg-slate-800/80 transition-all duration-200 ease-out group"
          >
            <span className="group-hover:-translate-x-0.5 transition-transform duration-200 ease-out">←</span>
            <span className="font-medium">Back</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-5xl mx-auto px-6 py-6 w-full relative z-10">
        {/* Page Header */}
        <div className="text-center mb-10">
          <h2 className="text-3xl md:text-4xl font-semibold text-white mb-3 tracking-tight">
            Setup Your Session
          </h2>
          <p className="text-gray-400/90 max-w-md mx-auto text-base leading-relaxed">
            Upload a resume for tailored questions, or choose a standard role-based practice.
          </p>
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">

          {/* Left: Resume Upload */}
          <div className="bg-slate-800/40 backdrop-blur-sm rounded-2xl p-7 border border-slate-700/40 relative overflow-hidden transition-all duration-300 ease-out hover:border-slate-600/60">
            {/* Subtle glow */}
            <div className="absolute top-0 right-0 w-48 h-48 bg-blue-500/5 blur-3xl rounded-full -mr-24 -mt-24 pointer-events-none"></div>

            <div className="flex items-center justify-between mb-6">
              <h3 className="text-white font-medium flex items-center gap-3">
                <span className="w-7 h-7 bg-blue-500/15 rounded-lg flex items-center justify-center text-blue-400 text-xs font-semibold">1</span>
                Upload Resume
              </h3>
              <span className="text-xs text-gray-500 bg-slate-700/30 px-2.5 py-1 rounded-md">Optional</span>
            </div>

            {/* Drop Zone */}
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}
              className={`relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-300 ease-out ${dragOver
                ? "border-blue-500/70 bg-blue-500/10"
                : file
                  ? "border-emerald-500/40 bg-emerald-500/5"
                  : "border-slate-600/40 hover:border-blue-400/40 hover:bg-blue-500/5"
                }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.doc,.docx"
                onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                className="hidden"
              />

              {uploading ? (
                <div className="py-4">
                  <div className="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                  <p className="text-blue-300 text-sm font-medium">Analyzing resume...</p>
                </div>
              ) : file ? (
                <div className="py-2">
                  <div className="w-12 h-12 bg-emerald-500/15 rounded-xl flex items-center justify-center mx-auto mb-3 border border-emerald-500/20">
                    <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <p className="text-white font-medium mb-0.5">{file.name}</p>
                  <p className="text-gray-500 text-xs mb-4">{(file.size / 1024).toFixed(1)} KB</p>
                  <button
                    onClick={(e) => { e.stopPropagation(); removeFile(); }}
                    className="text-red-400/80 text-xs hover:text-red-300 px-3 py-1.5 rounded-lg transition-colors duration-200"
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <div className="py-4">
                  <div className="w-14 h-14 bg-slate-700/50 rounded-xl flex items-center justify-center mx-auto mb-4 border border-slate-600/30 transition-transform duration-300 ease-out group-hover:scale-105">
                    <svg className="w-7 h-7 text-blue-400/70" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <p className="text-white font-medium mb-1">Drop your resume here</p>
                  <p className="text-gray-500 text-xs mb-3">PDF, DOC, DOCX • Max 10MB</p>
                  <p className="text-gray-600 text-xs">Your file is processed locally for this session only</p>
                </div>
              )}
            </div>

            {/* Parsed Resume Info */}
            {parsedResume && (
              <div className="mt-5 p-4 bg-slate-800/60 rounded-xl border border-slate-700/40">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full"></div>
                  <p className="text-emerald-400 text-xs font-medium">Resume analyzed</p>
                </div>
                {parsedResume.name && (
                  <p className="text-white text-sm font-medium mb-2">{parsedResume.name}</p>
                )}
                {parsedResume.skills && parsedResume.skills.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {parsedResume.skills.slice(0, 5).map((skill: string, i: number) => (
                      <span key={i} className="px-2 py-0.5 bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs rounded-md">
                        {skill}
                      </span>
                    ))}
                    {parsedResume.skills.length > 5 && (
                      <span className="text-gray-500 text-xs self-center">+{parsedResume.skills.length - 5}</span>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right: Configuration */}
          <div className="bg-slate-800/40 backdrop-blur-sm rounded-2xl p-7 border border-slate-700/40 relative overflow-hidden">
            {/* Subtle glow */}
            <div className="absolute top-0 right-0 w-48 h-48 bg-violet-500/5 blur-3xl rounded-full -mr-24 -mt-24 pointer-events-none"></div>

            <h3 className="text-white font-medium flex items-center gap-3 mb-6">
              <span className="w-7 h-7 bg-violet-500/15 rounded-lg flex items-center justify-center text-violet-400 text-xs font-semibold">2</span>
              Configure Session
            </h3>

            {/* Interview Type */}
            <div className="mb-6">
              <p className="text-gray-400 text-xs font-medium mb-3 uppercase tracking-wider">Interview Type</p>
              <div className="grid grid-cols-2 gap-3">
                {/* Resume Based */}
                <button
                  onClick={() => setMode("resume")}
                  disabled={!parsedResume}
                  className={`p-4 rounded-xl border text-left transition-all duration-200 ease-out relative ${mode === "resume" && parsedResume
                    ? "border-blue-500/50 bg-blue-500/10"
                    : !parsedResume
                      ? "border-slate-700/40 bg-slate-800/30 opacity-50 cursor-not-allowed"
                      : "border-slate-700/40 bg-slate-800/30 hover:border-slate-600 hover:bg-slate-800/50"
                    }`}
                >
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center mb-2.5 transition-colors duration-200 ${mode === "resume" && parsedResume ? "bg-blue-500 text-white" : "bg-slate-700/60 text-slate-400"
                    }`}>
                    <svg className="w-4.5 h-4.5" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <p className="text-white text-sm font-medium mb-0.5">Resume Based</p>
                  <p className="text-gray-500 text-xs">Tailored to your profile</p>
                  {mode === "resume" && parsedResume && (
                    <div className="absolute top-3 right-3 w-2 h-2 bg-blue-500 rounded-full"></div>
                  )}
                </button>

                {/* Career Based */}
                <button
                  onClick={() => setMode("career")}
                  className={`p-4 rounded-xl border text-left transition-all duration-200 ease-out relative ${mode === "career"
                    ? "border-violet-500/50 bg-violet-500/10"
                    : "border-slate-700/40 bg-slate-800/30 hover:border-slate-600 hover:bg-slate-800/50"
                    }`}
                >
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center mb-2.5 transition-colors duration-200 ${mode === "career" ? "bg-violet-500 text-white" : "bg-slate-700/60 text-slate-400"
                    }`}>
                    <svg className="w-4.5 h-4.5" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <p className="text-white text-sm font-medium mb-0.5">Role Based</p>
                  <p className="text-gray-500 text-xs">Standard role questions</p>
                  {mode === "career" && (
                    <div className="absolute top-3 right-3 w-2 h-2 bg-violet-500 rounded-full"></div>
                  )}
                </button>
              </div>
            </div>

            {/* Target Role */}
            <div className="mb-6">
              <label className="text-gray-400 text-xs font-medium mb-2 block uppercase tracking-wider">Target Role</label>
              <div className="relative">
                <select
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-800/60 border border-slate-700/40 rounded-xl text-white text-sm focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/30 appearance-none cursor-pointer transition-all duration-200 ease-out hover:border-slate-600"
                >
                  {roles.map(role => (
                    <option key={role} value={role}>{role}</option>
                  ))}
                </select>
                <div className="absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none text-gray-500">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Difficulty */}
            <div className="mb-8">
              <label className="text-gray-400 text-xs font-medium mb-2 block uppercase tracking-wider">Difficulty</label>
              <div className="bg-slate-800/60 p-1 rounded-xl border border-slate-700/40 flex">
                {[
                  { value: "auto", label: "Auto", hint: "Adjusts to your level" },
                  { value: "easy", label: "Easy" },
                  { value: "medium", label: "Medium" },
                  { value: "hard", label: "Hard" },
                ].map(opt => (
                  <button
                    key={opt.value}
                    onClick={() => setDifficulty(opt.value)}
                    className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all duration-200 ease-out ${difficulty === opt.value
                      ? "bg-slate-700 text-white shadow-sm"
                      : "text-gray-500 hover:text-gray-300"
                      }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
              {difficulty === "auto" && (
                <p className="text-gray-600 text-xs mt-2 ml-1">Difficulty adapts based on your responses</p>
              )}
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-5 p-3 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-2.5">
                <svg className="w-4 h-4 text-red-400 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-red-300 text-xs">{error}</p>
              </div>
            )}

            {/* Start Button */}
            <button
              onClick={startInterview}
              disabled={starting || (mode === "resume" && !parsedResume)}
              className="w-full bg-gradient-to-r from-blue-600 via-blue-500 to-indigo-600 text-white py-3.5 rounded-xl font-medium text-sm flex items-center justify-center gap-2 transition-all duration-300 ease-out shadow-lg shadow-blue-500/20 hover:shadow-xl hover:shadow-blue-500/25 hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 disabled:hover:shadow-lg group relative overflow-hidden"
            >
              {/* Shimmer */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-out"></div>

              <span className="relative">
                {starting ? (
                  <span className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    Starting...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    Start Practice Session
                    <svg className="w-4 h-4 group-hover:translate-x-0.5 transition-transform duration-200 ease-out" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </span>
                )}
              </span>
            </button>

            {/* Hint below CTA */}
            <p className="text-gray-600 text-xs text-center mt-3">
              ~15 min session • You can pause anytime
            </p>
          </div>
        </div>

        {/* Features Footer */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-14 max-w-3xl mx-auto">
          {[
            {
              icon: (
                <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              ),
              title: "Context Aware",
              desc: "Questions adapt in real-time",
              color: "emerald"
            },
            {
              icon: (
                <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              ),
              title: "Voice Mode",
              desc: "Practice speaking naturally",
              color: "blue"
            },
            {
              icon: (
                <svg className="w-5 h-5 text-violet-400" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              ),
              title: "Detailed Reports",
              desc: "Scored feedback after each session",
              color: "violet"
            }
          ].map((feature, i) => (
            <div
              key={i}
              className="bg-slate-800/30 rounded-xl p-5 text-center border border-slate-700/30 transition-all duration-200 ease-out hover:bg-slate-800/40 hover:border-slate-600/40 group"
            >
              <div className={`w-10 h-10 bg-${feature.color}-500/10 rounded-xl flex items-center justify-center mx-auto mb-3 border border-${feature.color}-500/15 transition-transform duration-200 ease-out group-hover:scale-105`}>
                {feature.icon}
              </div>
              <h4 className="text-white text-sm font-medium mb-1">{feature.title}</h4>
              <p className="text-gray-500 text-xs">{feature.desc}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}