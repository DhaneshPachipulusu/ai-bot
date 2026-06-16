"use client";

import { useState, useCallback, useEffect } from "react";
import { API_URL } from "@/lib/config";
import dynamic from "next/dynamic";

const ParticleBackground = dynamic(() => import("@/components/ParticleBackground"), {
    ssr: false,
});

/* ═══════════════════════════════════════
   TYPE DEFINITIONS — Locked Schema
   ═══════════════════════════════════════ */
interface Basics {
    full_name: string;
    phone: string;
    email: string;
    location: string;
    linkedin: string;
    github: string;
}
interface Skills {
    languages: string[];
    cloud_infrastructure: string[];
    devops_automation: string[];
    databases: string[];
    monitoring: string[];
    frameworks_tools: string[];
}
interface Experience {
    company: string;
    role: string;
    start_date: string;
    end_date: string;
    bullets: string[];
}
interface Project {
    name: string;
    type: string;
    year: string;
    bullets: string[];
}
interface Education {
    degree: string;
    institution: string;
    cgpa: string;
    start_year: string;
    end_year: string;
}
interface ResumeSchema {
    basics: Basics;
    summary: string;
    skills: Skills;
    experience: Experience[];
    projects: Project[];
    education: Education[];
    certifications: string[];
    achievements: string[];
}

const EMPTY_SKILLS: Skills = {
    languages: [], cloud_infrastructure: [], devops_automation: [],
    databases: [], monitoring: [], frameworks_tools: []
};

const SKILL_LABELS: Record<keyof Skills, string> = {
    languages: "Languages",
    cloud_infrastructure: "Cloud & Infrastructure",
    devops_automation: "DevOps & Automation",
    databases: "Databases",
    monitoring: "Monitoring",
    frameworks_tools: "Frameworks & Tools"
};

/* ═══════════════════════════════════════
   MAIN PAGE COMPONENT
   ═══════════════════════════════════════ */
export default function ResumeBuilderPage() {
    const [step, setStep] = useState<1 | 2 | 3>(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [schema, setSchema] = useState<ResumeSchema | null>(null);
    const [score, setScore] = useState(0);
    const [optimizedScore, setOptimizedScore] = useState(0);
    const [pdfUrl, setPdfUrl] = useState("");
    const [pdfFilename, setPdfFilename] = useState("");

    /* ── Session Persistence: Restore on mount ── */
    useEffect(() => {
        try {
            const saved = sessionStorage.getItem("resume_session");
            if (saved) {
                const data = JSON.parse(saved);
                if (data.schema) {
                    setSchema(data.schema);
                    setStep(data.step || 2);
                    setScore(data.score || 0);
                    setOptimizedScore(data.optimizedScore || 0);
                }
            }
        } catch { }
    }, []);

    /* ── Session Persistence: Save on changes ── */
    useEffect(() => {
        if (schema) {
            try {
                sessionStorage.setItem("resume_session", JSON.stringify({
                    schema, step, score, optimizedScore
                }));
            } catch { }
        }
    }, [schema, step, score, optimizedScore]);

    /* ── STEP 1: Upload ── */
    const handleUpload = useCallback(async (file: File) => {
        setError("");
        setLoading(true);
        try {
            const form = new FormData();
            form.append("file", file);
            const res = await fetch(`${API_URL}/api/resume-builder/parse`, {
                method: "POST",
                body: form,
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: "Upload failed" }));
                throw new Error(err.detail || "Upload failed");
            }
            const data = await res.json();
            setSchema(data.schema);
            setScore(data.score);
            setStep(2);
        } catch (e: any) {
            setError(e.message || "Upload failed");
        } finally {
            setLoading(false);
        }
    }, []);

    /* ── STEP 2 → 3: Optimize ── */
    const handleOptimize = useCallback(async () => {
        if (!schema) return;
        setError("");
        setLoading(true);
        try {
            const res = await fetch(`${API_URL}/api/resume-builder/optimize`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ schema_data: schema }),
            });
            if (!res.ok) throw new Error("Optimization failed");
            const data = await res.json();
            setSchema(data.schema);
            setOptimizedScore(data.after_score);
            setStep(3);
        } catch (e: any) {
            setError(e.message || "Optimization failed");
        } finally {
            setLoading(false);
        }
    }, [schema]);

    /* ── STEP 3: Generate PDF ── */
    const handleGenerate = useCallback(async () => {
        if (!schema) return;
        setError("");
        setLoading(true);
        try {
            const res = await fetch(`${API_URL}/api/resume-builder/generate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ schema_data: schema }),
            });
            if (!res.ok) throw new Error("PDF generation failed");
            const data = await res.json();
            setPdfUrl(`${API_URL}${data.pdf_url}`);
            setPdfFilename(data.pdf_filename);
            setOptimizedScore(data.final_score);
        } catch (e: any) {
            setError(e.message || "Generation failed");
        } finally {
            setLoading(false);
        }
    }, [schema]);

    /* ── Restart ── */
    const handleRestart = () => {
        setStep(1);
        setSchema(null);
        setScore(0);
        setOptimizedScore(0);
        setPdfUrl("");
        setPdfFilename("");
        setError("");
        sessionStorage.removeItem("resume_session");
    };

    return (
        <div className="min-h-screen relative">
            <ParticleBackground />
            <div className="relative z-10 max-w-5xl mx-auto px-4 py-8">
                {/* Header */}
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                        Resume Intelligence Engine
                    </h1>
                    <p className="text-slate-400 mt-2 text-sm">
                        Upload your resume · Review & edit · Generate a premium ATS-ready PDF
                    </p>
                </div>

                {/* Progress Steps */}
                <div className="flex items-center justify-center gap-2 mb-8">
                    {[
                        { n: 1, label: "Upload" },
                        { n: 2, label: "Review & Edit" },
                        { n: 3, label: "Generate" },
                    ].map(({ n, label }) => (
                        <div key={n} className="flex items-center gap-2">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold border-2 transition-all
                                ${step >= n ? "bg-blue-500/20 border-blue-400 text-blue-300" : "border-slate-600 text-slate-500"}
                            `}>{n}</div>
                            <span className={`text-sm hidden sm:inline ${step >= n ? "text-blue-300" : "text-slate-500"}`}>{label}</span>
                            {n < 3 && <div className={`w-12 h-0.5 ${step > n ? "bg-blue-400" : "bg-slate-700"}`} />}
                        </div>
                    ))}
                </div>

                {/* Error */}
                {error && (
                    <div className="bg-red-500/10 border border-red-500/30 text-red-300 px-4 py-3 rounded-xl mb-6 text-sm text-center">
                        {error}
                    </div>
                )}

                {/* ═══════════ STEP 1: UPLOAD ═══════════ */}
                {step === 1 && <UploadStep loading={loading} onUpload={handleUpload} />}

                {/* ═══════════ STEP 2: REVIEW & EDIT ═══════════ */}
                {step === 2 && schema && (
                    <ReviewStep
                        schema={schema}
                        score={score}
                        loading={loading}
                        onChange={setSchema}
                        onOptimize={handleOptimize}
                        onBack={() => setStep(1)}
                    />
                )}

                {/* ═══════════ STEP 3: GENERATE ═══════════ */}
                {step === 3 && schema && (
                    <GenerateStep
                        schema={schema}
                        score={optimizedScore}
                        loading={loading}
                        pdfUrl={pdfUrl}
                        pdfFilename={pdfFilename}
                        onChange={setSchema}
                        onGenerate={handleGenerate}
                        onRestart={handleRestart}
                        onBack={() => setStep(2)}
                    />
                )}
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════
   STEP 1 — Upload Component
   ═══════════════════════════════════════ */
function UploadStep({ loading, onUpload }: { loading: boolean; onUpload: (f: File) => void }) {
    const [dragActive, setDragActive] = useState(false);

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setDragActive(false);
        const file = e.dataTransfer.files[0];
        if (file) onUpload(file);
    };

    return (
        <div className="bg-slate-800/40 backdrop-blur-sm border border-slate-700/40 rounded-2xl p-8">
            <div
                className={`border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer
                    ${dragActive ? "border-blue-400 bg-blue-500/10" : "border-slate-600 hover:border-slate-500 hover:bg-slate-700/20"}`}
                onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
                onDragLeave={() => setDragActive(false)}
                onDrop={handleDrop}
                onClick={() => {
                    const input = document.createElement("input");
                    input.type = "file";
                    input.accept = ".pdf,.docx,.doc,.txt";
                    input.onchange = (e) => {
                        const file = (e.target as HTMLInputElement).files?.[0];
                        if (file) onUpload(file);
                    };
                    input.click();
                }}
            >
                {loading ? (
                    <div className="flex flex-col items-center gap-3">
                        <div className="w-10 h-10 border-3 border-blue-400 border-t-transparent rounded-full animate-spin" />
                        <p className="text-slate-300">Parsing your resume...</p>
                    </div>
                ) : (
                    <>
                        <div className="text-4xl mb-4">📄</div>
                        <p className="text-lg text-slate-200 font-medium">Drop your resume here</p>
                        <p className="text-slate-400 text-sm mt-2">PDF, DOCX, or TXT — we'll extract and structure everything</p>
                    </>
                )}
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════
   STEP 2 — Review & Edit Component
   ═══════════════════════════════════════ */
function ReviewStep({ schema, score, loading, onChange, onOptimize, onBack }: {
    schema: ResumeSchema; score: number; loading: boolean;
    onChange: (s: ResumeSchema) => void; onOptimize: () => void; onBack: () => void;
}) {
    const updateBasics = (field: keyof Basics, value: string) => {
        onChange({ ...schema, basics: { ...schema.basics, [field]: value } });
    };

    const updateSkills = (cat: keyof Skills, value: string) => {
        const items = value.split(",").map(s => s.trim()).filter(Boolean);
        onChange({ ...schema, skills: { ...schema.skills, [cat]: items } });
    };

    return (
        <div className="space-y-6">
            {/* Score badge */}
            <div className="flex items-center justify-between">
                <button onClick={onBack} className="text-sm text-slate-400 hover:text-slate-200 transition">
                    ← Back
                </button>
                <div className="bg-slate-800/60 border border-slate-700/40 rounded-xl px-4 py-2 text-sm">
                    <span className="text-slate-400">ATS Score: </span>
                    <span className={`font-bold ${score >= 70 ? "text-green-400" : score >= 40 ? "text-yellow-400" : "text-red-400"}`}>
                        {score}/100
                    </span>
                </div>
            </div>

            {/* Basics */}
            <Card title="👤 Basic Information">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {(["full_name", "email", "phone", "location", "linkedin", "github"] as (keyof Basics)[]).map(f => (
                        <div key={f}>
                            <label className="text-xs text-slate-400 mb-1 block capitalize">{f.replace("_", " ")}</label>
                            <input
                                className="w-full bg-slate-900/50 border border-slate-700/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:border-blue-500 focus:outline-none transition"
                                value={schema.basics[f]}
                                onChange={e => updateBasics(f, e.target.value)}
                                placeholder={f.replace("_", " ")}
                            />
                        </div>
                    ))}
                </div>
            </Card>

            {/* Summary */}
            <Card title="📝 Professional Summary">
                <textarea
                    className="w-full bg-slate-900/50 border border-slate-700/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:border-blue-500 focus:outline-none transition min-h-[80px] resize-y"
                    value={schema.summary}
                    onChange={e => onChange({ ...schema, summary: e.target.value })}
                    placeholder="Brief professional summary..."
                />
            </Card>

            {/* Skills */}
            <Card title="🛠 Technical Skills">
                <p className="text-xs text-slate-500 mb-3">Comma-separated. Edit or add skills in each category.</p>
                <div className="space-y-3">
                    {(Object.keys(SKILL_LABELS) as (keyof Skills)[]).map(cat => (
                        <div key={cat}>
                            <label className="text-xs text-slate-400 mb-1 block">{SKILL_LABELS[cat]}</label>
                            <input
                                className="w-full bg-slate-900/50 border border-slate-700/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:border-blue-500 focus:outline-none transition"
                                value={schema.skills[cat].join(", ")}
                                onChange={e => updateSkills(cat, e.target.value)}
                                placeholder={`e.g. ${SKILL_LABELS[cat]} skills...`}
                            />
                        </div>
                    ))}
                </div>
            </Card>

            {/* Experience */}
            <Card title="💼 Work Experience"
                onAdd={() => onChange({
                    ...schema,
                    experience: [...schema.experience, { company: "", role: "", start_date: "", end_date: "Present", bullets: [""] }]
                })}
            >
                {schema.experience.length === 0 && (
                    <p className="text-slate-500 text-sm text-center py-4">No experience entries yet. Click + to add.</p>
                )}
                {schema.experience.map((exp, i) => (
                    <ExperienceEditor
                        key={i}
                        exp={exp}
                        onChange={(updated) => {
                            const arr = [...schema.experience];
                            arr[i] = updated;
                            onChange({ ...schema, experience: arr });
                        }}
                        onDelete={() => {
                            onChange({ ...schema, experience: schema.experience.filter((_, j) => j !== i) });
                        }}
                    />
                ))}
            </Card>

            {/* Projects */}
            <Card title="🚀 Projects"
                onAdd={() => onChange({
                    ...schema,
                    projects: [...schema.projects, { name: "", type: "", year: "", bullets: [""] }]
                })}
            >
                {schema.projects.length === 0 && (
                    <p className="text-slate-500 text-sm text-center py-4">No projects yet. Click + to add.</p>
                )}
                {schema.projects.map((proj, i) => (
                    <ProjectEditor
                        key={i}
                        proj={proj}
                        onChange={(updated) => {
                            const arr = [...schema.projects];
                            arr[i] = updated;
                            onChange({ ...schema, projects: arr });
                        }}
                        onDelete={() => {
                            onChange({ ...schema, projects: schema.projects.filter((_, j) => j !== i) });
                        }}
                    />
                ))}
            </Card>

            {/* Education */}
            <Card title="🎓 Education"
                onAdd={() => onChange({
                    ...schema,
                    education: [...schema.education, { degree: "", institution: "", cgpa: "", start_year: "", end_year: "" }]
                })}
            >
                {schema.education.map((edu, i) => (
                    <EducationEditor
                        key={i}
                        edu={edu}
                        onChange={(updated) => {
                            const arr = [...schema.education];
                            arr[i] = updated;
                            onChange({ ...schema, education: arr });
                        }}
                        onDelete={() => {
                            onChange({ ...schema, education: schema.education.filter((_, j) => j !== i) });
                        }}
                    />
                ))}
            </Card>

            {/* Certifications */}
            <Card title="📜 Certifications">
                <ListEditor
                    items={schema.certifications}
                    onChange={items => onChange({ ...schema, certifications: items })}
                    placeholder="e.g. AWS Certified Solutions Architect"
                />
            </Card>

            {/* Achievements */}
            <Card title="🏆 Achievements">
                <ListEditor
                    items={schema.achievements}
                    onChange={items => onChange({ ...schema, achievements: items })}
                    placeholder="e.g. Won XYZ Hackathon 2024"
                />
            </Card>

            {/* Optimize button */}
            <div className="flex justify-center pt-2 pb-6">
                <button
                    onClick={onOptimize}
                    disabled={loading}
                    className="px-8 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold rounded-xl
                        hover:from-blue-600 hover:to-purple-600 transition-all shadow-lg shadow-blue-500/20
                        disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                    {loading ? (
                        <>
                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            AI is optimizing...
                        </>
                    ) : (
                        <>✨ Optimize with AI</>
                    )}
                </button>
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════
   STEP 3 — Generate & Download Component
   ═══════════════════════════════════════ */
function GenerateStep({ schema, score, loading, pdfUrl, pdfFilename, onChange, onGenerate, onRestart, onBack }: {
    schema: ResumeSchema; score: number; loading: boolean;
    pdfUrl: string; pdfFilename: string;
    onChange: (s: ResumeSchema) => void; onGenerate: () => void;
    onRestart: () => void; onBack: () => void;
}) {
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <button onClick={onBack} className="text-sm text-slate-400 hover:text-slate-200 transition">← Back to edit</button>
                <div className="bg-slate-800/60 border border-slate-700/40 rounded-xl px-4 py-2 text-sm">
                    <span className="text-slate-400">Optimized Score: </span>
                    <span className="font-bold text-green-400">{score}/100</span>
                </div>
            </div>

            {/* Preview — read-only summary */}
            <Card title="📋 Resume Preview">
                <div className="space-y-4 text-sm">
                    <div>
                        <span className="text-slate-400">Name: </span>
                        <span className="text-slate-200 font-medium">{schema.basics.full_name}</span>
                    </div>
                    <div>
                        <span className="text-slate-400">Summary: </span>
                        <span className="text-slate-300">{schema.summary || "—"}</span>
                    </div>
                    <div>
                        <span className="text-slate-400">Skills: </span>
                        <span className="text-slate-300">
                            {Object.values(schema.skills).flat().filter(Boolean).length} skills across {
                                Object.values(schema.skills).filter(arr => arr.length > 0).length
                            } categories
                        </span>
                    </div>
                    <div>
                        <span className="text-slate-400">Experience: </span>
                        <span className="text-slate-300">{schema.experience.length} entries</span>
                    </div>
                    <div>
                        <span className="text-slate-400">Projects: </span>
                        <span className="text-slate-300">{schema.projects.length} projects</span>
                    </div>
                    <div>
                        <span className="text-slate-400">Education: </span>
                        <span className="text-slate-300">{schema.education.length} entries</span>
                    </div>
                </div>
            </Card>

            {/* Actions */}
            <div className="flex flex-col items-center gap-4">
                {!pdfUrl ? (
                    <button
                        onClick={onGenerate}
                        disabled={loading}
                        className="px-8 py-3 bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-semibold rounded-xl
                            hover:from-emerald-600 hover:to-teal-600 transition-all shadow-lg shadow-emerald-500/20
                            disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        {loading ? (
                            <>
                                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                Generating PDF...
                            </>
                        ) : (
                            <>📄 Generate PDF</>
                        )}
                    </button>
                ) : (
                    <div className="text-center space-y-4">
                        <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 px-6 py-4 rounded-xl">
                            <p className="text-lg font-semibold mb-1">✅ Resume Ready!</p>
                            <p className="text-sm text-emerald-400/80">{pdfFilename}</p>
                        </div>
                        <div className="flex gap-3 justify-center">
                            <a
                                href={pdfUrl}
                                download={pdfFilename}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold rounded-xl
                                    hover:from-blue-600 hover:to-purple-600 transition-all shadow-lg shadow-blue-500/20"
                            >
                                ⬇️ Download PDF
                            </a>
                            <button
                                onClick={onRestart}
                                className="px-6 py-3 bg-slate-700/50 text-slate-300 font-medium rounded-xl
                                    hover:bg-slate-700 transition border border-slate-600/40"
                            >
                                🔄 New Resume
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════
   REUSABLE COMPONENTS
   ═══════════════════════════════════════ */

function Card({ title, children, onAdd }: { title: string; children: React.ReactNode; onAdd?: () => void }) {
    return (
        <div className="bg-slate-800/40 backdrop-blur-sm border border-slate-700/40 rounded-2xl p-5">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-semibold text-slate-200">{title}</h3>
                {onAdd && (
                    <button
                        onClick={onAdd}
                        className="w-7 h-7 rounded-lg bg-blue-500/20 border border-blue-500/30 text-blue-400 flex items-center justify-center
                            hover:bg-blue-500/30 transition text-sm font-bold"
                    >+</button>
                )}
            </div>
            {children}
        </div>
    );
}

function ExperienceEditor({ exp, onChange, onDelete }: {
    exp: Experience; onChange: (e: Experience) => void; onDelete: () => void;
}) {
    return (
        <div className="border border-slate-700/30 rounded-xl p-4 mb-3 bg-slate-900/20">
            <div className="flex justify-between items-start mb-3">
                <span className="text-xs text-slate-500">Experience Entry</span>
                <button onClick={onDelete} className="text-red-400/60 hover:text-red-400 text-xs transition">✕ Remove</button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                <input className="inp" value={exp.role} onChange={e => onChange({ ...exp, role: e.target.value })} placeholder="Role / Title" />
                <input className="inp" value={exp.company} onChange={e => onChange({ ...exp, company: e.target.value })} placeholder="Company" />
                <input className="inp" value={exp.start_date} onChange={e => onChange({ ...exp, start_date: e.target.value })} placeholder="Start Date (e.g. Jun 2024)" />
                <input className="inp" value={exp.end_date} onChange={e => onChange({ ...exp, end_date: e.target.value })} placeholder="End Date (e.g. Present)" />
            </div>
            <BulletsEditor
                bullets={exp.bullets}
                onChange={bullets => onChange({ ...exp, bullets })}
                placeholder="Achievement / responsibility bullet..."
            />
        </div>
    );
}

function ProjectEditor({ proj, onChange, onDelete }: {
    proj: Project; onChange: (p: Project) => void; onDelete: () => void;
}) {
    return (
        <div className="border border-slate-700/30 rounded-xl p-4 mb-3 bg-slate-900/20">
            <div className="flex justify-between items-start mb-3">
                <span className="text-xs text-slate-500">Project</span>
                <button onClick={onDelete} className="text-red-400/60 hover:text-red-400 text-xs transition">✕ Remove</button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                <input className="inp md:col-span-1" value={proj.name} onChange={e => onChange({ ...proj, name: e.target.value })} placeholder="Project Name" />
                <input className="inp" value={proj.type} onChange={e => onChange({ ...proj, type: e.target.value })} placeholder="Tech (e.g. Python, AWS)" />
                <input className="inp" value={proj.year} onChange={e => onChange({ ...proj, year: e.target.value })} placeholder="Year" />
            </div>
            <BulletsEditor
                bullets={proj.bullets}
                onChange={bullets => onChange({ ...proj, bullets })}
                placeholder="Project description bullet..."
            />
        </div>
    );
}

function EducationEditor({ edu, onChange, onDelete }: {
    edu: Education; onChange: (e: Education) => void; onDelete: () => void;
}) {
    return (
        <div className="border border-slate-700/30 rounded-xl p-4 mb-3 bg-slate-900/20">
            <div className="flex justify-between items-start mb-3">
                <span className="text-xs text-slate-500">Education</span>
                <button onClick={onDelete} className="text-red-400/60 hover:text-red-400 text-xs transition">✕ Remove</button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <input className="inp md:col-span-2" value={edu.degree} onChange={e => onChange({ ...edu, degree: e.target.value })} placeholder="Degree (e.g. B.Tech in CSE)" />
                <input className="inp" value={edu.institution} onChange={e => onChange({ ...edu, institution: e.target.value })} placeholder="Institution" />
                <input className="inp" value={edu.cgpa} onChange={e => onChange({ ...edu, cgpa: e.target.value })} placeholder="CGPA" />
                <input className="inp" value={edu.start_year} onChange={e => onChange({ ...edu, start_year: e.target.value })} placeholder="Start Year" />
                <input className="inp" value={edu.end_year} onChange={e => onChange({ ...edu, end_year: e.target.value })} placeholder="End Year" />
            </div>
        </div>
    );
}

function BulletsEditor({ bullets, onChange, placeholder }: {
    bullets: string[]; onChange: (b: string[]) => void; placeholder: string;
}) {
    return (
        <div className="space-y-2">
            {bullets.map((b, i) => (
                <div key={i} className="flex gap-2">
                    <span className="text-slate-600 mt-2 text-sm">•</span>
                    <input
                        className="inp flex-1"
                        value={b}
                        onChange={e => {
                            const arr = [...bullets];
                            arr[i] = e.target.value;
                            onChange(arr);
                        }}
                        placeholder={placeholder}
                    />
                    <button
                        onClick={() => onChange(bullets.filter((_, j) => j !== i))}
                        className="text-red-400/40 hover:text-red-400 text-xs mt-2 transition"
                    >✕</button>
                </div>
            ))}
            <button
                onClick={() => onChange([...bullets, ""])}
                className="text-xs text-blue-400/60 hover:text-blue-400 transition"
            >+ Add bullet</button>
        </div>
    );
}

function ListEditor({ items, onChange, placeholder }: {
    items: string[]; onChange: (i: string[]) => void; placeholder: string;
}) {
    return (
        <div className="space-y-2">
            {items.map((item, i) => (
                <div key={i} className="flex gap-2">
                    <input
                        className="inp flex-1"
                        value={item}
                        onChange={e => {
                            const arr = [...items];
                            arr[i] = e.target.value;
                            onChange(arr);
                        }}
                        placeholder={placeholder}
                    />
                    <button
                        onClick={() => onChange(items.filter((_, j) => j !== i))}
                        className="text-red-400/40 hover:text-red-400 text-xs transition"
                    >✕</button>
                </div>
            ))}
            <button
                onClick={() => onChange([...items, ""])}
                className="text-xs text-blue-400/60 hover:text-blue-400 transition"
            >+ Add item</button>
        </div>
    );
}
