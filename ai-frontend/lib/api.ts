/**
 * API Functions
 * =============
 * Centralized API for AI Interview Bot
 */

import { API_URL } from "./config";

// ======================
// RESUME ENDPOINTS
// ======================

export async function uploadResume(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_URL}/api/upload-resume`, {
    method: "POST",
    body: formData,
  });

  return res.json();
}

export async function generateQuestions(parsedResume: any) {
  const res = await fetch(`${API_URL}/api/generate-questions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ parsed_resume: parsedResume }),
  });

  return res.json();
}

// ======================
// LEGACY INTERVIEW ENDPOINTS
// ======================

export async function startInterview(questions: any) {
  const res = await fetch(`${API_URL}/api/start-interview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(questions),
  });

  return res.json();
}

export async function submitAnswer(interviewId: string, answer: string) {
  const res = await fetch(
    `${API_URL}/api/submit-answer?interview_id=${interviewId}&answer=${encodeURIComponent(answer)}`,
    { method: "POST" }
  );

  return res.json();
}

export async function analyzeInterview(interviewId: string) {
  const res = await fetch(
    `${API_URL}/api/analyze-interview?interview_id=${interviewId}`,
    { method: "POST" }
  );

  return res.json();
}

// ======================
// CONVERSATIONAL INTERVIEW - TYPES
// ======================

export interface InterviewMessage {
  type: string;
  acknowledgment?: string;
  text: string;
  audio_text?: string;
  topic?: string;
}

export interface InterviewState {
  stage: string;
  progress_percent: number;
  topics_covered: string[];
  current_topic?: string;
  questions_asked: number;
  questions_remaining: number;
  time_elapsed_mins: number;
  time_remaining_mins: number;
}

export interface PerformanceHint {
  answer_quality: string;
  suggestion?: string;
}

export interface StartInterviewResponse {
  interview_id: string;
  message: InterviewMessage;
  state: InterviewState;
}

export interface RespondResponse {
  message: InterviewMessage;
  state: InterviewState;
  performance_hint?: PerformanceHint;
  is_complete: boolean;
}

export interface EndInterviewResponse {
  message: InterviewMessage;
  summary: {
    duration_mins: number;
    questions_answered: number;
    strong_areas: string[];
    areas_to_improve: string[];
    overall_performance: string;
  };
  report_id: string;
}

// ======================
// CONVERSATIONAL INTERVIEW - FUNCTIONS
// ======================

/**
 * Start a new conversational interview
 */
export async function startConversationalInterview(request: {
  user_id: number;
  mode: "resume" | "career";
  parsed_resume?: any;
  target_role?: string;
  experience_level?: string;
  difficulty?: "auto" | "easy" | "medium" | "hard";
  max_questions?: number;
  max_duration_mins?: number;
}): Promise<StartInterviewResponse> {
  const res = await fetch(`${API_URL}/api/interview/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to start interview" }));
    throw new Error(error.detail || "Failed to start interview");
  }

  return res.json();
}

/**
 * Send answer and get AI response
 */
export async function respondToInterview(
  interviewId: string,
  userId: number,
  answer: string,
  answerDurationSeconds?: number
): Promise<RespondResponse> {
  const res = await fetch(`${API_URL}/api/interview/respond`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      interview_id: interviewId,
      user_id: userId,
      answer: answer,
      answer_duration_seconds: answerDurationSeconds,
    }),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to process answer" }));
    throw new Error(error.detail || "Failed to process answer");
  }

  return res.json();
}

/**
 * End the interview
 */
export async function endConversationalInterview(
  interviewId: string,
  userId: number,
  reason: "user_ended" | "time_limit" | "completed" = "user_ended"
): Promise<EndInterviewResponse> {
  const res = await fetch(`${API_URL}/api/interview/end`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      interview_id: interviewId,
      user_id: userId,
      reason: reason,
    }),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to end interview" }));
    throw new Error(error.detail || "Failed to end interview");
  }

  return res.json();
}

/**
 * Get interview status
 */
export async function getInterviewStatus(interviewId: string, userId: number) {
  const res = await fetch(
    `${API_URL}/api/interview/${interviewId}/status?user_id=${userId}`,
    { method: "GET" }
  );

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to get status" }));
    throw new Error(error.detail || "Failed to get status");
  }

  return res.json();
}

/**
 * Get conversation history
 */
export async function getInterviewHistory(interviewId: string, userId: number) {
  const res = await fetch(
    `${API_URL}/api/interview/${interviewId}/history?user_id=${userId}`,
    { method: "GET" }
  );

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to get history" }));
    throw new Error(error.detail || "Failed to get history");
  }

  return res.json();
}