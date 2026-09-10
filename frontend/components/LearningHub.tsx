"use client";

import { useState, useEffect } from "react";
import { API_URL } from "@/lib/config";

interface Branch {
    id: string;
    name: string;
    icon: string;
    color: string;
    description: string;
}

interface Topic {
    id: string;
    title: string;
    icon: string;
    description: string;
    subtopics?: number;
}

interface NoteItem {
    id: string;
    title: string;
    icon: string;
    keyPoints: string[];
    mustKnow: string[];
    practiceTopics: string[];
}

interface TopicNotes {
    topic: string;
    notes: NoteItem[];
}

export default function LearningHub() {
    const [branches, setBranches] = useState<Branch[]>([]);
    const [selectedBranch, setSelectedBranch] = useState<string>("cse");
    const [topics, setTopics] = useState<Topic[]>([]);
    const [selectedTopic, setSelectedTopic] = useState<Topic | null>(null);
    const [notes, setNotes] = useState<TopicNotes | null>(null);
    const [loading, setLoading] = useState(true);
    const [notesLoading, setNotesLoading] = useState(false);

    // Fetch branches on mount
    useEffect(() => {
        fetch(`${API_URL}/api/learning/branches`)
            .then((res) => res.json())
            .then((data) => {
                if (data.branches) {
                    setBranches(data.branches);
                    // Default to first branch if available
                    if (data.branches.length > 0) {
                        setSelectedBranch(data.branches[0].id);
                    }
                }
                setLoading(false);
            })
            .catch((err) => {
                console.error("Failed to fetch branches:", err);
                setLoading(false);
            });
    }, []);

    // Fetch topics when branch changes
    useEffect(() => {
        if (!selectedBranch) return;

        setTopics([]);
        setSelectedTopic(null);
        setNotes(null);

        fetch(`${API_URL}/api/learning/${selectedBranch}`)
            .then((res) => res.json())
            .then((data) => {
                if (data.topics) {
                    setTopics(data.topics);
                }
            })
            .catch((err) => console.error("Failed to fetch topics:", err));
    }, [selectedBranch]);

    // Fetch notes when topic selected
    async function handleTopicClick(topic: Topic) {
        setSelectedTopic(topic);
        setNotesLoading(true);

        try {
            const res = await fetch(`${API_URL}/api/learning/${selectedBranch}/${topic.id}`);
            if (res.ok) {
                const data = await res.json();
                setNotes(data);
            } else {
                setNotes({ topic: topic.title, notes: [] });
            }
        } catch (err) {
            console.error("Failed to fetch notes:", err);
            setNotes({ topic: topic.title, notes: [] });
        } finally {
            setNotesLoading(false);
        }
    }

    if (loading) {
        return <div className="p-12 text-center text-gray-400">Loading learning hub...</div>;
    }

    return (
        <div className="max-w-6xl mx-auto space-y-8">
            {/* Header */}
            <div className="text-center">
                <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400 mb-3">
                    Learning & Preparation Hub
                </h1>
                <p className="text-gray-400 max-w-2xl mx-auto">
                    Select your branch and master the core concepts needed for your interview.
                    Curated notes and roadmaps for every career path.
                </p>
            </div>

            {/* Branch Tabs */}
            <div className="flex flex-wrap justify-center gap-2">
                {branches.map((branch) => (
                    <button
                        key={branch.id}
                        onClick={() => setSelectedBranch(branch.id)}
                        className={`tab-base ${selectedBranch === branch.id
                            ? "tab-active"
                            : "tab-inactive"
                            }`}
                    >
                        <span className="mr-2">{branch.icon}</span>
                        {branch.name}
                    </button>
                ))}
            </div>

            {!selectedTopic ? (
                /* Topics Grid */
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    {topics.map((topic) => (
                        <div
                            key={topic.id}
                            onClick={() => handleTopicClick(topic)}
                            className="card-interactive group min-h-[160px] flex flex-col justify-between"
                        >
                            <div>
                                <div className="flex justify-between items-start mb-3">
                                    <span className="text-3xl p-3 bg-slate-700/50 rounded-xl group-hover:scale-110 transition-transform duration-300 block">
                                        {topic.icon}
                                    </span>
                                    <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded-full border border-slate-700">
                                        Topic
                                    </span>
                                </div>
                                <h3 className="text-lg font-bold text-gray-100 mb-1 leading-tight">
                                    {topic.title}
                                </h3>
                                <p className="text-sm text-gray-400">
                                    {topic.description}
                                </p>
                            </div>
                            <div className="mt-4 flex items-center text-blue-400 text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity transform translate-x-[-10px] group-hover:translate-x-0 duration-300">
                                View Notes →
                            </div>
                        </div>
                    ))}
                    {topics.length === 0 && (
                        <div className="col-span-full py-12 text-center border-2 border-dashed border-slate-700 rounded-2xl bg-slate-800/30">
                            <span className="text-4xl block mb-2">🚧</span>
                            <h3 className="text-xl font-medium text-gray-300">Content Coming Soon</h3>
                            <p className="text-gray-500 mt-2">
                                We are currently adding topics for this branch.
                            </p>
                        </div>
                    )}
                </div>
            ) : (
                /* Notes View */
                <div className="animate-in fade-in slide-in-from-right-8 duration-500">
                    <button
                        onClick={() => setSelectedTopic(null)}
                        className="mb-6 flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
                    >
                        ← Back to Topics
                    </button>

                    <div className="flex items-center gap-3 mb-8">
                        <span className="text-4xl">{selectedTopic.icon}</span>
                        <div>
                            <h2 className="text-3xl font-bold">{selectedTopic.title}</h2>
                            <p className="text-gray-400">Preparation notes & key concepts</p>
                        </div>
                    </div>

                    {notesLoading ? (
                        <div className="p-12 text-center bg-slate-800/50 rounded-2xl">
                            <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                            Loading notes...
                        </div>
                    ) : notes && notes.notes && notes.notes.length > 0 ? (
                        <div className="grid gap-6">
                            {notes.notes.map((note, idx) => (
                                <div key={idx} className="bg-slate-800/80 border border-slate-700 rounded-2xl p-6 md:p-8">
                                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-700">
                                        <span className="text-2xl">{note.icon}</span>
                                        <h3 className="text-xl font-bold text-blue-100">{note.title}</h3>
                                    </div>

                                    <div className="grid md:grid-cols-2 gap-8">
                                        {/* Key Points */}
                                        <div className="space-y-4">
                                            <h4 className="text-emerald-400 font-semibold text-sm uppercase tracking-wider flex items-center gap-2">
                                                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
                                                Key Concepts
                                            </h4>
                                            <ul className="space-y-2">
                                                {note.keyPoints.map((point, k) => (
                                                    <li key={k} className="flex items-start gap-2 text-gray-300 text-sm leading-relaxed">
                                                        <span className="text-emerald-500/50 mt-1">•</span>
                                                        {point}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>

                                        {/* Must Know */}
                                        <div className="space-y-4">
                                            <h4 className="text-amber-400 font-semibold text-sm uppercase tracking-wider flex items-center gap-2">
                                                <span className="h-1.5 w-1.5 rounded-full bg-amber-400"></span>
                                                Interview Checklist
                                            </h4>
                                            <div className="bg-amber-500/5 rounded-xl p-4 border border-amber-500/10">
                                                <ul className="space-y-2">
                                                    {note.mustKnow.map((item, k) => (
                                                        <li key={k} className="flex items-center gap-2 text-gray-300 text-sm">
                                                            <span className="text-amber-500">✓</span>
                                                            {item}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Practice Topics */}
                                    <div className="mt-6 pt-6 border-t border-slate-700/50 flex flex-wrap gap-2 items-center">
                                        <span className="text-xs font-semibold text-slate-500 uppercase mr-2">Focus Areas:</span>
                                        {note.practiceTopics.map((tag, t) => (
                                            <span key={t} className="px-3 py-1 bg-slate-700 text-slate-300 rounded-full text-xs border border-slate-600">
                                                {tag}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="p-12 text-center bg-slate-800/30 rounded-2xl border border-dashed border-slate-700">
                            <span className="text-4xl block mb-2">📓</span>
                            <h3 className="text-lg font-medium text-gray-300">Notes Not Available</h3>
                            <p className="text-gray-500 mt-1">Detailed notes for this topic are being prepared.</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
