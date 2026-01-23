const API_BASE = "https://ai-bot-ikyi.onrender.com/api";

export async function uploadResume(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/upload-resume`, {
    method: "POST",
    body: formData,
  });

  return res.json();
}

export async function generateQuestions(parsedResume: any) {
  const res = await fetch(`${API_BASE}/generate-questions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ parsed_resume: parsedResume }),  // ✅ FIXED: Wrap in object
  });

  return res.json();
}

export async function startInterview(questions: any) {
  const res = await fetch(`${API_BASE}/start-interview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(questions),
  });

  return res.json();
}

export async function submitAnswer(interviewId: string, answer: string) {
  const res = await fetch(
    `${API_BASE}/submit-answer?interview_id=${interviewId}&answer=${answer}`,
    { method: "POST" }
  );

  return res.json();
}

export async function analyzeInterview(interviewId: string) {
  const res = await fetch(
    `${API_BASE}/analyze-interview?interview_id=${interviewId}`,
    { method: "POST" }
  );

  return res.json();
}