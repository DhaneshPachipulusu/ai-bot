"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { isAuthenticated } from "@/lib/auth";

export default function AuthCheck({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    // Allow login page without auth
    if (pathname === "/login") {
      setIsChecking(false);
      return;
    }

    // Check if user is authenticated
    if (!isAuthenticated()) {
      router.push("/login");
    } else {
      setIsChecking(false);
    }
  }, [pathname, router]);

  // Show loading while checking
  if (isChecking && pathname !== "/login") {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}