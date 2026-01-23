"use client";

import { useState, useEffect } from "react";
import ResumeUpload from "@/components/ResumeUpload";
import InterviewBox from "@/components/InterviewBox";

export default function InterviewPage() {
  const [mode, setMode] = useState<"loading" | "upload" | "interview">("loading");

  useEffect(() => {
    // Check session storage
    const interviewMode = sessionStorage.getItem("interview_mode");
    const questionsExist = sessionStorage.getItem("questions");

    console.log("Interview Page - Mode:", interviewMode);
    console.log("Interview Page - Questions exist:", !!questionsExist);

    if (interviewMode === "career" && questionsExist) {
      // Career mode: questions already generated, go to interview
      console.log("Career mode detected, starting interview");
      setMode("interview");
    } else if (interviewMode === "resume" && questionsExist) {
      // Resume mode: questions generated after upload, go to interview
      console.log("Resume mode detected, starting interview");
      setMode("interview");
    } else {
      // No mode set or no questions: show upload page
      console.log("No mode/questions, showing upload");
      // Only clear old data if we're showing upload
      sessionStorage.removeItem("interview_mode");
      sessionStorage.removeItem("questions");
      sessionStorage.removeItem("interview_role");
      sessionStorage.removeItem("interview_level");
      setMode("upload");
    }
  }, []);

  // Called when user clicks "Start Interview" after uploading resume
  const handleStartInterview = () => {
    sessionStorage.setItem("interview_mode", "resume");
    setMode("interview");
  };

  // Loading state
  if (mode === "loading") {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  // Interview mode (both career and resume)
  if (mode === "interview") {
    return (
      <div className="h-screen p-6">
        <InterviewBox />
      </div>
    );
  }

  // Upload mode
  return (
    <div className="min-h-screen py-12 px-4">
      <ResumeUpload onStartInterview={handleStartInterview} />
    </div>
  );
}