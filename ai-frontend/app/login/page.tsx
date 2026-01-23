"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        throw new Error("Invalid credentials");
      }

      const data = await response.json();
      localStorage.setItem("user", JSON.stringify(data.user));
      router.push("/dashboard");
      
    } catch (err: any) {
      setError("Invalid username or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      
      <div className="w-full max-w-xs">
        
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-block w-16 h-16 bg-blue-600 rounded-2xl mb-4">
            <span className="flex items-center justify-center h-full text-white font-bold text-2xl">AI</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">AI Interview Bot</h1>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-xl shadow-xs p-6">
        
        <h2 className="text-lg font-semibold text-gray-900 mb-5">Sign In</h2>
        
        <form onSubmit={handleLogin} className="space-y-4">
            
            <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
                Username
            </label>
            <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-sm"
            />
            </div>

            <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
                Password
            </label>
            <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-sm"
            />
            </div>

            {error && (
            <div className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded">
                {error}
            </div>
            )}

            <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2.5 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 font-medium text-sm"
            >
            {loading ? "Signing in..." : "Sign In"}
            </button>
        </form>

        <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
            Test: nri1 to nri10 (password = username)
            </p>
        </div>
        </div>

        <p className="text-center text-xs text-gray-500 mt-6">
          NRI Institute of Technology
        </p>
      </div>

    </div>
  );
}