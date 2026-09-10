"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import fresherJobsData from "@/data/fresher-jobs.json";

// Job interface - future-ready for DB migration
export interface FresherJob {
    id: string;
    title: string;
    company: string;
    location: string;
    apply_url: string;
    active: boolean;
}

interface FresherJobsContextType {
    jobs: FresherJob[];
    isLoading: boolean;
    hasJobs: boolean;
    jobCount: number;
    dismissed: boolean;
    dismissJobs: () => void;
    resetDismissed: () => void;
}

const FresherJobsContext = createContext<FresherJobsContextType | undefined>(undefined);

export function FresherJobsProvider({ children }: { children: ReactNode }) {
    const [jobs, setJobs] = useState<FresherJob[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [dismissed, setDismissed] = useState(false);

    useEffect(() => {
        // Load jobs from static JSON
        // In future, this can be replaced with API call to DB
        const loadJobs = () => {
            setIsLoading(true);
            try {
                // Filter active jobs and limit to 5
                const activeJobs = (fresherJobsData as FresherJob[])
                    .filter(job => job.active)
                    .slice(0, 5);
                setJobs(activeJobs);
            } catch (error) {
                console.error("Failed to load fresher jobs:", error);
                setJobs([]);
            } finally {
                setIsLoading(false);
            }
        };

        loadJobs();
    }, []);

    const dismissJobs = () => setDismissed(true);
    const resetDismissed = () => setDismissed(false);

    return (
        <FresherJobsContext.Provider
            value={{
                jobs,
                isLoading,
                hasJobs: jobs.length > 0,
                jobCount: jobs.length,
                dismissed,
                dismissJobs,
                resetDismissed,
            }}
        >
            {children}
        </FresherJobsContext.Provider>
    );
}

export function useFresherJobs() {
    const context = useContext(FresherJobsContext);
    if (context === undefined) {
        throw new Error("useFresherJobs must be used within a FresherJobsProvider");
    }
    return context;
}
