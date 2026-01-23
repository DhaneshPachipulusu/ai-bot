"use client";

import { useState } from "react";
import { uploadResume, generateQuestions } from "@/lib/api";
import { useRouter } from "next/navigation";
import { getUser } from "@/lib/auth";

interface Question {
  type: string;
  topic: string;
  question: string;
}

interface QuestionsData {
  role: string;
  difficulty: string;
  questions: Question[];
}

interface ResumeUploadProps {
  onStartInterview?: () => void;  // Optional callback when starting interview
}

export default function ResumeUpload({ onStartInterview }: ResumeUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [questionsData, setQuestionsData] = useState<QuestionsData | null>(null);
  const router = useRouter();

  // Step 1: Upload resume and generate questions
  async function handleUpload() {
    if (!file) return;

    const user = getUser();
    if (!user) {
      alert("Please login first");
      router.push("/login");
      return;
    }

    setLoading(true);
    try {
      const parsed = await uploadResume(file);
      const questions = await generateQuestions(parsed.parsed_resume);

      // Store questions and show preview (don't navigate yet)
      setQuestionsData(questions);
      sessionStorage.setItem("questions", JSON.stringify(questions));
      sessionStorage.setItem("current_user_id", user.id.toString());
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Failed to upload resume. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  // Step 2: Start the interview
  function handleStartInterview() {
    if (onStartInterview) {
      // Use callback if provided (same page transition)
      onStartInterview();
    } else {
      // Fallback to navigation
      router.push("/interview");
    }
  }

  // Reset to upload another resume
  function handleReset() {
    setFile(null);
    setQuestionsData(null);
    sessionStorage.removeItem("questions");
  }

  // Get badge color based on question type
  function getTypeBadgeColor(type: string) {
    switch (type.toLowerCase()) {
      case "skill":
        return "bg-blue-100 text-blue-700";
      case "project":
        return "bg-green-100 text-green-700";
      case "behavioral":
        return "bg-purple-100 text-purple-700";
      case "scenario":
        return "bg-orange-100 text-orange-700";
      default:
        return "bg-gray-100 text-gray-700";
    }
  }

  // ==========================================
  // STEP 2 UI: Show questions preview
  // ==========================================
  if (questionsData) {
    return (
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl mb-4 shadow-lg">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">
            Questions Generated!
          </h1>
          <p className="text-lg text-gray-600">
            Review your personalized interview questions below
          </p>
        </div>

        {/* Role & Difficulty Badge */}
        <div className="flex items-center justify-center gap-4 mb-8">
          <span className="px-4 py-2 bg-blue-100 text-blue-700 rounded-full font-medium">
            {questionsData.role}
          </span>
          <span className="px-4 py-2 bg-gray-100 text-gray-700 rounded-full font-medium capitalize">
            {questionsData.difficulty} Level
          </span>
        </div>

        {/* Questions Preview */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden mb-6">
          <div className="p-6 border-b border-gray-100">
            <h2 className="text-xl font-bold text-gray-900">
              Interview Questions ({questionsData.questions.length})
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              These questions are tailored to your resume
            </p>
          </div>

          <div className="divide-y divide-gray-100 max-h-96 overflow-y-auto">
            {questionsData.questions.map((q, index) => (
              <div key={index} className="p-5 hover:bg-gray-50 transition-colors">
                <div className="flex items-start gap-4">
                  {/* Question Number */}
                  <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
                    {index + 1}
                  </div>

                  <div className="flex-1 min-w-0">
                    {/* Type & Topic Badges */}
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${getTypeBadgeColor(q.type)}`}>
                        {q.type}
                      </span>
                      <span className="text-xs text-gray-500">
                        {q.topic}
                      </span>
                    </div>

                    {/* Question Text */}
                    <p className="text-gray-800 text-sm leading-relaxed">
                      {q.question}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button
            onClick={handleReset}
            className="flex-1 py-4 rounded-xl font-semibold text-lg border-2 border-gray-200 text-gray-700 hover:bg-gray-50 transition-all"
          >
            ← Upload Different Resume
          </button>

          <button
            onClick={handleStartInterview}
            className="flex-1 py-4 rounded-xl font-semibold text-lg bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all flex items-center justify-center gap-2"
          >
            Start Interview
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </button>
        </div>

        {/* Info Note */}
        <p className="text-center text-sm text-gray-500 mt-6">
          💡 The AI interviewer will ask these questions one by one. You can answer via voice or text.
        </p>
      </div>
    );
  }

  // ==========================================
  // STEP 1 UI: Upload Resume
  // ==========================================
  return (
    <div className="max-w-4xl mx-auto">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
          Ace Your Next Interview
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Upload your resume and practice with AI-powered mock interviews. Get instant feedback and improve your skills.
        </p>
      </div>

      {/* Upload Card */}
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
        <div className="p-8 md:p-12">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl mb-4 shadow-lg">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Upload Your Resume
            </h2>
            <p className="text-gray-600">
              We'll generate personalized interview questions based on your experience
            </p>
          </div>

          {/* Drag & Drop Area */}
          <label className="block cursor-pointer">
            <input
              type="file"
              accept=".pdf,.doc,.docx"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="hidden"
            />
            <div className={`border-2 border-dashed rounded-xl p-12 text-center transition-all ${
              file
                ? "border-blue-500 bg-blue-50"
                : "border-gray-300 hover:border-blue-400 hover:bg-gray-50"
            }`}>
              <svg className="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              
              {file ? (
                <div>
                  <p className="text-blue-700 font-semibold text-lg mb-2">
                    ✓ {file.name}
                  </p>
                  <p className="text-sm text-gray-600">
                    Click to change file
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-gray-700 font-semibold text-lg mb-2">
                    Click to upload or drag and drop
                  </p>
                  <p className="text-sm text-gray-500">
                    PDF, DOC, or DOCX (max 10MB)
                  </p>
                </div>
              )}
            </div>
          </label>

          {/* Upload Button */}
          <button
            onClick={handleUpload}
            disabled={!file || loading}
            className={`mt-8 w-full py-4 rounded-xl font-semibold text-lg transition-all ${
              file && !loading
                ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
                : "bg-gray-200 text-gray-400 cursor-not-allowed"
            }`}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Generating Questions...
              </span>
            ) : (
              "Upload & Generate Questions"
            )}
          </button>
        </div>
      </div>

      {/* Features Section */}
      <div className="grid md:grid-cols-3 gap-6 mt-12">
        <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="font-bold text-gray-900 mb-2">AI-Powered Questions</h3>
          <p className="text-sm text-gray-600">
            Get personalized interview questions based on your resume and experience
          </p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="font-bold text-gray-900 mb-2">Instant Feedback</h3>
          <p className="text-sm text-gray-600">
            Receive detailed analysis and performance scores after each interview
          </p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h3 className="font-bold text-gray-900 mb-2">Track Progress</h3>
          <p className="text-sm text-gray-600">
            Monitor your improvement over time with comprehensive reports
          </p>
        </div>
      </div>
    </div>
  );
}