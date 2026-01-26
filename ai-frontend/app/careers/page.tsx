// app/careers/page.tsx
"use client";
import CareerInterview from "@/components/CareerInterview";

export default function CareersPage() {
  return (
    <div className="py-12 px-4">  // ← Remove bg-gray-50
      <CareerInterview />
    </div>
  );
}