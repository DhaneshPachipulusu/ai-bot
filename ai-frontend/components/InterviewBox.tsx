"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { getUser } from "@/lib/auth";

export default function InterviewBox() {
  const router = useRouter();

  const [interviewId, setInterviewId] = useState<string | null>(null);
  const [question, setQuestion] = useState<string | null>(null);
  const [questionType, setQuestionType] = useState<string>("technical");
  const [questionNumber, setQuestionNumber] = useState(1);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [answer, setAnswer] = useState("");

  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [micError, setMicError] = useState<string | null>(null);
  const [isCompleted, setIsCompleted] = useState(false);

  const recognitionRef = useRef<any>(null);
  const startedRef = useRef(false);

  /* =========================
     START INTERVIEW
  ==========================*/
  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;

    const user = getUser();
    if (!user) {
      console.error("User not logged in");
      router.push("/login");
      return;
    }

    const stored = sessionStorage.getItem("questions");
    if (!stored) {
      console.error("No questions in sessionStorage");
      return;
    }

    const parsed = JSON.parse(stored);
    let rawQuestions = Array.isArray(parsed)
      ? parsed
      : Array.isArray(parsed.questions)
      ? parsed.questions
      : Object.values(parsed.questions || {}).flat();

    const questionsArray: string[] = rawQuestions.map((q: any) =>
      typeof q === "string" ? q : q.question
    );

    setTotalQuestions(questionsArray.length);

    fetch("https://ai-bot-ikyi.onrender.com/api/start-interview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: user.id,
        questions: questionsArray,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        setInterviewId(data.interview_id);
        setQuestion(data.question);
        // Detect question type from first question
        const firstQ = rawQuestions[0];
        if (firstQ?.type) setQuestionType(firstQ.type);
      })
      .catch((err) => console.error("Start interview failed", err));
  }, [router]);

  /* =========================
     SPEAK QUESTION
  ==========================*/
  useEffect(() => {
    if (!question || isCompleted) return;

    speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(question);
    utterance.lang = "en-US";
    utterance.rate = 0.95;

    utterance.onstart = () => setSpeaking(true);
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);

    speechSynthesis.speak(utterance);

    return () => speechSynthesis.cancel();
  }, [question, isCompleted]);

  /* =========================
     SPEECH RECOGNITION
  ==========================*/
  useEffect(() => {
    const SR =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SR) {
      setMicError("Speech recognition not supported");
      return;
    }

    const rec = new SR();
    rec.lang = "en-US";
    rec.continuous = false;

    rec.onresult = (e: any) => {
      setAnswer(e.results[0][0].transcript);
      setListening(false);
    };

    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);

    recognitionRef.current = rec;
  }, []);

  const startListening = async () => {
    if (!recognitionRef.current) {
      setMicError(
        "Speech recognition not available. Please use Chrome, Edge, or Safari."
      );
      return;
    }

    if (listening) return;

    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (error: any) {
      console.error("Microphone permission error:", error);
      if (
        error.name === "NotAllowedError" ||
        error.name === "PermissionDeniedError"
      ) {
        setMicError(
          "Microphone access denied. Please allow microphone access."
        );
      } else if (error.name === "NotFoundError") {
        setMicError("No microphone found.");
      } else {
        setMicError("Unable to access microphone.");
      }
      return;
    }

    try {
      setMicError(null);
      setListening(true);
      recognitionRef.current.start();
    } catch (error) {
      console.error("Error starting recognition:", error);
      setListening(false);
      setMicError("Failed to start speech recognition.");
    }
  };

  /* =========================
     SUBMIT ANSWER
  ==========================*/
  const submit = async () => {
    if (!answer.trim() || !interviewId || !question) return;

    const user = getUser();
    if (!user) {
      router.push("/login");
      return;
    }

    const res = await fetch("https://ai-bot-ikyi.onrender.com/api/submit-answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: user.id,
        interview_id: interviewId,
        question: question,
        answer: answer,
      }),
    });

    const data = await res.json();
    setAnswer("");

    if (data.status === "completed") {
      setIsCompleted(true);
      
      // Save interview ID for report
      sessionStorage.setItem("interviewId", interviewId);
      
      // Clear interview data (so next interview starts fresh)
      sessionStorage.removeItem("questions");
      sessionStorage.removeItem("interview_mode");
      sessionStorage.removeItem("interview_role");
      sessionStorage.removeItem("interview_level");
      
      // Show thank you for 4 seconds then redirect
      setTimeout(() => {
        router.replace("/report");
      }, 4000);
      return;
    }

    if (data.next_question) {
      setQuestion(data.next_question);
      setQuestionNumber((prev) => prev + 1);
      
      // Try to detect question type from stored questions
      const stored = sessionStorage.getItem("questions");
      if (stored) {
        const parsed = JSON.parse(stored);
        const questions = parsed.questions || parsed;
        const nextQ = questions[questionNumber]; // next question index
        if (nextQ?.type) setQuestionType(nextQ.type);
      }
    }
  };

  /* =========================
     GET QUESTION TYPE BADGE
  ==========================*/
  function getQuestionTypeBadge(type: string) {
    switch (type.toLowerCase()) {
      case "introduction":
        return { bg: "bg-purple-100", text: "text-purple-700", label: "🎤 Introduction" };
      case "technical":
      case "skill":
        return { bg: "bg-blue-100", text: "text-blue-700", label: "💻 Technical" };
      case "project":
        return { bg: "bg-green-100", text: "text-green-700", label: "📁 Project" };
      case "behavioral":
        return { bg: "bg-orange-100", text: "text-orange-700", label: "💬 Behavioral" };
      case "scenario":
        return { bg: "bg-yellow-100", text: "text-yellow-700", label: "🎯 Scenario" };
      case "closing":
        return { bg: "bg-gray-100", text: "text-gray-700", label: "🤝 Closing" };
      default:
        return { bg: "bg-gray-100", text: "text-gray-700", label: "Question" };
    }
  }

  /* =========================
     THANK YOU SCREEN
  ==========================*/
  if (isCompleted) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="w-24 h-24 bg-gradient-to-br from-green-400 to-emerald-500 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg">
            <span className="text-5xl">🎉</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Interview Complete!
          </h1>
          <p className="text-gray-600 mb-6">
            Thank you for your time today! You've done a great job answering all
            the questions. Your detailed feedback report is being prepared.
          </p>
          <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
            <svg
              className="animate-spin h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            Redirecting to your report...
          </div>
        </div>
      </div>
    );
  }

  /* =========================
     LOADING SCREEN
  ==========================*/
  if (!question) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Preparing interview...</p>
          <p className="text-gray-400 text-sm mt-1">Please wait</p>
        </div>
      </div>
    );
  }

  const badge = getQuestionTypeBadge(questionType);

  /* =========================
     MAIN UI
  ==========================*/
  return (
    <div className="h-full flex flex-col">
      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-500 mb-1">
          <span>Question {questionNumber} of {totalQuestions}</span>
          <span>{Math.round((questionNumber / totalQuestions) * 100)}% complete</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-gradient-to-r from-blue-500 to-indigo-500 h-2 rounded-full transition-all duration-500"
            style={{ width: `${(questionNumber / totalQuestions) * 100}%` }}
          ></div>
        </div>
      </div>

      {/* INTERVIEWER SECTION */}
      <div className="flex-1 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-3xl shadow-2xl relative overflow-hidden flex items-center justify-center mb-6">
        {/* Animated background */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-96 h-96 bg-blue-500 rounded-full filter blur-3xl animate-pulse"></div>
          <div
            className="absolute bottom-0 right-0 w-96 h-96 bg-purple-500 rounded-full filter blur-3xl animate-pulse"
            style={{ animationDelay: "1s" }}
          ></div>
        </div>

        <div className="relative z-10 flex flex-col items-center text-center">
          {/* AUDIO WAVE VISUALIZATION */}
          <div className="mb-8 flex items-center justify-center gap-2.5 h-40">
            {[
              { delay: 0, baseHeight: "2rem" },
              { delay: 0.1, baseHeight: "3rem" },
              { delay: 0.2, baseHeight: "2.5rem" },
              { delay: 0.15, baseHeight: "3.5rem" },
              { delay: 0.05, baseHeight: "2rem" },
            ].map((bar, i) => (
              <div
                key={i}
                className={`w-2.5 bg-gradient-to-t from-blue-500 via-blue-400 to-indigo-400 rounded-full transition-all duration-150 shadow-lg ${
                  speaking ? "shadow-blue-500/50" : ""
                }`}
                style={{
                  height: speaking ? bar.baseHeight : listening ? "2rem" : bar.baseHeight,
                  animation: speaking ? `wave-${i} 0.6s ease-in-out infinite` : "none",
                  animationDelay: `${bar.delay}s`,
                }}
              />
            ))}
          </div>

          {/* INTERVIEWER INFO */}
          <div>
            <h3 className="text-white font-semibold text-2xl mb-2">AI Interviewer</h3>
            <p className="text-gray-400 text-sm mb-3">Technical Interview Specialist</p>
            <span
              className={`inline-block px-4 py-1.5 rounded-full text-sm font-medium ${
                speaking
                  ? "bg-green-500/20 text-green-300 animate-pulse"
                  : listening
                  ? "bg-red-500/20 text-red-300 animate-pulse"
                  : "bg-blue-500/20 text-blue-300"
              }`}
            >
              {speaking ? "🔊 Speaking..." : listening ? "🎤 Listening..." : "⏸️ Ready"}
            </span>
          </div>
        </div>
      </div>

      {/* Enhanced wave animations */}
      <style jsx>{`
        @keyframes wave-0 { 0%, 100% { height: 2rem; } 50% { height: 8rem; } }
        @keyframes wave-1 { 0%, 100% { height: 3rem; } 50% { height: 10rem; } }
        @keyframes wave-2 { 0%, 100% { height: 2.5rem; } 50% { height: 9rem; } }
        @keyframes wave-3 { 0%, 100% { height: 3.5rem; } 50% { height: 11rem; } }
        @keyframes wave-4 { 0%, 100% { height: 2rem; } 50% { height: 7rem; } }
      `}</style>

      {/* QUESTION & ANSWER BOX */}
      <div className="bg-white rounded-2xl shadow-xl p-6">
        {/* Question Type Badge & Question */}
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${badge.bg} ${badge.text}`}>
              {badge.label}
            </span>
          </div>
          <h2 className="text-xl font-semibold text-gray-900">{question}</h2>
        </div>

        {/* Answer Input Row */}
        <div className="flex items-end gap-3">
          <div className="flex-1">
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && e.ctrlKey) {
                  submit();
                }
              }}
              placeholder="Type your answer here or use voice input..."
              rows={3}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all resize-none"
            />
          </div>

          {/* Voice button */}
          <button
            onClick={startListening}
            disabled={listening}
            className={`flex items-center justify-center w-12 h-12 rounded-xl font-medium transition-all relative ${
              listening
                ? "bg-red-500 text-white animate-pulse"
                : micError
                ? "bg-yellow-100 text-yellow-700 hover:bg-yellow-200"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
            title={micError ? "Click to retry" : "Voice Input"}
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z"
                clipRule="evenodd"
              />
            </svg>
            {micError && (
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-500 rounded-full border-2 border-white"></span>
            )}
          </button>

          {/* Submit button */}
          <button
            onClick={submit}
            disabled={!answer.trim()}
            className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-6 py-3 rounded-xl font-semibold hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all h-12"
          >
            {questionNumber === totalQuestions ? "Finish" : "Next"}
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </button>
        </div>

        {/* Error message */}
        {micError && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-xl">
            <p className="text-sm text-red-700">{micError}</p>
          </div>
        )}

        {/* Helper text */}
        <p className="text-xs text-gray-400 mt-2 text-center">
          Press Ctrl+Enter to submit • Click mic to use voice input
        </p>
      </div>
    </div>
  );
}