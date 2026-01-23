"use client";

import { useEffect, useState } from "react";
import { analyzeInterview } from "@/lib/api";

/* ------------------ CIRCULAR SCORE COMPONENT ------------------ */
function CircleScore({
  label,
  value,
  size = 110,
}: {
  label: string;
  value: number;
  size?: number;
}) {
  const radius = size / 2 - 8;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 10) * circumference;

  const color =
    value >= 8
      ? "#22c55e"
      : value >= 6
      ? "#facc15"
      : "#ef4444";

  return (
    <div className="flex flex-col items-center group hover:scale-105 transition-transform duration-300">
      <div className="relative">
        <svg width={size} height={size}>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="#e5e7eb"
            strokeWidth="8"
            fill="none"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={color}
            strokeWidth="8"
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
            className="transition-all duration-1000 ease-out"
          />
          <text
            x="50%"
            y="50%"
            dominantBaseline="middle"
            textAnchor="middle"
            className="text-2xl font-bold"
            style={{ fill: color }}
          >
            {value}
          </text>
        </svg>
        <div 
          className="absolute inset-0 rounded-full blur-xl opacity-20 group-hover:opacity-30 transition-opacity"
          style={{ backgroundColor: color }}
        />
      </div>
      <p className="mt-3 text-sm font-semibold text-gray-700">
        {label}
      </p>
    </div>
  );
}

/* ------------------ REPORT PAGE ------------------ */
export default function ReportPage() {
  const [report, setReport] = useState<any>(null);

  useEffect(() => {
    const interviewId = sessionStorage.getItem("interviewId");
    if (!interviewId) return;

    analyzeInterview(interviewId).then(setReport);
  }, []);

  if (!report) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-2xl shadow-2xl">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="text-lg font-medium text-gray-700">
              Generating interview insights…
            </span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* REPORT HEADER - Full Width */}
      <div className="bg-gradient-to-r from-blue-600 via-blue-700 to-purple-700 text-white py-16 px-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <div>
              <div className="inline-block px-4 py-1.5 bg-white/20 backdrop-blur-sm rounded-full text-sm font-medium mb-4">
                AI-Powered Analysis
              </div>
              <h1 className="text-5xl md:text-6xl font-bold mb-4">
                Interview Performance Report
              </h1>
              <p className="text-xl text-blue-100">
                Comprehensive AI-driven evaluation of your interview performance
              </p>
            </div>
          </div>
          
          {/* Report Meta Info */}
          <div className="flex items-center gap-6 text-sm text-blue-100 mt-8">
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Analysis Complete
            </div>
          </div>
        </div>
      </div>

      {/* MAIN REPORT CONTENT */}
      <div className="max-w-7xl mx-auto px-8 -mt-8">
        
        {/* OVERALL SCORE CARD */}
        <div className="bg-white rounded-2xl shadow-xl p-10 mb-8 border-t-4 border-blue-600">
          <div className="grid md:grid-cols-[1fr_300px] gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-gray-800 mb-4">Overall Performance</h2>
              <p className="text-gray-600 mb-6">
                Your interview performance has been evaluated across multiple dimensions including communication, 
                technical knowledge, and professional presentation. Below is your comprehensive score.
              </p>
              <div className="flex items-center gap-4">
                <div className="flex-1 h-3 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-blue-500 to-purple-600 transition-all duration-1000"
                    style={{ width: `${(report.overall_score / 10) * 100}%` }}
                  />
                </div>
                <span className="text-2xl font-bold text-gray-700">{report.overall_score}/10</span>
              </div>
            </div>
            <div className="flex justify-center">
              <CircleScore
                label="Overall Score"
                value={report.overall_score}
                size={200}
              />
            </div>
          </div>
        </div>

        {/* PERFORMANCE METRICS */}
        <div className="bg-white rounded-2xl shadow-xl p-10 mb-8">
          <h2 className="text-3xl font-bold text-gray-800 mb-8">Performance Metrics</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8">
            {[
              { label: "Fluency", value: report.fluency },
              { label: "Grammar", value: report.grammar },
              { label: "Technical Depth", value: report.technical_depth },
              { label: "Confidence", value: report.confidence },
              { label: "Clarity", value: report.clarity },
              { label: "Response Pace", value: report.response_pace },
            ].map((metric) => (
              <div key={metric.label} className="flex justify-center">
                <CircleScore label={metric.label} value={metric.value} size={120} />
              </div>
            ))}
          </div>
        </div>

        {/* DETAILED ANALYSIS */}
        <div className="grid md:grid-cols-2 gap-8 mb-8">
          
          {/* Strengths */}
          <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
            <div className="bg-gradient-to-r from-green-500 to-emerald-600 px-8 py-6">
              <div className="flex items-center gap-3 text-white">
                <div className="bg-white/20 rounded-full p-2">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold">Key Strengths</h3>
              </div>
            </div>
            <div className="p-8">
              <ul className="space-y-4">
                {report.strengths.map((s: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-3">
                    <div className="mt-1 flex-shrink-0 w-6 h-6 rounded-full bg-green-100 flex items-center justify-center">
                      <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <span className="text-gray-700 flex-1">{s}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Areas to Improve */}
          <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
            <div className="bg-gradient-to-r from-orange-500 to-red-600 px-8 py-6">
              <div className="flex items-center gap-3 text-white">
                <div className="bg-white/20 rounded-full p-2">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold">Areas for Improvement</h3>
              </div>
            </div>
            <div className="p-8">
              <ul className="space-y-4">
                {report.weaknesses.map((w: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-3">
                    <div className="mt-1 flex-shrink-0 w-6 h-6 rounded-full bg-orange-100 flex items-center justify-center">
                      <svg className="w-4 h-4 text-orange-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <span className="text-gray-700 flex-1">{w}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* ACTIONABLE RECOMMENDATIONS */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden mb-8">
          <div className="bg-gradient-to-r from-blue-600 to-indigo-700 px-8 py-6">
            <div className="flex items-center gap-3 text-white">
              <div className="bg-white/20 rounded-full p-2">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <h3 className="text-2xl font-bold">Actionable Recommendations</h3>
            </div>
          </div>
          <div className="p-8">
            <p className="text-gray-600 mb-6">
              Based on your performance analysis, here are specific recommendations to enhance your interview skills:
            </p>
            <div className="space-y-4">
              {report.recommendations.map((r: string, idx: number) => (
                <div key={idx} className="flex items-start gap-4 p-4 bg-blue-50 rounded-lg border-l-4 border-blue-600">
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                    {idx + 1}
                  </div>
                  <span className="text-gray-700 flex-1 pt-1">{r}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* JOB READINESS ASSESSMENT */}
        <div className="bg-gradient-to-r from-indigo-600 to-purple-700 rounded-2xl shadow-xl p-10 mb-12 text-white text-center">
          <h3 className="text-2xl font-bold mb-3">Job Readiness Assessment</h3>
          <div className="inline-block bg-white/20 backdrop-blur-sm px-8 py-4 rounded-xl">
            <p className="text-3xl font-bold">{report.job_readiness}</p>
          </div>
        </div>

        {/* FOOTER */}
        <div className="text-center py-8 text-gray-500 text-sm border-t border-gray-200">
          <p>Generated by AI Interview Bot • Confidential Report • {new Date().getFullYear()}</p>
        </div>
      </div>

      <style jsx>{`
        @keyframes fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }
      `}</style>
    </div>
  );
}