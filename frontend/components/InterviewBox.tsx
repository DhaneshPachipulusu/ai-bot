"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { getUser } from "@/lib/auth";
import {
  startConversationalInterview,
  respondToInterview,
  endConversationalInterview,
  InterviewMessage,
  InterviewState,
  PerformanceHint,
} from "@/lib/api";

export default function InterviewBox() {
  const router = useRouter();

  // Interview state
  const [interviewId, setInterviewId] = useState<string | null>(null);
  const [userId, setUserId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Conversation
  const [currentMessage, setCurrentMessage] = useState<InterviewMessage | null>(null);
  const [interviewState, setInterviewState] = useState<InterviewState | null>(null);
  const [performanceHint, setPerformanceHint] = useState<PerformanceHint | null>(null);

  // User input
  const [answer, setAnswer] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // AI states
  const [aiState, setAiState] = useState<"ready" | "speaking" | "listening" | "thinking">("ready");
  const [isCompleted, setIsCompleted] = useState(false);
  const [isPaused, setIsPaused] = useState(false);

  // Greeting & Conclusion state
  const [showGreeting, setShowGreeting] = useState(true);
  const [greetingText, setGreetingText] = useState("Welcome! Preparing your interview...");
  const [showConclusion, setShowConclusion] = useState(false);
  const [conclusionText, setConclusionText] = useState("");

  // Auto-mic state
  const [micCountdown, setMicCountdown] = useState<number | null>(null);
  const [silenceTimer, setSilenceTimer] = useState<number>(0);
  const [showSilenceWarning, setShowSilenceWarning] = useState(false);
  const [autoMicEnabled, setAutoMicEnabled] = useState(true);

  // Media state
  const [listening, setListening] = useState(false);
  const [cameraEnabled, setCameraEnabled] = useState(false);
  const [cameraOn, setCameraOn] = useState(true);
  const [micOn, setMicOn] = useState(true);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);

  // Camera error state
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [isRetryingCamera, setIsRetryingCamera] = useState(false);

  // Refs
  const recognitionRef = useRef<any>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const startedRef = useRef(false);

  // Mirror state into refs so the stable recognition handlers never read stale values
  const listeningRef = useRef(false);
  const isPausedRef = useRef(false);
  const voicesRef = useRef<SpeechSynthesisVoice[]>([]);

  // Auto-mic refs
  const micCountdownRef = useRef<NodeJS.Timeout | null>(null);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastSoundTimeRef = useRef<number>(Date.now());
  const silenceCheckRef = useRef<NodeJS.Timeout | null>(null);

  // Constants
  const MIC_COUNTDOWN_SECONDS = 5;
  const SILENCE_TIMEOUT_SECONDS = 8;
  const SILENCE_WARNING_SECONDS = 5;
  const SOUND_THRESHOLD = 15; // Audio level threshold to detect speech

  // Initialize
  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;

    const initInterview = async () => {
      const user = getUser();
      if (!user) {
        router.push("/login");
        return;
      }
      setUserId(user.id);

      const storedResume = sessionStorage.getItem("parsed_resume");
      const parsedResume = storedResume ? JSON.parse(storedResume) : null;
      const targetRole = sessionStorage.getItem("interview_role") || "Software Engineer";
      const difficulty = sessionStorage.getItem("interview_difficulty") || "auto";

      // Get candidate name for greeting
      const candidateName = parsedResume?.name || "there";

      try {
        setIsLoading(true);
        setError(null);

        // Show personalized greeting first
        setGreetingText(`Hi ${candidateName}! 👋`);

        // Wait a moment for greeting to be visible
        await new Promise(resolve => setTimeout(resolve, 1500));

        setGreetingText(`Setting up your ${targetRole} interview...`);

        const response = await startConversationalInterview({
          user_id: user.id,
          mode: parsedResume ? "resume" : "career",
          parsed_resume: parsedResume,
          target_role: targetRole,
          difficulty: difficulty as "auto" | "easy" | "medium" | "hard",
          max_questions: 12,
          max_duration_mins: 25,
        });

        setInterviewId(response.interview_id);
        sessionStorage.setItem("interviewId", response.interview_id);
        setCurrentMessage(response.message);
        setInterviewState(response.state);

        // Update greeting to show ready state
        setGreetingText(`Ready! Let's begin your interview.`);
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Hide greeting and start
        setShowGreeting(false);
        setIsLoading(false);

        // Initialize media first, then speak
        await initializeMedia();

        // Small delay before speaking first message
        setTimeout(() => {
          speakMessage(response.message.text);
        }, 500);

      } catch (err: any) {
        console.error("Failed to start interview:", err);
        setError(err.message || "Failed to start interview");
        setIsLoading(false);
      }
    };

    initInterview();
    return () => cleanup();
  }, [router]);

  // Media initialization with proper error handling
  const initializeMedia = async () => {
    try {
      setCameraError(null);

      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setCameraError("Your browser doesn't support camera access");
        return;
      }

      const devices = await navigator.mediaDevices.enumerateDevices();
      const hasCamera = devices.some(device => device.kind === 'videoinput');
      const hasMic = devices.some(device => device.kind === 'audioinput');

      if (!hasCamera) {
        setCameraError("No camera found on this device");
        if (hasMic) {
          await initializeAudioOnly();
        }
        return;
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: "user" },
        audio: true,
      });

      streamRef.current = stream;
      setCameraEnabled(true);
      setCameraError(null);

      const assignStream = () => {
        if (videoRef.current && streamRef.current) {
          videoRef.current.srcObject = streamRef.current;
          videoRef.current.play().catch(err => console.log("Play error:", err));
          return true;
        }
        return false;
      };

      if (!assignStream()) {
        const retryInterval = setInterval(() => {
          if (assignStream()) {
            clearInterval(retryInterval);
          }
        }, 100);
        setTimeout(() => clearInterval(retryInterval), 3000);
      }

      const audioContext = new AudioContext();
      const analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyser);
      analyser.fftSize = 256;

      audioContextRef.current = audioContext;
      analyserRef.current = analyser;
      startAudioAnalysis();

      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);

    } catch (err: any) {
      console.error("Media init error:", err);

      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setCameraError("Camera permission denied. Please allow camera access.");
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setCameraError("No camera found on this device");
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        setCameraError("Camera is in use by another application");
      } else if (err.name === 'OverconstrainedError') {
        setCameraError("Camera doesn't support required settings. Trying fallback...");
        await initializeMediaFallback();
      } else if (err.name === 'SecurityError') {
        setCameraError("Camera access blocked. Please use HTTPS.");
      } else {
        setCameraError(`Camera error: ${err.message || 'Unknown error'}`);
      }

      await initializeAudioOnly();
    }
  };

  const initializeMediaFallback = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current?.play();
          setCameraEnabled(true);
          setCameraError(null);
        };
      }

      setupAudioAnalysis(stream);
    } catch (err) {
      console.error("Fallback media init error:", err);
      await initializeAudioOnly();
    }
  };

  const initializeAudioOnly = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: false,
        audio: true,
      });

      streamRef.current = stream;
      setupAudioAnalysis(stream);

      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      console.error("Audio init error:", err);
    }
  };

  const setupAudioAnalysis = (stream: MediaStream) => {
    const audioContext = new AudioContext();
    const analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(stream);
    source.connect(analyser);
    analyser.fftSize = 256;

    audioContextRef.current = audioContext;
    analyserRef.current = analyser;
    startAudioAnalysis();
  };

  const retryCamera = async () => {
    setIsRetryingCamera(true);
    setCameraError(null);

    streamRef.current?.getTracks().forEach((t) => t.stop());

    await initializeMedia();
    setIsRetryingCamera(false);
  };

  const startAudioAnalysis = () => {
    const analyze = () => {
      if (!analyserRef.current) return;
      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
      analyserRef.current.getByteFrequencyData(dataArray);
      const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
      const level = Math.min(100, (avg / 128) * 100);
      setAudioLevel(level);

      // Track last sound time for silence detection
      if (level > SOUND_THRESHOLD && listening) {
        lastSoundTimeRef.current = Date.now();
        setShowSilenceWarning(false);
        setSilenceTimer(0);
      }

      animationFrameRef.current = requestAnimationFrame(analyze);
    };
    analyze();
  };

  const cleanup = () => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    audioContextRef.current?.close();
    if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    if (timerRef.current) clearInterval(timerRef.current);
    if (micCountdownRef.current) clearTimeout(micCountdownRef.current);
    if (silenceTimerRef.current) clearInterval(silenceTimerRef.current);
    if (silenceCheckRef.current) clearInterval(silenceCheckRef.current);
    speechSynthesis.cancel();
    recognitionRef.current?.stop();
  };

  // ==================== AUTO MIC FUNCTIONS ====================

  // Start mic countdown after AI finishes speaking
  const startMicCountdown = useCallback(() => {
    if (!autoMicEnabled || isPaused || isCompleted) return;

    // Clear any existing countdown
    if (micCountdownRef.current) {
      clearTimeout(micCountdownRef.current);
    }

    let countdown = MIC_COUNTDOWN_SECONDS;
    setMicCountdown(countdown);

    const tick = () => {
      countdown -= 1;
      setMicCountdown(countdown);

      if (countdown <= 0) {
        setMicCountdown(null);
        startListeningAuto();
      } else {
        micCountdownRef.current = setTimeout(tick, 1000);
      }
    };

    micCountdownRef.current = setTimeout(tick, 1000);
  }, [autoMicEnabled, isPaused, isCompleted]);

  // Cancel mic countdown
  const cancelMicCountdown = () => {
    if (micCountdownRef.current) {
      clearTimeout(micCountdownRef.current);
      micCountdownRef.current = null;
    }
    setMicCountdown(null);
  };

  // Start listening with silence detection
  const startListeningAuto = () => {
    if (isPaused || isCompleted || listening) return;

    listeningRef.current = true;
    setListening(true);
    setAiState("listening");
    lastSoundTimeRef.current = Date.now();
    setSilenceTimer(0);
    setShowSilenceWarning(false);

    try {
      recognitionRef.current?.start();
    } catch (e) {
      console.log("Recognition already started");
    }

    // Start silence detection
    startSilenceDetection();
  };

  // Silence detection
  const startSilenceDetection = () => {
    if (silenceCheckRef.current) {
      clearInterval(silenceCheckRef.current);
    }

    silenceCheckRef.current = setInterval(() => {
      if (!listening) {
        clearInterval(silenceCheckRef.current!);
        return;
      }

      const silenceDuration = (Date.now() - lastSoundTimeRef.current) / 1000;
      setSilenceTimer(Math.floor(silenceDuration));

      // Show warning when approaching timeout
      if (silenceDuration >= SILENCE_WARNING_SECONDS && !showSilenceWarning) {
        setShowSilenceWarning(true);
      }

      // Auto submit on timeout (only if there's an answer)
      if (silenceDuration >= SILENCE_TIMEOUT_SECONDS) {
        if (answer.trim()) {
          console.log("Silence detected, auto-submitting...");
          handleAutoSubmit();
        } else {
          // Reset silence timer if no answer yet
          lastSoundTimeRef.current = Date.now();
          setSilenceTimer(0);
        }
      }
    }, 500);
  };

  // Stop silence detection
  const stopSilenceDetection = () => {
    if (silenceCheckRef.current) {
      clearInterval(silenceCheckRef.current);
      silenceCheckRef.current = null;
    }
    setSilenceTimer(0);
    setShowSilenceWarning(false);
  };

  // Auto submit handler
  const handleAutoSubmit = () => {
    stopSilenceDetection();
    submitAnswer();
  };

  // Cancel auto-submit
  const cancelAutoSubmit = () => {
    lastSoundTimeRef.current = Date.now();
    setSilenceTimer(0);
    setShowSilenceWarning(false);
  };

  // ==================== TTS ====================

  const speakMessage = (text: string) => {
    speechSynthesis.cancel();
    cancelMicCountdown();
    stopSilenceDetection();
    setAiState("speaking");

    const utterance = new SpeechSynthesisUtterance(text);
    const voices = voicesRef.current.length ? voicesRef.current : speechSynthesis.getVoices();
    const find = (re: RegExp) => voices.find((v) => re.test(v.name) || re.test(v.lang));
    // INDIAN ACCENT first: natural online en-IN voices -> classic en-IN -> any en-IN ->
    // en-GB (closer to Indian than US) -> any English.
    const bestVoice =
      find(/Neerja|Prabhat/i) ||                                       // MS natural en-IN (online)
      voices.find((v) => v.lang === "en-IN" && /Natural|Online/i.test(v.name)) ||
      find(/Heera|Ravi/i) ||                                           // MS classic en-IN
      find(/Google.*(India|हिन्दी)/i) ||
      voices.find((v) => v.lang === "en-IN") ||
      voices.find((v) => /india/i.test(v.name)) ||
      voices.find((v) => v.lang === "en-GB") ||
      voices.find((v) => v.lang?.startsWith("en")) ||
      null;

    utterance.voice = bestVoice;
    utterance.lang = bestVoice?.lang || "en-IN";
    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    // Track if mic has been started to prevent double start
    let micStarted = false;

    const startMicAfterSpeech = () => {
      if (micStarted) return;
      micStarted = true;
      setAiState("ready");
      if (autoMicEnabled && !isPaused && !isCompleted) {
        startMicCountdown();
      }
    };

    utterance.onend = () => {
      startMicAfterSpeech();
    };

    utterance.onerror = () => {
      startMicAfterSpeech();
    };

    speechSynthesis.speak(utterance);

    // FALLBACK: If TTS onend doesn't fire within estimated time, start mic anyway
    // Estimate ~100ms per word + 2s buffer
    const estimatedDuration = Math.max(3000, text.split(' ').length * 100 + 2000);
    setTimeout(() => {
      if (!micStarted && aiState === "speaking") {
        console.log("⚠️ TTS onend fallback triggered");
        startMicAfterSpeech();
      }
    }, estimatedDuration);
  };

  // ==================== STT ====================

  // Keep refs in sync so the stable recognition handlers always read current state
  useEffect(() => { listeningRef.current = listening; }, [listening]);
  useEffect(() => { isPausedRef.current = isPaused; }, [isPaused]);

  // Load TTS voices once. getVoices() is empty until the browser loads them async,
  // so we also listen for "voiceschanged".
  useEffect(() => {
    const load = () => {
      voicesRef.current = window.speechSynthesis.getVoices();
      const en = voicesRef.current.filter((v) => v.lang?.toLowerCase().startsWith("en"));
      if (en.length) {
        console.log("🔊 Available English voices:", en.map((v) => `${v.name} (${v.lang})`));
        console.log("🇮🇳 Indian (en-IN) voices:", en.filter((v) => v.lang === "en-IN").map((v) => v.name));
      }
    };
    load();
    window.speechSynthesis.addEventListener("voiceschanged", load);
    return () => window.speechSynthesis.removeEventListener("voiceschanged", load);
  }, []);

  // Create ONE SpeechRecognition instance for the whole session.
  // Recreating it on every `listening` change left orphaned instances running,
  // which blocked the mic from restarting after the first answer.
  useEffect(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) return;

    const rec = new SR();
    rec.lang = "en-IN";
    rec.continuous = true;
    rec.interimResults = true;

    rec.onresult = (e: any) => {
      let final = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        if (e.results[i].isFinal) {
          final += e.results[i][0].transcript;
        }
      }
      if (final) {
        setAnswer((prev) => prev + final);
        // Reset silence timer when speech detected
        lastSoundTimeRef.current = Date.now();
        setShowSilenceWarning(false);
      }
    };

    // Browsers auto-stop recognition periodically; restart while we still want to listen.
    rec.onend = () => {
      if (listeningRef.current && !isPausedRef.current) {
        try { rec.start(); } catch { }
      } else {
        setListening(false);
        stopSilenceDetection();
      }
    };

    rec.onerror = (e: any) => {
      // no-speech / aborted are recoverable (onend restarts). Permission errors are not.
      if (e?.error === "not-allowed" || e?.error === "service-not-allowed") {
        listeningRef.current = false;
        setListening(false);
      }
    };

    recognitionRef.current = rec;
    return () => {
      try { rec.stop(); } catch { }
      recognitionRef.current = null;
    };
  }, []);

  const toggleListening = () => {
    cancelMicCountdown();

    if (listening) {
      listeningRef.current = false;
      recognitionRef.current?.stop();
      setListening(false);
      setAiState("ready");
      stopSilenceDetection();
    } else {
      listeningRef.current = true;
      setListening(true);
      setAiState("listening");
      lastSoundTimeRef.current = Date.now();
      try { recognitionRef.current?.start(); } catch { }
      startSilenceDetection();
    }
  };

  // ==================== SUBMIT ====================

  const submitAnswer = async () => {
    if (!answer.trim() || !interviewId || !userId || isSubmitting) return;

    cancelMicCountdown();
    stopSilenceDetection();

    if (listening) {
      listeningRef.current = false;
      recognitionRef.current?.stop();
      setListening(false);
    }

    const answerText = answer;
    setIsSubmitting(true);
    setAiState("thinking");
    setAnswer("");
    setPerformanceHint(null);

    try {
      const response = await respondToInterview(
        interviewId,
        userId,
        answerText,
        Math.ceil(answerText.split(" ").length * 0.5)
      );

      setCurrentMessage(response.message);
      setInterviewState(response.state);
      setPerformanceHint(response.performance_hint || null);

      if (response.is_complete) {
        handleComplete(response.message.text);
      } else {
        speakMessage(response.message.text);
      }

    } catch (err: any) {
      console.error("Submit error:", err);
      setError(err.message);
      setAiState("ready");
    } finally {
      setIsSubmitting(false);
    }
  };

  // ==================== CONTROLS ====================

  const handleComplete = (finalMessage?: string) => {
    cancelMicCountdown();
    stopSilenceDetection();
    cleanup();

    // Show conclusion
    setConclusionText(finalMessage || "Thank you for completing the interview!");
    setShowConclusion(true);

    // Speak conclusion
    if (finalMessage) {
      const utterance = new SpeechSynthesisUtterance(finalMessage);
      utterance.rate = 0.95;
      speechSynthesis.speak(utterance);
    }

    sessionStorage.setItem("interviewId", interviewId || "");

    // Wait for conclusion, then redirect
    setTimeout(() => {
      setIsCompleted(true);
      setTimeout(() => router.push("/report"), 2000);
    }, 4000);
  };

  const endInterview = async () => {
    if (!confirm("Are you sure you want to end the interview?")) return;
    try {
      const response = await endConversationalInterview(interviewId!, userId!, "user_ended");
      handleComplete("Thanks for your time! Your report is being generated.");
    } catch (err) {
      console.error("End interview error:", err);
      handleComplete();
    }
  };

  const togglePause = () => {
    if (!isPaused) {
      // Pausing
      cancelMicCountdown();
      stopSilenceDetection();
      speechSynthesis.cancel();
      listeningRef.current = false;
      recognitionRef.current?.stop();
      setListening(false);
    }
    setIsPaused(!isPaused);
  };

  const toggleCamera = () => {
    const track = streamRef.current?.getVideoTracks()[0];
    if (track) {
      track.enabled = !track.enabled;
      setCameraOn(track.enabled);
    }
  };

  const toggleMic = () => {
    const track = streamRef.current?.getAudioTracks()[0];
    if (track) {
      track.enabled = !track.enabled;
      setMicOn(track.enabled);
    }
  };

  const repeatMessage = () => {
    if (currentMessage && aiState !== "speaking") {
      speakMessage(currentMessage.text);
    }
  };

  const toggleAutoMic = () => {
    setAutoMicEnabled(!autoMicEnabled);
    if (autoMicEnabled) {
      cancelMicCountdown();
    }
  };

  // ==================== HELPERS ====================

  const formatTime = (s: number) =>
    `${Math.floor(s / 60).toString().padStart(2, "0")}:${(s % 60).toString().padStart(2, "0")}`;

  const getStageLabel = (stage: string) => {
    const labels: Record<string, string> = {
      greeting: "Getting Started",
      introduction: "Introduction",
      skills_deep_dive: "Technical",
      project_discussion: "Projects",
      behavioral: "Behavioral",
      situational: "Situational",
      closing: "Closing",
      completed: "Complete",
    };
    return labels[stage] || stage;
  };

  // ==================== RENDER: LOADING ====================

  if (isLoading || showGreeting) {
    return (
      <div className="fixed inset-0 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center max-w-md px-6">
          <div className="relative w-24 h-24 mx-auto mb-8">
            <div className="absolute inset-0 rounded-full border-4 border-blue-500/30"></div>
            <div className="absolute inset-0 rounded-full border-4 border-blue-500 border-t-transparent animate-spin"></div>
            <div className="absolute inset-4 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            </div>
          </div>
          <h2 className="text-2xl font-bold text-white mb-3">{greetingText}</h2>
          <div className="flex justify-center gap-1 mt-4">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>
      </div>
    );
  }

  // ==================== RENDER: ERROR ====================

  if (error) {
    return (
      <div className="fixed inset-0 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
        <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-8 max-w-md text-center">
          <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-white mb-2">Unable to Start Interview</h3>
          <p className="text-gray-400 mb-6">{error}</p>
          <button onClick={() => window.location.reload()} className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // ==================== RENDER: CONCLUSION ====================

  if (showConclusion) {
    return (
      <div className="fixed inset-0 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center max-w-lg px-6">
          <div className="w-24 h-24 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-12 h-12 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-3xl font-bold text-white mb-4">Great Job! 🎉</h2>
          <p className="text-gray-300 text-lg mb-2">{conclusionText}</p>
          <p className="text-gray-500 text-sm mt-6">Generating your personalized report...</p>
          <div className="flex justify-center gap-1 mt-4">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>
      </div>
    );
  }

  // ==================== RENDER: COMPLETED ====================

  if (isCompleted) {
    return (
      <div className="fixed inset-0 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-24 h-24 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-12 h-12 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-3xl font-bold text-white mb-3">Interview Complete!</h2>
          <p className="text-gray-400 mb-2">Redirecting to your report...</p>
        </div>
      </div>
    );
  }

  // ==================== RENDER: MAIN INTERVIEW ====================

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col">
      {/* Header */}
      <header className="flex-shrink-0 px-4 sm:px-6 py-4 border-b border-slate-700/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-white">AI Interview</h1>
              <p className="text-xs text-gray-400">{interviewState ? getStageLabel(interviewState.stage) : "Starting"}</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Auto-mic indicator */}
            <button
              onClick={toggleAutoMic}
              className={`hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full text-xs transition-colors ${autoMicEnabled ? "bg-green-500/20 text-green-400" : "bg-slate-700 text-gray-400"
                }`}
            >
              <span>Auto-Mic</span>
              <span>{autoMicEnabled ? "ON" : "OFF"}</span>
            </button>

            <div className="hidden sm:flex items-center gap-2 bg-slate-800/50 px-4 py-2 rounded-full">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              <span className="text-sm text-gray-300">{interviewState?.progress_percent || 0}%</span>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-400">Time</p>
              <p className="text-lg font-semibold text-white">{interviewState?.time_remaining_mins || 25}m</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Video Area */}
      <main className="flex-1 p-4 sm:p-6 flex flex-col sm:flex-row gap-4 sm:gap-6 min-h-0">
        {/* AI Interviewer */}
        <div className={`flex-1 relative rounded-2xl overflow-hidden min-h-[200px] sm:min-h-0 transition-all duration-300 ${aiState === "speaking"
            ? "ring-4 ring-green-400 shadow-lg shadow-green-400/30"
            : aiState === "thinking"
              ? "ring-4 ring-yellow-400 shadow-lg shadow-yellow-400/30"
              : "ring-2 ring-blue-500/30"
          }`}>
          <img
            src="/ai-interviewer.jpg"
            alt="AI Interviewer"
            className="absolute inset-0 w-full h-full object-cover"
          />

          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />

          {aiState === "speaking" && (
            <div className="absolute inset-0 bg-green-500/10 animate-pulse" />
          )}

          <div className="absolute bottom-4 left-4 flex items-center gap-2 bg-black/60 backdrop-blur-sm px-3 py-1.5 rounded-full">
            <div className={`w-2.5 h-2.5 rounded-full ${aiState === "speaking" ? "bg-green-400 animate-pulse" :
                aiState === "thinking" ? "bg-yellow-400 animate-pulse" :
                  "bg-blue-400"
              }`} />
            <span className="text-white text-sm font-medium">AI Interviewer</span>
            <span className="text-gray-300 text-sm">
              {aiState === "speaking" ? "• Speaking" : aiState === "thinking" ? "• Thinking" : "• Ready"}
            </span>
          </div>

          {aiState === "speaking" && (
            <div className="absolute bottom-4 right-4 flex items-end gap-1 bg-black/60 backdrop-blur-sm px-3 py-2 rounded-full">
              {[1, 2, 3, 4, 3, 2, 1].map((h, i) => (
                <div
                  key={i}
                  className="w-1.5 bg-green-400 rounded-full animate-pulse"
                  style={{ height: `${h * 6}px`, animationDelay: `${i * 0.08}s` }}
                />
              ))}
            </div>
          )}
        </div>

        {/* Your Camera */}
        <div className="flex-1 relative bg-slate-800/50 rounded-2xl overflow-hidden border border-slate-700/50 min-h-[200px] sm:min-h-0">
          <video ref={videoRef} autoPlay muted playsInline className={`w-full h-full object-cover scale-x-[-1] ${cameraEnabled && cameraOn ? "" : "hidden"}`} />

          {(!cameraEnabled || !cameraOn) && (
            <div className="absolute inset-0 flex flex-col items-center justify-center p-4">
              {cameraError ? (
                <>
                  <div className="w-20 h-20 sm:w-24 sm:h-24 bg-red-500/20 rounded-full flex items-center justify-center mb-3">
                    <svg className="w-10 h-10 sm:w-12 sm:h-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3l18 18" />
                    </svg>
                  </div>
                  <p className="text-red-400 text-center text-sm mb-3 px-4">{cameraError}</p>
                  <button
                    onClick={retryCamera}
                    disabled={isRetryingCamera}
                    className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2"
                  >
                    {isRetryingCamera ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        Retrying...
                      </>
                    ) : (
                      "Retry Camera"
                    )}
                  </button>
                </>
              ) : !cameraOn ? (
                <>
                  <div className="w-20 h-20 sm:w-24 sm:h-24 bg-slate-700 rounded-full flex items-center justify-center mb-3">
                    <svg className="w-10 h-10 sm:w-12 sm:h-12 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                  <p className="text-gray-400">Camera Off</p>
                </>
              ) : (
                <>
                  <div className="w-20 h-20 sm:w-24 sm:h-24 bg-slate-700 rounded-full flex items-center justify-center mb-3">
                    <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                  </div>
                  <p className="text-gray-400">Initializing camera...</p>
                </>
              )}
            </div>
          )}

          <div className="absolute top-4 left-4 flex items-center gap-2 bg-black/50 backdrop-blur-sm px-3 py-1.5 rounded-full">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            <span className="text-white text-sm font-medium">{formatTime(recordingTime)}</span>
          </div>

          <div className="absolute bottom-4 left-4 bg-black/50 backdrop-blur-sm px-3 py-1.5 rounded-full">
            <span className="text-white text-sm font-medium">You</span>
          </div>

          {/* Audio level indicator */}
          <div className="absolute bottom-4 right-4 flex items-end gap-0.5 h-6">
            {[...Array(5)].map((_, i) => (
              <div key={i} className={`w-1 rounded-full transition-all ${audioLevel > i * 20 ? "bg-green-400" : "bg-slate-600"}`} style={{ height: `${(i + 1) * 4 + 4}px` }} />
            ))}
          </div>

          {/* Mic Countdown Overlay */}
          {micCountdown !== null && (
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center">
              <div className="text-center">
                <div className="w-20 h-20 rounded-full border-4 border-blue-500 flex items-center justify-center mb-3 mx-auto">
                  <span className="text-4xl font-bold text-white">{micCountdown}</span>
                </div>
                <p className="text-white font-medium">Mic starting...</p>
                <button
                  onClick={cancelMicCountdown}
                  className="mt-3 px-4 py-1.5 bg-slate-700 text-gray-300 text-sm rounded-lg hover:bg-slate-600"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Question & Input */}
      <div className="flex-shrink-0 px-4 sm:px-6 pb-4 sm:pb-6 space-y-4">
        {/* Question */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/50 p-4 sm:p-6">
          <p className="text-white text-base sm:text-lg lg:text-xl leading-relaxed text-center">
            {currentMessage?.text || "Preparing your interview..."}
          </p>
        </div>

        {/* Silence Warning */}
        {showSilenceWarning && listening && (
          <div className="flex items-center justify-center gap-3 bg-amber-500/20 border border-amber-500/30 rounded-xl px-4 py-2">
            <span className="text-amber-400">⏱️</span>
            <span className="text-amber-400 text-sm">
              Submitting in {SILENCE_TIMEOUT_SECONDS - silenceTimer}s...
            </span>
            <button
              onClick={cancelAutoSubmit}
              className="px-3 py-1 bg-amber-500/30 text-amber-300 text-xs rounded-lg hover:bg-amber-500/40"
            >
              Keep talking
            </button>
          </div>
        )}

        {/* Performance Hint */}
        {performanceHint?.suggestion && !showSilenceWarning && (
          <div className="flex items-center justify-center gap-2 text-amber-400 text-sm">
            <span>💡</span>
            <span>{performanceHint.suggestion}</span>
          </div>
        )}

        {/* Input */}
        <div className="flex items-center gap-3">
          <div className="flex-1 relative">
            <textarea
              value={answer}
              onChange={(e) => {
                setAnswer(e.target.value);
                // Reset silence when typing
                lastSoundTimeRef.current = Date.now();
              }}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submitAnswer(); } }}
              placeholder={listening ? "🎤 Listening... speak now" : micCountdown ? `Mic in ${micCountdown}s...` : "Type your answer or wait for mic..."}
              disabled={isPaused || isSubmitting}
              rows={1}
              className={`w-full px-4 sm:px-6 py-3 sm:py-4 bg-slate-800/80 border rounded-xl sm:rounded-2xl text-white text-sm sm:text-base resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 placeholder:text-gray-500 ${listening ? "border-green-500 ring-2 ring-green-500/30" : "border-slate-700"
                }`}
            />
            {listening && (
              <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-1">
                {[1, 2, 3, 2, 1].map((h, i) => (
                  <div
                    key={i}
                    className="w-1 bg-green-400 rounded-full animate-pulse"
                    style={{ height: `${h * 4 + 4}px`, animationDelay: `${i * 0.1}s` }}
                  />
                ))}
              </div>
            )}
          </div>

          <button
            onClick={toggleListening}
            disabled={isPaused || isSubmitting}
            className={`w-12 h-12 sm:w-14 sm:h-14 rounded-xl sm:rounded-2xl flex items-center justify-center transition-all ${listening
                ? "bg-red-500 text-white shadow-lg shadow-red-500/40 animate-pulse"
                : micCountdown !== null
                  ? "bg-blue-500/50 text-white"
                  : "bg-slate-700 text-gray-300 hover:bg-slate-600"
              } disabled:opacity-50`}
          >
            <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
            </svg>
          </button>

          <button onClick={submitAnswer} disabled={!answer.trim() || isPaused || isSubmitting} className="w-12 h-12 sm:w-14 sm:h-14 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl sm:rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50 disabled:opacity-50 disabled:shadow-none transition-all">
            {isSubmitting ? <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>}
          </button>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-center gap-2 sm:gap-3 flex-wrap">
          <button onClick={toggleCamera} disabled={!!cameraError} className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg transition-colors ${cameraError ? "bg-red-500/20 text-red-400 cursor-not-allowed" : cameraOn ? "bg-slate-700 text-white" : "bg-red-500/20 text-red-400"}`}>
            <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
            <span className="hidden sm:inline text-sm">{cameraError ? "Error" : cameraOn ? "Camera" : "Off"}</span>
          </button>

          <button onClick={toggleMic} className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg transition-colors ${micOn ? "bg-slate-700 text-white" : "bg-red-500/20 text-red-400"}`}>
            <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" /></svg>
            <span className="hidden sm:inline text-sm">{micOn ? "Mic" : "Off"}</span>
          </button>

          <div className="w-px h-6 bg-slate-700" />

          <button
            onClick={toggleAutoMic}
            className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg transition-colors ${autoMicEnabled ? "bg-green-500/20 text-green-400" : "bg-slate-700 text-gray-400"
              }`}
          >
            <span className="text-sm">Auto</span>
          </button>

          <button onClick={repeatMessage} disabled={aiState === "speaking"} className="flex items-center gap-2 px-3 sm:px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 disabled:opacity-50 transition-colors">
            <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
            <span className="hidden sm:inline text-sm">Repeat</span>
          </button>

          <button onClick={togglePause} className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg transition-colors ${isPaused ? "bg-green-500/20 text-green-400" : "bg-slate-700 text-white hover:bg-slate-600"}`}>
            {isPaused ? <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" /></svg> : <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" /></svg>}
            <span className="hidden sm:inline text-sm">{isPaused ? "Resume" : "Pause"}</span>
          </button>

          <div className="w-px h-6 bg-slate-700" />

          <button onClick={endInterview} className="flex items-center gap-2 px-3 sm:px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors">
            <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" /></svg>
            <span className="hidden sm:inline text-sm">End</span>
          </button>
        </div>
      </div>

      {/* Pause Overlay */}
      {isPaused && (
        <div className="absolute inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-3xl p-8 sm:p-10 text-center shadow-2xl max-w-sm mx-4 border border-slate-700">
            <div className="w-20 h-20 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-10 h-10 text-blue-400" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
            </div>
            <h3 className="text-2xl font-bold text-white mb-2">Interview Paused</h3>
            <p className="text-gray-400 mb-8">Take a moment. Click resume when ready.</p>
            <button onClick={togglePause} className="w-full px-6 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-2xl font-semibold shadow-lg hover:shadow-xl transition-all">
              Resume Interview
            </button>
          </div>
        </div>
      )}
    </div>
  );
}