export function getUser() {
    if (typeof window === "undefined") return null;
    
    const userStr = localStorage.getItem("user");
    if (!userStr) return null;
    
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }
  
  export function isAuthenticated(): boolean {
    return getUser() !== null;
  }
  
  export function logout() {
    localStorage.removeItem("user");
    window.location.href = "/login";
  }
  
  export function requireAuth() {
    if (typeof window === "undefined") return;
    
    if (!isAuthenticated()) {
      window.location.href = "/login";
    }
  }