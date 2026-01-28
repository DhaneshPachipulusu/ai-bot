"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { API_URL } from "@/lib/config";

interface UserStats {
  id: number;
  username: string;
  college: string;
  total_interviews: number;
  completed_interviews: number;
  avg_score: number;
}

interface DetailedReport {
  id: number;
  interview_id: string;
  overall_score: number;
  fluency: number;
  grammar: number;
  technical_depth: number;
  confidence: number;
  clarity: number;
  response_pace: number;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  job_readiness: string;
  created_at: string;
}

interface SkillAnalysis {
  skill: string;
  count: number;
  avgScore: number;
}

export default function AdminDashboard() {
  const router = useRouter();
  const [users, setUsers] = useState<UserStats[]>([]);
  const [loading, setLoading] = useState(true);

  // Auth check
  useEffect(() => {
    const user = JSON.parse(localStorage.getItem("user") || "null");
    if (!user) {
      router.push("/login");
    } else if (user.role !== "admin") {
      router.push("/dashboard");
    }
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("user");
    router.push("/login");
  };
  const [selectedUser, setSelectedUser] = useState<UserStats | null>(null);
  const [userReports, setUserReports] = useState<DetailedReport[]>([]);
  const [loadingReports, setLoadingReports] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"name" | "score" | "interviews">("score");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [activeTab, setActiveTab] = useState<"overview" | "students" | "skills" | "reports">("overview");

  // Fetch all users
  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await fetch(`${API_URL}/api/admin/users`);
      const data = await response.json();
      setUsers(data.users || []);
    } catch (error) {
      console.error("Failed to fetch users:", error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch user reports
  const fetchUserReports = async (userId: number) => {
    setLoadingReports(true);
    try {
      const response = await fetch(`${API_URL}/api/user/${userId}/reports`);
      const data = await response.json();
      setUserReports(data.reports || []);
    } catch (error) {
      console.error("Failed to fetch reports:", error);
    } finally {
      setLoadingReports(false);
    }
  };

  const handleUserClick = (user: UserStats) => {
    setSelectedUser(user);
    fetchUserReports(user.id);
  };

  // Calculate stats
  const totalStudents = users.length;
  const totalInterviews = users.reduce((sum, u) => sum + u.total_interviews, 0);
  const completedInterviews = users.reduce((sum, u) => sum + u.completed_interviews, 0);
  const avgScore = users.length > 0 
    ? users.reduce((sum, u) => sum + (u.avg_score || 0), 0) / users.filter(u => u.avg_score > 0).length 
    : 0;

  // Performance distribution
  const excellent = users.filter(u => u.avg_score >= 8).length;
  const good = users.filter(u => u.avg_score >= 6 && u.avg_score < 8).length;
  const average = users.filter(u => u.avg_score >= 4 && u.avg_score < 6).length;
  const needsWork = users.filter(u => u.avg_score > 0 && u.avg_score < 4).length;
  const notAttempted = users.filter(u => !u.avg_score || u.avg_score === 0).length;

  // Filter and sort users
  const filteredUsers = users
    .filter(u => 
      u.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.college.toLowerCase().includes(searchQuery.toLowerCase())
    )
    .sort((a, b) => {
      let comparison = 0;
      if (sortBy === "name") comparison = a.username.localeCompare(b.username);
      else if (sortBy === "score") comparison = (a.avg_score || 0) - (b.avg_score || 0);
      else if (sortBy === "interviews") comparison = a.completed_interviews - b.completed_interviews;
      return sortOrder === "desc" ? -comparison : comparison;
    });

  // Skill analysis from all reports (mock - you'd aggregate from actual data)
  const skillAnalysis: SkillAnalysis[] = [
    { skill: "Communication", count: 45, avgScore: 7.2 },
    { skill: "Technical Knowledge", count: 42, avgScore: 6.8 },
    { skill: "Problem Solving", count: 38, avgScore: 6.5 },
    { skill: "Confidence", count: 45, avgScore: 7.0 },
    { skill: "Clarity", count: 45, avgScore: 6.9 },
    { skill: "Grammar", count: 45, avgScore: 7.5 },
  ];

  const getScoreColor = (score: number) => {
    if (score >= 8) return "text-green-400";
    if (score >= 6) return "text-blue-400";
    if (score >= 4) return "text-yellow-400";
    return "text-red-400";
  };

  const getScoreBg = (score: number) => {
    if (score >= 8) return "bg-green-500/20 border-green-500/30";
    if (score >= 6) return "bg-blue-500/20 border-blue-500/30";
    if (score >= 4) return "bg-yellow-500/20 border-yellow-500/30";
    return "bg-red-500/20 border-red-500/30";
  };

  const getReadinessColor = (readiness: string) => {
    if (readiness?.toLowerCase().includes("ready")) return "text-green-400 bg-green-500/20";
    if (readiness?.toLowerCase().includes("improvement")) return "text-red-400 bg-red-500/20";
    return "text-yellow-400 bg-yellow-500/20";
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Top Navbar */}
      
      {/* Header with Tabs */}
      <header className="border-b border-slate-700/50 px-6 py-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white">Dashboard Overview</h2>
            <p className="text-gray-400 text-sm">Monitor student performance & skills</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchUsers}
              className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition flex items-center gap-2 text-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
            <button
              onClick={() => {/* Export logic */}}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2 text-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Export
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mt-4 overflow-x-auto pb-1">
          {[
            { id: "overview", label: "Overview", icon: "📊" },
            { id: "students", label: "Students", icon: "👥" },
            { id: "skills", label: "Skills Analysis", icon: "🎯" },
            { id: "reports", label: "Recent Reports", icon: "📋" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition flex items-center gap-2 ${
                activeTab === tab.id
                  ? "bg-blue-600 text-white"
                  : "bg-slate-800 text-gray-400 hover:bg-slate-700"
              }`}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </header>

      <main className="p-6">
        {/* Overview Tab */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-800/60 rounded-xl border border-slate-700/50 p-5">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-blue-500/20 rounded-xl flex items-center justify-center">
                    <span className="text-2xl">👥</span>
                  </div>
                  <div>
                    <p className="text-gray-400 text-sm">Total Students</p>
                    <p className="text-2xl font-bold text-white">{totalStudents}</p>
                  </div>
                </div>
              </div>

              <div className="bg-slate-800/60 rounded-xl border border-slate-700/50 p-5">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-green-500/20 rounded-xl flex items-center justify-center">
                    <span className="text-2xl">✅</span>
                  </div>
                  <div>
                    <p className="text-gray-400 text-sm">Completed</p>
                    <p className="text-2xl font-bold text-white">{completedInterviews}</p>
                  </div>
                </div>
              </div>

              <div className="bg-slate-800/60 rounded-xl border border-slate-700/50 p-5">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-yellow-500/20 rounded-xl flex items-center justify-center">
                    <span className="text-2xl">📈</span>
                  </div>
                  <div>
                    <p className="text-gray-400 text-sm">Avg Score</p>
                    <p className={`text-2xl font-bold ${getScoreColor(avgScore)}`}>
                      {avgScore ? avgScore.toFixed(1) : "N/A"}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-slate-800/60 rounded-xl border border-slate-700/50 p-5">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-purple-500/20 rounded-xl flex items-center justify-center">
                    <span className="text-2xl">🎯</span>
                  </div>
                  <div>
                    <p className="text-gray-400 text-sm">Job Ready</p>
                    <p className="text-2xl font-bold text-green-400">{excellent + good}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Performance Distribution */}
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-slate-800/60 rounded-xl border border-slate-700/50 p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Performance Distribution</h3>
                <div className="space-y-3">
                  {[
                    { label: "Excellent (8-10)", count: excellent, color: "bg-green-500", percent: (excellent / totalStudents) * 100 },
                    { label: "Good (6-8)", count: good, color: "bg-blue-500", percent: (good / totalStudents) * 100 },
                    { label: "Average (4-6)", count: average, color: "bg-yellow-500", percent: (average / totalStudents) * 100 },
                    { label: "Needs Work (<4)", count: needsWork, color: "bg-red-500", percent: (needsWork / totalStudents) * 100 },
                    { label: "Not Attempted", count: notAttempted, color: "bg-gray-500", percent: (notAttempted / totalStudents) * 100 },
                  ].map((item) => (
                    <div key={item.label} className="flex items-center gap-3">
                      <div className="w-32 text-sm text-gray-400">{item.label}</div>
                      <div className="flex-1 h-6 bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${item.color} transition-all duration-500`}
                          style={{ width: `${item.percent || 0}%` }}
                        />
                      </div>
                      <div className="w-12 text-right text-white font-medium">{item.count}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Quick Skills Overview */}
              <div className="bg-slate-800/60 rounded-xl border border-slate-700/50 p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Skills Overview</h3>
                <div className="space-y-3">
                  {skillAnalysis.map((skill) => (
                    <div key={skill.skill} className="flex items-center justify-between">
                      <span className="text-gray-300">{skill.skill}</span>
                      <div className="flex items-center gap-3">
                        <div className="w-24 h-2 bg-slate-700 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              skill.avgScore >= 7 ? "bg-green-500" : skill.avgScore >= 5 ? "bg-yellow-500" : "bg-red-500"
                            }`}
                            style={{ width: `${(skill.avgScore / 10) * 100}%` }}
                          />
                        </div>
                        <span className={`font-medium ${getScoreColor(skill.avgScore)}`}>
                          {skill.avgScore.toFixed(1)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Top Performers */}
            <div className="bg-slate-800/60 rounded-xl border border-slate-700/50 p-6">
              <h3 className="text-lg font-semibold text-white mb-4">🏆 Top Performers</h3>
              <div className="grid md:grid-cols-5 gap-4">
                {users
                  .filter(u => u.avg_score > 0)
                  .sort((a, b) => b.avg_score - a.avg_score)
                  .slice(0, 5)
                  .map((user, index) => (
                    <div
                      key={user.id}
                      onClick={() => handleUserClick(user)}
                      className="bg-slate-700/50 rounded-xl p-4 text-center cursor-pointer hover:bg-slate-700 transition"
                    >
                      <div className={`w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-2 ${
                        index === 0 ? "bg-yellow-500/20" : index === 1 ? "bg-gray-400/20" : index === 2 ? "bg-orange-500/20" : "bg-slate-600"
                      }`}>
                        <span className="text-xl">
                          {index === 0 ? "🥇" : index === 1 ? "🥈" : index === 2 ? "🥉" : `#${index + 1}`}
                        </span>
                      </div>
                      <p className="text-white font-medium truncate">{user.username}</p>
                      <p className={`text-lg font-bold ${getScoreColor(user.avg_score)}`}>
                        {user.avg_score.toFixed(1)}
                      </p>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        )}

        {/* Students Tab */}
        {activeTab === "students" && (
          <div className="space-y-4">
            {/* Search and Filter */}
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1 relative">
                <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  type="text"
                  placeholder="Search students..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex gap-2">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="score">Sort by Score</option>
                  <option value="name">Sort by Name</option>
                  <option value="interviews">Sort by Interviews</option>
                </select>
                <button
                  onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}
                  className="px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white hover:bg-slate-700 transition"
                >
                  {sortOrder === "desc" ? "↓" : "↑"}
                </button>
              </div>
            </div>

            {/* Students Table */}
            <div className="bg-slate-800/60 rounded-xl border border-slate-700/50 overflow-hidden">
              <table className="w-full">
                <thead className="bg-slate-700/50">
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-medium text-gray-400">#</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-gray-400">Student</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-gray-400">College</th>
                    <th className="px-6 py-4 text-center text-sm font-medium text-gray-400">Interviews</th>
                    <th className="px-6 py-4 text-center text-sm font-medium text-gray-400">Avg Score</th>
                    <th className="px-6 py-4 text-center text-sm font-medium text-gray-400">Status</th>
                    <th className="px-6 py-4 text-center text-sm font-medium text-gray-400">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/50">
                  {filteredUsers.map((user, index) => (
                    <tr
                      key={user.id}
                      className="hover:bg-slate-700/30 transition cursor-pointer"
                      onClick={() => handleUserClick(user)}
                    >
                      <td className="px-6 py-4 text-gray-400">{index + 1}</td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white font-medium">
                            {user.username.charAt(0).toUpperCase()}
                          </div>
                          <span className="text-white font-medium">{user.username}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-gray-400">{user.college}</td>
                      <td className="px-6 py-4 text-center">
                        <span className="text-white">{user.completed_interviews}</span>
                        <span className="text-gray-500">/{user.total_interviews}</span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span className={`text-lg font-bold ${getScoreColor(user.avg_score)}`}>
                          {user.avg_score ? user.avg_score.toFixed(1) : "—"}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          user.avg_score >= 7 ? "bg-green-500/20 text-green-400" :
                          user.avg_score >= 5 ? "bg-yellow-500/20 text-yellow-400" :
                          user.avg_score > 0 ? "bg-red-500/20 text-red-400" :
                          "bg-gray-500/20 text-gray-400"
                        }`}>
                          {user.avg_score >= 7 ? "Job Ready" :
                           user.avg_score >= 5 ? "Developing" :
                           user.avg_score > 0 ? "Needs Work" : "No Data"}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <button className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-lg text-sm hover:bg-blue-500/30 transition">
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {filteredUsers.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  No students found matching your search
                </div>
              )}
            </div>
          </div>
        )}

        {/* Skills Analysis Tab */}
        {activeTab === "skills" && (
          <div className="space-y-6">
            <div className="grid md:grid-cols-3 gap-6">
              {/* Skill Cards */}
              {[
                { name: "Communication", icon: "💬", score: 7.2, trend: "+0.3" },
                { name: "Technical Depth", icon: "💻", score: 6.8, trend: "+0.5" },
                { name: "Problem Solving", icon: "🧩", score: 6.5, trend: "-0.2" },
                { name: "Confidence", icon: "💪", score: 7.0, trend: "+0.4" },
                { name: "Clarity", icon: "🎯", score: 6.9, trend: "+0.1" },
                { name: "Grammar", icon: "📝", score: 7.5, trend: "+0.2" },
              ].map((skill) => (
                <div key={skill.name} className={`rounded-xl border p-6 ${getScoreBg(skill.score)}`}>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{skill.icon}</span>
                      <h3 className="text-white font-semibold">{skill.name}</h3>
                    </div>
                    <span className={`text-sm ${skill.trend.startsWith("+") ? "text-green-400" : "text-red-400"}`}>
                      {skill.trend}
                    </span>
                  </div>
                  <div className="flex items-end justify-between">
                    <span className={`text-4xl font-bold ${getScoreColor(skill.score)}`}>
                      {skill.score.toFixed(1)}
                    </span>
                    <span className="text-gray-400 text-sm">/10</span>
                  </div>
                  <div className="mt-4 h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        skill.score >= 7 ? "bg-green-500" : skill.score >= 5 ? "bg-yellow-500" : "bg-red-500"
                      }`}
                      style={{ width: `${(skill.score / 10) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* Common Weaknesses */}
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-red-500/10 rounded-xl border border-red-500/30 p-6">
                <h3 className="text-red-400 font-semibold mb-4 flex items-center gap-2">
                  <span>⚠️</span> Common Weaknesses
                </h3>
                <ul className="space-y-3">
                  {[
                    "Lack of specific examples in answers",
                    "Technical depth needs improvement",
                    "Nervousness affecting confidence",
                    "Incomplete STAR method responses",
                    "Insufficient project explanations",
                  ].map((item, i) => (
                    <li key={i} className="flex items-start gap-2 text-gray-300">
                      <span className="text-red-400 mt-1">•</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-green-500/10 rounded-xl border border-green-500/30 p-6">
                <h3 className="text-green-400 font-semibold mb-4 flex items-center gap-2">
                  <span>✓</span> Common Strengths
                </h3>
                <ul className="space-y-3">
                  {[
                    "Good communication skills overall",
                    "Strong grammar and language",
                    "Positive attitude and enthusiasm",
                    "Basic technical knowledge present",
                    "Willingness to learn and improve",
                  ].map((item, i) => (
                    <li key={i} className="flex items-start gap-2 text-gray-300">
                      <span className="text-green-400 mt-1">•</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Recommendations */}
            <div className="bg-blue-500/10 rounded-xl border border-blue-500/30 p-6">
              <h3 className="text-blue-400 font-semibold mb-4 flex items-center gap-2">
                <span>💡</span> Training Recommendations
              </h3>
              <div className="grid md:grid-cols-3 gap-4">
                {[
                  { title: "STAR Method Workshop", desc: "Teach structured answering technique", priority: "High" },
                  { title: "Technical Deep Dives", desc: "Focus sessions on core concepts", priority: "High" },
                  { title: "Mock Interviews", desc: "More practice with feedback", priority: "Medium" },
                  { title: "Project Presentation", desc: "Practice explaining projects clearly", priority: "Medium" },
                  { title: "Confidence Building", desc: "Group activities and speaking practice", priority: "Low" },
                  { title: "Resume Optimization", desc: "Workshops on resume writing", priority: "Low" },
                ].map((rec, i) => (
                  <div key={i} className="bg-slate-800/50 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-white font-medium">{rec.title}</h4>
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        rec.priority === "High" ? "bg-red-500/20 text-red-400" :
                        rec.priority === "Medium" ? "bg-yellow-500/20 text-yellow-400" :
                        "bg-green-500/20 text-green-400"
                      }`}>
                        {rec.priority}
                      </span>
                    </div>
                    <p className="text-gray-400 text-sm">{rec.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Reports Tab */}
        {activeTab === "reports" && (
          <div className="space-y-4">
            <div className="bg-slate-800/60 rounded-xl border border-slate-700/50 p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Recent Interview Reports</h3>
              <div className="space-y-3">
                {users
                  .filter(u => u.completed_interviews > 0)
                  .slice(0, 10)
                  .map((user) => (
                    <div
                      key={user.id}
                      onClick={() => handleUserClick(user)}
                      className="flex items-center justify-between p-4 bg-slate-700/30 rounded-xl hover:bg-slate-700/50 cursor-pointer transition"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white font-bold">
                          {user.username.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p className="text-white font-medium">{user.username}</p>
                          <p className="text-gray-400 text-sm">{user.college}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-6">
                        <div className="text-center">
                          <p className="text-gray-400 text-xs">Interviews</p>
                          <p className="text-white font-semibold">{user.completed_interviews}</p>
                        </div>
                        <div className="text-center">
                          <p className="text-gray-400 text-xs">Avg Score</p>
                          <p className={`font-bold ${getScoreColor(user.avg_score)}`}>
                            {user.avg_score ? user.avg_score.toFixed(1) : "—"}
                          </p>
                        </div>
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Student Detail Modal */}
      {selectedUser && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="sticky top-0 bg-slate-800 border-b border-slate-700 px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white text-xl font-bold">
                  {selectedUser.username.charAt(0).toUpperCase()}
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">{selectedUser.username}</h2>
                  <p className="text-gray-400">{selectedUser.college}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedUser(null)}
                className="w-10 h-10 bg-slate-700 rounded-full flex items-center justify-center text-gray-400 hover:text-white hover:bg-slate-600 transition"
              >
                ✕
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-6">
              {/* Stats */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-slate-700/50 rounded-xl p-4 text-center">
                  <p className="text-gray-400 text-sm">Interviews</p>
                  <p className="text-2xl font-bold text-white">{selectedUser.completed_interviews}</p>
                </div>
                <div className="bg-slate-700/50 rounded-xl p-4 text-center">
                  <p className="text-gray-400 text-sm">Avg Score</p>
                  <p className={`text-2xl font-bold ${getScoreColor(selectedUser.avg_score)}`}>
                    {selectedUser.avg_score ? selectedUser.avg_score.toFixed(1) : "N/A"}
                  </p>
                </div>
                <div className="bg-slate-700/50 rounded-xl p-4 text-center">
                  <p className="text-gray-400 text-sm">Status</p>
                  <p className={`text-lg font-bold ${
                    selectedUser.avg_score >= 7 ? "text-green-400" : 
                    selectedUser.avg_score >= 5 ? "text-yellow-400" : "text-red-400"
                  }`}>
                    {selectedUser.avg_score >= 7 ? "Ready" : selectedUser.avg_score >= 5 ? "Developing" : "Needs Work"}
                  </p>
                </div>
              </div>

              {/* Reports */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">Interview History</h3>
                {loadingReports ? (
                  <div className="text-center py-8">
                    <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                    <p className="text-gray-400">Loading reports...</p>
                  </div>
                ) : userReports.length > 0 ? (
                  <div className="space-y-3">
                    {userReports.map((report, index) => (
                      <div key={report.id} className="bg-slate-700/30 rounded-xl p-4">
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-gray-400 text-sm">
                            Interview #{userReports.length - index}
                          </span>
                          <span className="text-gray-500 text-xs">
                            {new Date(report.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        <div className="grid grid-cols-6 gap-2 mb-3">
                          {[
                            { label: "Overall", value: report.overall_score },
                            { label: "Fluency", value: report.fluency },
                            { label: "Technical", value: report.technical_depth },
                            { label: "Confidence", value: report.confidence },
                            { label: "Clarity", value: report.clarity },
                            { label: "Grammar", value: report.grammar },
                          ].map((metric) => (
                            <div key={metric.label} className="text-center">
                              <p className="text-gray-500 text-xs">{metric.label}</p>
                              <p className={`font-bold ${getScoreColor(metric.value || 0)}`}>
                                {metric.value || "—"}
                              </p>
                            </div>
                          ))}
                        </div>
                        <div className={`inline-block px-3 py-1 rounded-full text-xs ${getReadinessColor(report.job_readiness)}`}>
                          {report.job_readiness || "Not assessed"}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">No interview reports yet</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}