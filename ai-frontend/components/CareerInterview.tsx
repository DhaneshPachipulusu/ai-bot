"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { getUser } from "@/lib/auth";
import { API_URL } from "@/lib/config";

interface CareerRole {
  id: string;
  title: string;
  icon: string;
  description: string;
  levels: string[];
}
const CAREER_ROLES: CareerRole[] = [
  {
    id: "data-analyst",
    title: "Data Analyst",
    icon: "📊",
    description: "SQL, Excel, visualization, statistical analysis",
    levels: ["Entry Level", "Mid Level", "Senior"],
  },
  {
    id: "frontend-developer",
    title: "Frontend Developer",
    icon: "🎨",
    description: "React, JavaScript, CSS, responsive design",
    levels: ["Junior", "Mid Level", "Senior"],
  },
  {
    id: "backend-developer",
    title: "Backend Developer",
    icon: "⚙️",
    description: "APIs, databases, server architecture",
    levels: ["Junior", "Mid Level", "Senior"],
  },
  {
    id: "fullstack-developer",
    title: "Full Stack Developer",
    icon: "🔄",
    description: "Frontend + Backend, end-to-end development",
    levels: ["Junior", "Mid Level", "Senior"],
  },
  {
    id: "data-scientist",
    title: "Data Scientist",
    icon: "🧪",
    description: "ML, Python, statistics, predictive modeling",
    levels: ["Entry Level", "Mid Level", "Senior"],
  },
  {
    id: "devops-engineer",
    title: "DevOps Engineer",
    icon: "🚀",
    description: "CI/CD, Docker, Kubernetes, cloud infrastructure",
    levels: ["Junior", "Mid Level", "Senior"],
  },
  {
    id: "product-manager",
    title: "Product Manager",
    icon: "📋",
    description: "Roadmaps, stakeholders, user research, agile",
    levels: ["Associate", "Mid Level", "Senior"],
  },
  {
    id: "qa-engineer",
    title: "QA Engineer",
    icon: "🔍",
    description: "Testing, automation, quality assurance",
    levels: ["Junior", "Mid Level", "Senior"],
  },
];

export default function CareerInterview() {
  const [selectedRole, setSelectedRole] = useState<CareerRole | null>(null);
  const [selectedLevel, setSelectedLevel] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleStartInterview() {
    if (!selectedRole || !selectedLevel) return;

    const user = getUser();
    if (!user) {
      alert("Please login first");
      router.push("/login");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/generate-role-questions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          role: selectedRole.title,
          level: selectedLevel,
        }),
      });

      const questions = await response.json();

      sessionStorage.setItem("interview_mode", "career");
      sessionStorage.setItem("interview_role", selectedRole.title);
      sessionStorage.setItem("interview_level", selectedLevel);
      sessionStorage.setItem("current_user_id", user.id.toString());
      sessionStorage.setItem("questions", JSON.stringify(questions));

      setTimeout(() => {
        router.push("/interview");
      }, 100);
    } catch (error) {
      console.error("Failed to generate questions:", error);
      alert("Failed to start interview. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          Practice by Career Role
        </h1>
        <p className="text-gray-400">
          Select a role to practice common interview questions — no resume needed
        </p>
      </div>

      {/* Role Selection */}
      <div className="bg-slate-800/50 rounded-2xl border border-slate-700/50 p-6 mb-6">
        <h2 className="text-lg font-bold text-white mb-4">
          1. Choose a Role
        </h2>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {CAREER_ROLES.map((role) => (
            <button
              key={role.id}
              onClick={() => {
                setSelectedRole(role);
                setSelectedLevel("");
              }}
              className={`p-4 rounded-xl border-2 text-left transition-all ${
                selectedRole?.id === role.id
                  ? "border-blue-500 bg-blue-500/20"
                  : "border-slate-600 hover:border-blue-400 hover:bg-slate-700/50"
              }`}
            >
              <span className="text-2xl">{role.icon}</span>
              <p className="font-semibold text-white mt-2 text-sm">
                {role.title}
              </p>
              <p className="text-xs text-gray-400 mt-1 line-clamp-2">
                {role.description}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Level Selection */}
      {selectedRole && (
        <div className="bg-slate-800/50 rounded-2xl border border-slate-700/50 p-6 mb-6">
          <h2 className="text-lg font-bold text-white mb-4">
            2. Select Experience Level
          </h2>

          <div className="flex flex-wrap gap-3">
            {selectedRole.levels.map((level) => (
              <button
                key={level}
                onClick={() => setSelectedLevel(level)}
                className={`px-6 py-3 rounded-xl font-medium transition-all ${
                  selectedLevel === level
                    ? "bg-blue-600 text-white"
                    : "bg-slate-700 text-gray-300 hover:bg-slate-600"
                }`}
              >
                {level}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Interview Preview */}
      {selectedRole && selectedLevel && (
        <div className="bg-gradient-to-br from-blue-500/10 to-indigo-500/10 rounded-2xl border border-blue-500/30 p-6 mb-6">
          <h2 className="text-lg font-bold text-white mb-3">
            Interview Preview
          </h2>

          <div className="grid md:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-400">Role</p>
              <p className="font-semibold text-white">
                {selectedRole.icon} {selectedRole.title}
              </p>
            </div>
            <div>
              <p className="text-gray-400">Level</p>
              <p className="font-semibold text-white">{selectedLevel}</p>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-blue-500/30">
            <p className="text-sm text-gray-300 mb-2">
              <strong>What to expect:</strong>
            </p>
            <ul className="text-sm text-gray-400 space-y-1">
              <li>• Self introduction</li>
              <li>• Technical questions for {selectedRole.title}</li>
              <li>• Behavioral questions (strengths, challenges)</li>
              <li>• Scenario-based problems</li>
              <li>• Closing & feedback</li>
            </ul>
          </div>
        </div>
      )}

      {/* Start Button */}
      <button
        onClick={handleStartInterview}
        disabled={!selectedRole || !selectedLevel || loading}
        className={`w-full py-4 rounded-xl font-semibold text-lg transition-all ${
          selectedRole && selectedLevel && !loading
            ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 shadow-lg shadow-blue-500/25"
            : "bg-slate-700 text-gray-500 cursor-not-allowed"
        }`}
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Preparing Interview...
          </span>
        ) : (
          "Start Practice Interview →"
        )}
      </button>

      {/* Note */}
      <p className="text-center text-sm text-gray-500 mt-4">
        💡 For personalized questions based on your experience,{" "}
        <a href="/interview" className="text-blue-400 hover:underline">
          upload your resume instead
        </a>
      </p>
    </div>
  );
}