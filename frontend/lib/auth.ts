/**
 * Auth Helper
 * ===========
 * Authentication functions with role support
 */

export interface User {
  id: number;
  username: string;
  college: string;
  role: "student" | "admin";
}

/**
 * Get current logged in user
 */
export function getUser(): User | null {
  if (typeof window === "undefined") return null;
  
  const userStr = localStorage.getItem("user");
  if (!userStr) return null;
  
  try {
    return JSON.parse(userStr) as User;
  } catch {
    return null;
  }
}

/**
 * Check if user is logged in
 */
export function isAuthenticated(): boolean {
  return getUser() !== null;
}

/**
 * Check if current user is admin
 */
export function isAdmin(): boolean {
  const user = getUser();
  return user?.role === "admin";
}

/**
 * Check if current user is student
 */
export function isStudent(): boolean {
  const user = getUser();
  return user?.role === "student" || !user?.role;
}

/**
 * Logout and redirect to login
 */
export function logout() {
  localStorage.removeItem("user");
  window.location.href = "/login";
}

/**
 * Require authentication - redirect if not logged in
 */
export function requireAuth() {
  if (typeof window === "undefined") return;
  
  if (!isAuthenticated()) {
    window.location.href = "/login";
  }
}

/**
 * Require admin role - redirect if not admin
 */
export function requireAdmin() {
  if (typeof window === "undefined") return;
  
  const user = getUser();
  
  if (!user) {
    window.location.href = "/login";
    return;
  }
  
  if (user.role !== "admin") {
    window.location.href = "/dashboard";
    return;
  }
}

/**
 * Require student role - redirect if admin
 */
export function requireStudent() {
  if (typeof window === "undefined") return;
  
  const user = getUser();
  
  if (!user) {
    window.location.href = "/login";
    return;
  }
  
  if (user.role === "admin") {
    window.location.href = "/admin";
    return;
  }
}

/**
 * Get redirect path based on role
 */
export function getRedirectPath(): string {
  const user = getUser();
  if (!user) return "/login";
  return user.role === "admin" ? "/admin" : "/dashboard";
}