"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { getUser } from "@/lib/auth";

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

      const response = await fetch("http://127.0.0.1:8000/api/parse-resume", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Failed to parse resume");

      const data = await response.json();
      setParsedResume(data);
      setMode("resume");
      
      // Auto-detect role from resume if available
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
      // Store data in session
      if (parsedResume) {
        sessionStorage.setItem("parsed_resume", JSON.stringify(parsedResume));
      } else {
        sessionStorage.removeItem("parsed_resume");
      }
      sessionStorage.setItem("interview_role", targetRole);
      sessionStorage.setItem("interview_difficulty", difficulty);
      sessionStorage.setItem("interview_mode", mode);

      // Navigate to interview
      router.push("/interview/live");
    } catch (err: any) {
      setError(err.message || "Failed to start interview");
      setStarting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="px-6 py-4 border-b border-slate-700/50">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center text-white font-bold">
              AI
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">AI Interview</h1>
              <p className="text-xs text-gray-400">Setup your session</p>
            </div>
          </div>
          <button onClick={() => router.push("/")} className="px-4 py-2 text-gray-400 hover:text-white text-sm">
            ← Back to Home
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-white mb-2">Start Your Interview</h2>
          <p className="text-gray-400">Upload your resume or start a career-based interview</p>
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Left: Resume Upload */}
          <div className="bg-slate-800/50 rounded-2xl border border-slate-700/50 p-6">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <span className="w-6 h-6 bg-blue-500/20 rounded-full flex items-center justify-center text-blue-400 text-xs">1</span>
              Upload Resume (Optional)
            </h3>

            {/* Drop Zone */}
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}
              className={`relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                dragOver 
                  ? "border-blue-500 bg-blue-500/10" 
                  : file 
                  ? "border-green-500/50 bg-green-500/5" 
                  : "border-slate-600 hover:border-slate-500 hover:bg-slate-700/30"
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
                  <div className="w-10 h-10 border-3 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
                  <p className="text-gray-400 text-sm">Parsing resume...</p>
                </div>
              ) : file ? (
                <div className="py-2">
                  <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                    <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <p className="text-white font-medium mb-1">{file.name}</p>
                  <p className="text-gray-400 text-xs mb-3">{(file.size / 1024).toFixed(1)} KB</p>
                  <button
                    onClick={(e) => { e.stopPropagation(); removeFile(); }}
                    className="text-red-400 text-xs hover:text-red-300"
                  >
                    Remove file
                  </button>
                </div>
              ) : (
                <div className="py-4">
                  <div className="w-12 h-12 bg-slate-700 rounded-full flex items-center justify-center mx-auto mb-3">
                    <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <p className="text-white font-medium mb-1">Drop your resume here</p>
                  <p className="text-gray-400 text-xs">PDF, DOC, DOCX (max 10MB)</p>
                </div>
              )}
            </div>

            {/* Parsed Resume Info */}
            {parsedResume && (
              <div className="mt-4 p-3 bg-slate-700/30 rounded-lg">
                <p className="text-green-400 text-xs font-medium mb-2">✓ Resume Parsed</p>
                {parsedResume.name && (
                  <p className="text-white text-sm">{parsedResume.name}</p>
                )}
                {parsedResume.skills && parsedResume.skills.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {parsedResume.skills.slice(0, 5).map((skill: string, i: number) => (
                      <span key={i} className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-xs rounded">
                        {skill}
                      </span>
                    ))}
                    {parsedResume.skills.length > 5 && (
                      <span className="text-gray-400 text-xs">+{parsedResume.skills.length - 5} more</span>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right: Mode Selection & Start */}
          <div className="bg-slate-800/50 rounded-2xl border border-slate-700/50 p-6">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <span className="w-6 h-6 bg-blue-500/20 rounded-full flex items-center justify-center text-blue-400 text-xs">2</span>
              Configure Interview
            </h3>

            {/* Mode Selection */}
            <div className="space-y-3 mb-6">
              <p className="text-gray-400 text-sm">Interview Type</p>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => setMode("resume")}
                  disabled={!parsedResume}
                  className={`p-4 rounded-xl border-2 text-left transition-all ${
                    mode === "resume" && parsedResume
                      ? "border-blue-500 bg-blue-500/10"
                      : !parsedResume
                      ? "border-slate-700 bg-slate-800/50 opacity-50 cursor-not-allowed"
                      : "border-slate-700 hover:border-slate-600"
                  }`}
                >
                  <div className="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center mb-2">
                    <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <p className="text-white font-medium text-sm">Resume Based</p>
                  <p className="text-gray-400 text-xs mt-1">Questions from your resume</p>
                </button>

                <button
                  onClick={() => setMode("career")}
                  className={`p-4 rounded-xl border-2 text-left transition-all ${
                    mode === "career"
                      ? "border-purple-500 bg-purple-500/10"
                      : "border-slate-700 hover:border-slate-600"
                  }`}
                >
                  <div className="w-8 h-8 bg-purple-500/20 rounded-lg flex items-center justify-center mb-2">
                    <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <p className="text-white font-medium text-sm">Career Based</p>
                  <p className="text-gray-400 text-xs mt-1">General role questions</p>
                </button>
              </div>
            </div>

            {/* Target Role */}
            <div className="mb-4">
              <p className="text-gray-400 text-sm mb-2">Target Role</p>
              <select
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-700/50 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {roles.map(role => (
                  <option key={role} value={role}>{role}</option>
                ))}
              </select>
            </div>

            {/* Difficulty */}
            <div className="mb-6">
              <p className="text-gray-400 text-sm mb-2">Difficulty</p>
              <div className="flex gap-2">
                {[
                  { value: "auto", label: "Auto" },
                  { value: "easy", label: "Easy" },
                  { value: "medium", label: "Medium" },
                  { value: "hard", label: "Hard" },
                ].map(opt => (
                  <button
                    key={opt.value}
                    onClick={() => setDifficulty(opt.value)}
                    className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
                      difficulty === opt.value
                        ? "bg-blue-600 text-white"
                        : "bg-slate-700/50 text-gray-400 hover:text-white"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            )}

            {/* Start Button */}
            <button
              onClick={startInterview}
              disabled={starting || (mode === "resume" && !parsedResume)}
              className="w-full py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
            >
              {starting ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Starting...
                </>
              ) : (
                <>
                  Start Interview
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </>
              )}
            </button>

            {/* Info */}
            <p className="text-center text-gray-500 text-xs mt-4">
              {mode === "resume" 
                ? "Questions will be based on your resume and experience"
                : "Questions will be based on the selected role"
              }
            </p>
          </div>
        </div>

        {/* Features */}
        <div className="grid grid-cols-3 gap-4 mt-8">
          <div className="bg-slate-800/30 rounded-xl p-4 text-center">
            <div className="w-10 h-10 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
              <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="text-white font-medium text-sm">AI-Powered</p>
            <p className="text-gray-400 text-xs mt-1">Smart questions based on your profile</p>
          </div>
          <div className="bg-slate-800/30 rounded-xl p-4 text-center">
            <div className="w-10 h-10 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
              <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <p className="text-white font-medium text-sm">Instant Feedback</p>
            <p className="text-gray-400 text-xs mt-1">Detailed performance analysis</p>
          </div>
          <div className="bg-slate-800/30 rounded-xl p-4 text-center">
            <div className="w-10 h-10 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
              <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <p className="text-white font-medium text-sm">Track Progress</p>
            <p className="text-gray-400 text-xs mt-1">Monitor improvement over time</p>
          </div>
        </div>
      </main>
    </div>
  );
}