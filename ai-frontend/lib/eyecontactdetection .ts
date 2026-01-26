"use client";

import { useEffect, useRef, useState, useCallback } from "react";

/**
 * Eye Contact Detection Hook using MediaPipe Face Mesh
 * 
 * This runs entirely in the browser - NO backend needed!
 * 
 * How it works:
 * 1. MediaPipe Face Mesh detects 468 facial landmarks
 * 2. We extract eye landmarks (iris position)
 * 3. We calculate if eyes are looking at the camera based on iris position relative to eye corners
 * 4. We also detect if face is visible and facing forward
 */

interface FaceAnalysis {
  faceDetected: boolean;
  eyeContact: boolean;
  lookingDirection: "center" | "left" | "right" | "up" | "down";
  confidence: number;
  message: string;
}

interface UseEyeContactOptions {
  videoElement: HTMLVideoElement | null;
  enabled?: boolean;
  checkInterval?: number; // ms between checks
}

// MediaPipe Face Mesh landmark indices
const LEFT_EYE_IRIS = [468, 469, 470, 471, 472]; // Left iris landmarks
const RIGHT_EYE_IRIS = [473, 474, 475, 476, 477]; // Right iris landmarks
const LEFT_EYE_CORNERS = [33, 133]; // Left eye inner and outer corners
const RIGHT_EYE_CORNERS = [362, 263]; // Right eye inner and outer corners
const NOSE_TIP = 1;
const FOREHEAD = 10;
const CHIN = 152;

export function useEyeContactDetection({ videoElement, enabled = true, checkInterval = 500 }: UseEyeContactOptions) {
  const [analysis, setAnalysis] = useState<FaceAnalysis>({
    faceDetected: true,
    eyeContact: true,
    lookingDirection: "center",
    confidence: 1,
    message: "Looking at screen ✓",
  });

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const faceMeshRef = useRef<any>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const lastResultRef = useRef<any>(null);

  // Initialize MediaPipe Face Mesh
  const initializeFaceMesh = useCallback(async () => {
    if (!enabled || !videoElement) return;

    try {
      setIsLoading(true);

      // Dynamically import MediaPipe
      // @ts-ignore
      const { FaceMesh } = await import("@mediapipe/face_mesh");
      // @ts-ignore
      const { Camera } = await import("@mediapipe/camera_utils");

      const faceMesh = new FaceMesh({
        locateFile: (file: string) => {
          return `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`;
        },
      });

      faceMesh.setOptions({
        maxNumFaces: 1,
        refineLandmarks: true, // Enables iris landmarks
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5,
      });

      faceMesh.onResults((results: any) => {
        lastResultRef.current = results;
        processResults(results);
      });

      faceMeshRef.current = faceMesh;

      // Use Camera utility for continuous processing
      const camera = new Camera(videoElement, {
        onFrame: async () => {
          if (faceMeshRef.current && videoElement.readyState >= 2) {
            await faceMeshRef.current.send({ image: videoElement });
          }
        },
        width: 640,
        height: 480,
      });

      await camera.start();
      setIsLoading(false);
    } catch (err) {
      console.error("Failed to initialize face detection:", err);
      setError("Face detection unavailable");
      setIsLoading(false);
      
      // Fallback to simulation if MediaPipe fails to load
      startSimulation();
    }
  }, [enabled, videoElement]);

  // Process MediaPipe results
  const processResults = useCallback((results: any) => {
    if (!results.multiFaceLandmarks || results.multiFaceLandmarks.length === 0) {
      setAnalysis({
        faceDetected: false,
        eyeContact: false,
        lookingDirection: "center",
        confidence: 0,
        message: "Face not visible ⚠️",
      });
      return;
    }

    const landmarks = results.multiFaceLandmarks[0];

    // Calculate eye contact
    const eyeContactData = calculateEyeContact(landmarks);
    const headPose = calculateHeadPose(landmarks);

    // Combine eye gaze and head pose for final determination
    const isLookingAtCamera =
      eyeContactData.isLookingCenter &&
      headPose.isFacingForward &&
      eyeContactData.confidence > 0.6;

    let message = "";
    let direction: "center" | "left" | "right" | "up" | "down" = "center";

    if (!headPose.isFacingForward) {
      if (headPose.yaw > 0.15) {
        message = "Turn head right 👉";
        direction = "left";
      } else if (headPose.yaw < -0.15) {
        message = "Turn head left 👈";
        direction = "right";
      } else if (headPose.pitch > 0.15) {
        message = "Look down slightly 👇";
        direction = "up";
      } else if (headPose.pitch < -0.15) {
        message = "Look up slightly 👆";
        direction = "down";
      }
    } else if (!eyeContactData.isLookingCenter) {
      if (eyeContactData.gazeX > 0.6) {
        message = "Eyes looking right 👀";
        direction = "right";
      } else if (eyeContactData.gazeX < 0.4) {
        message = "Eyes looking left 👀";
        direction = "left";
      } else {
        message = "Look at the camera 👀";
      }
    } else {
      message = "Looking at screen ✓";
    }

    setAnalysis({
      faceDetected: true,
      eyeContact: isLookingAtCamera,
      lookingDirection: direction,
      confidence: eyeContactData.confidence,
      message,
    });
  }, []);

  // Calculate eye contact from iris landmarks
  const calculateEyeContact = (landmarks: any[]) => {
    try {
      // Get iris center positions
      const leftIris = landmarks[468]; // Left iris center
      const rightIris = landmarks[473]; // Right iris center

      // Get eye corner positions
      const leftEyeInner = landmarks[133];
      const leftEyeOuter = landmarks[33];
      const rightEyeInner = landmarks[362];
      const rightEyeOuter = landmarks[263];

      // Calculate horizontal position of iris within eye (0 = outer, 1 = inner)
      const leftEyeWidth = Math.abs(leftEyeOuter.x - leftEyeInner.x);
      const rightEyeWidth = Math.abs(rightEyeOuter.x - rightEyeInner.x);

      const leftGazeX = (leftIris.x - leftEyeOuter.x) / leftEyeWidth;
      const rightGazeX = (rightIris.x - rightEyeOuter.x) / rightEyeWidth;

      // Average gaze position
      const avgGazeX = (leftGazeX + rightGazeX) / 2;

      // Looking center if gaze is roughly in the middle (0.35 - 0.65)
      const isLookingCenter = avgGazeX > 0.35 && avgGazeX < 0.65;

      // Confidence based on how centered the gaze is
      const centerDistance = Math.abs(avgGazeX - 0.5);
      const confidence = Math.max(0, 1 - centerDistance * 2);

      return {
        isLookingCenter,
        gazeX: avgGazeX,
        confidence,
      };
    } catch (e) {
      return { isLookingCenter: true, gazeX: 0.5, confidence: 0.5 };
    }
  };

  // Calculate head pose from landmarks
  const calculateHeadPose = (landmarks: any[]) => {
    try {
      const noseTip = landmarks[NOSE_TIP];
      const forehead = landmarks[FOREHEAD];
      const chin = landmarks[CHIN];

      // Simple head pose estimation
      // Yaw: horizontal rotation (looking left/right)
      const yaw = noseTip.x - 0.5; // Deviation from center

      // Pitch: vertical rotation (looking up/down)
      const faceHeight = Math.abs(forehead.y - chin.y);
      const noseRelativeY = (noseTip.y - forehead.y) / faceHeight;
      const pitch = noseRelativeY - 0.4; // Expected ratio when facing forward

      const isFacingForward = Math.abs(yaw) < 0.15 && Math.abs(pitch) < 0.15;

      return { yaw, pitch, isFacingForward };
    } catch (e) {
      return { yaw: 0, pitch: 0, isFacingForward: true };
    }
  };

  // Fallback simulation when MediaPipe unavailable
  const startSimulation = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);

    intervalRef.current = setInterval(() => {
      const random = Math.random();

      if (random > 0.85) {
        setAnalysis({
          faceDetected: false,
          eyeContact: false,
          lookingDirection: "center",
          confidence: 0,
          message: "Face not visible ⚠️",
        });
      } else if (random > 0.7) {
        const directions = ["left", "right", "up", "down"] as const;
        const dir = directions[Math.floor(Math.random() * directions.length)];
        setAnalysis({
          faceDetected: true,
          eyeContact: false,
          lookingDirection: dir,
          confidence: 0.5,
          message: "Look at the camera 👀",
        });
      } else {
        setAnalysis({
          faceDetected: true,
          eyeContact: true,
          lookingDirection: "center",
          confidence: 0.9,
          message: "Looking at screen ✓",
        });
      }
    }, checkInterval);
  }, [checkInterval]);

  // Initialize on mount
  useEffect(() => {
    if (videoElement && enabled) {
      initializeFaceMesh();
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (faceMeshRef.current) {
        faceMeshRef.current.close?.();
      }
    };
  }, [videoElement, enabled, initializeFaceMesh]);

  return {
    analysis,
    isLoading,
    error,
  };
}

/**
 * Simplified hook that doesn't require MediaPipe (mock/simulation only)
 * Use this for development or when MediaPipe isn't available
 */
export function useSimulatedEyeContact(enabled: boolean = true, intervalMs: number = 3000) {
  const [analysis, setAnalysis] = useState<FaceAnalysis>({
    faceDetected: true,
    eyeContact: true,
    lookingDirection: "center",
    confidence: 1,
    message: "Looking at screen ✓",
  });

  useEffect(() => {
    if (!enabled) return;

    const interval = setInterval(() => {
      const random = Math.random();

      if (random > 0.88) {
        // 12% chance: Face not visible
        setAnalysis({
          faceDetected: false,
          eyeContact: false,
          lookingDirection: "center",
          confidence: 0,
          message: "Face not visible ⚠️",
        });
      } else if (random > 0.75) {
        // 13% chance: Looking away
        const messages = [
          { dir: "left" as const, msg: "Eyes looking left 👀" },
          { dir: "right" as const, msg: "Eyes looking right 👀" },
          { dir: "up" as const, msg: "Look at the camera 👀" },
        ];
        const choice = messages[Math.floor(Math.random() * messages.length)];
        setAnalysis({
          faceDetected: true,
          eyeContact: false,
          lookingDirection: choice.dir,
          confidence: 0.6,
          message: choice.msg,
        });
      } else {
        // 75% chance: Good eye contact
        setAnalysis({
          faceDetected: true,
          eyeContact: true,
          lookingDirection: "center",
          confidence: 0.95,
          message: "Looking at screen ✓",
        });
      }
    }, intervalMs);

    return () => clearInterval(interval);
  }, [enabled, intervalMs]);

  return analysis;
}

export default useEyeContactDetection;