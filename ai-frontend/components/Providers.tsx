"use client";

import { FresherJobsProvider } from "@/lib/JobNotificationContext";

export default function Providers({ children }: { children: React.ReactNode }) {
    return (
        <FresherJobsProvider>
            {children}
        </FresherJobsProvider>
    );
}
