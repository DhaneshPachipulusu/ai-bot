"use client";

import { useState } from "react";

type TabType = "intro" | "aptitude" | "hr" | "technical" | "tips";

export default function PracticePage() {
  const [activeTab, setActiveTab] = useState<TabType>("intro");
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const tabs = [
    { id: "intro", name: "Self Intro", icon: "👤" },
    { id: "aptitude", name: "Aptitude", icon: "🧮" },
    { id: "hr", name: "HR Questions", icon: "💬" },
    { id: "technical", name: "Tech Basics", icon: "💻" },
    { id: "tips", name: "Quick Tips", icon: "💡" },
  ];

  return (
    <div className="w-full pb-10">
      {/* Header */}
      <div className="mb-10">
        <h1 className="text-3xl md:text-4xl font-semibold text-white mb-3 tracking-tight">
          Interview Prep Kit
        </h1>
        <p className="text-gray-400/80 max-w-lg text-base leading-relaxed">
          Everything you need to crack your interview
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-8 overflow-x-auto pb-2 p-1.5 bg-slate-800/30 backdrop-blur-sm rounded-2xl border border-slate-700/30">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as TabType)}
            className={`px-4 py-2.5 rounded-xl font-medium text-sm whitespace-nowrap transition-all duration-200 flex items-center gap-2 ${activeTab === tab.id
              ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/20"
              : "bg-transparent text-gray-500 hover:text-gray-300 hover:bg-slate-700/50"
              }`}
          >
            <span>{tab.icon}</span>
            {tab.name}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="space-y-6">
        {activeTab === "intro" && <SelfIntroSection copyToClipboard={copyToClipboard} copiedIndex={copiedIndex} />}
        {activeTab === "aptitude" && <AptitudeSection />}
        {activeTab === "hr" && <HRQuestionsSection copyToClipboard={copyToClipboard} copiedIndex={copiedIndex} />}
        {activeTab === "technical" && <TechnicalSection />}
        {activeTab === "tips" && <TipsSection />}
      </div>
    </div>
  );
}

// ==================== SELF INTRO ====================
function SelfIntroSection({ copyToClipboard, copiedIndex }: { copyToClipboard: (text: string, index: number) => void; copiedIndex: number | null }) {
  const intros = [
    {
      title: "Fresher - CS/IT Graduate",
      template: `Good [morning/afternoon], my name is [Your Name]. I recently graduated from [College Name] with a degree in [Your Degree] with [CGPA/Percentage].

During my academics, I developed a strong foundation in [2-3 key skills like programming, databases, web development].

I completed a project called [Project Name] where I used [Technologies]. This helped me understand [what you learned].

I'm a quick learner, work well in teams, and I'm excited to start my career where I can contribute and grow.

Thank you for this opportunity.`,
    },
    {
      title: "Fresher - With Internship",
      template: `Hello, I'm [Your Name], a [Degree] graduate from [College Name].

I completed a [Duration] internship at [Company Name] where I worked on [Brief description]. I used [Technologies] and learned [Key learning].

My final year project was [Project Name], built using [Tech stack], which [what it does].

I'm passionate about [Your interest area] and looking forward to applying my skills in a professional environment.

Thank you.`,
    },
    {
      title: "Fresher - Non-CS Background",
      template: `Good [morning/afternoon], I'm [Your Name]. I completed my [Degree] in [Branch] from [College].

While my core background is in [Your field], I developed a strong interest in technology and taught myself [Skills like Python, Web Development, etc.].

I built [Project/Portfolio] to apply my learning practically. I believe my [analytical/problem-solving] skills from my background combined with my technical skills make me a good fit.

I'm eager to learn and grow in the IT industry.

Thank you.`,
    },
  ];

  return (
    <div className="space-y-5">
      {/* Tips Card - Enhanced glassmorphism */}
      <div className="bg-slate-800/40 backdrop-blur-sm border border-blue-500/20 rounded-2xl p-5 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/8 blur-3xl rounded-full -mr-16 -mt-16 pointer-events-none"></div>
        <div className="flex items-center gap-2.5 mb-3 relative">
          <div className="w-8 h-8 bg-blue-500/15 rounded-lg flex items-center justify-center text-blue-400 text-sm">📌</div>
          <h3 className="text-white font-medium">Self Intro Tips</h3>
        </div>
        <ul className="text-sm text-gray-400 space-y-2 relative">
          <li className="flex items-start gap-2"><span className="text-blue-400/60 mt-0.5">•</span><span>Keep it under 2 minutes</span></li>
          <li className="flex items-start gap-2"><span className="text-blue-400/60 mt-0.5">•</span><span>Speak clearly and confidently</span></li>
          <li className="flex items-start gap-2"><span className="text-blue-400/60 mt-0.5">•</span><span>Mention: Name → Education → Skills → Project → Why this role</span></li>
          <li className="flex items-start gap-2"><span className="text-blue-400/60 mt-0.5">•</span><span>Practice in front of mirror or record yourself</span></li>
        </ul>
      </div>

      {intros.map((intro, index) => (
        <div key={index} className="bg-slate-800/40 backdrop-blur-sm rounded-2xl border border-slate-700/40 overflow-hidden transition-all duration-200 hover:border-slate-600/60">
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-700/40">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-blue-500"></div>
              <h3 className="font-medium text-white">{intro.title}</h3>
            </div>
            <button
              onClick={() => copyToClipboard(intro.template, index)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 flex items-center gap-1.5 ${copiedIndex === index
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                : "bg-slate-700/60 text-gray-300 hover:bg-slate-600 hover:text-white border border-slate-600/50"
                }`}
            >
              {copiedIndex === index ? (
                <><svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>Copied</>
              ) : (
                <><svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" /></svg>Copy</>
              )}
            </button>
          </div>
          <pre className="p-5 text-sm text-gray-400/90 whitespace-pre-wrap font-mono leading-relaxed bg-slate-900/30 border-l-2 border-blue-500/30">
            {intro.template}
          </pre>
        </div>
      ))}
    </div>
  );
}

// ==================== APTITUDE ====================
function AptitudeSection() {
  const categories = [
    {
      title: "Percentages",
      icon: "%",
      formulas: [
        { name: "Percentage", formula: "(Value / Total) × 100" },
        { name: "% Increase", formula: "[(New - Old) / Old] × 100" },
        { name: "% Decrease", formula: "[(Old - New) / Old] × 100" },
        { name: "X% of Y", formula: "(X × Y) / 100" },
      ],
    },
    {
      title: "Profit & Loss",
      icon: "💰",
      formulas: [
        { name: "Profit", formula: "SP - CP" },
        { name: "Loss", formula: "CP - SP" },
        { name: "Profit %", formula: "(Profit / CP) × 100" },
        { name: "Loss %", formula: "(Loss / CP) × 100" },
        { name: "SP (Profit)", formula: "CP × (100 + P%) / 100" },
        { name: "SP (Loss)", formula: "CP × (100 - L%) / 100" },
      ],
    },
    {
      title: "Simple Interest",
      icon: "🏦",
      formulas: [
        { name: "SI", formula: "(P × R × T) / 100" },
        { name: "Amount", formula: "P + SI" },
        { name: "Principal", formula: "(SI × 100) / (R × T)" },
        { name: "Rate", formula: "(SI × 100) / (P × T)" },
        { name: "Time", formula: "(SI × 100) / (P × R)" },
      ],
    },
    {
      title: "Compound Interest",
      icon: "📈",
      formulas: [
        { name: "Amount", formula: "P × (1 + R/100)ⁿ" },
        { name: "CI", formula: "Amount - Principal" },
        { name: "2 Years CI", formula: "P × R × (200 + R) / 10000" },
      ],
    },
    {
      title: "Time & Work",
      icon: "⏱️",
      formulas: [
        { name: "Work", formula: "Time × Efficiency" },
        { name: "A's 1 day work", formula: "1/A days" },
        { name: "A+B together", formula: "1/A + 1/B = 1/T" },
        { name: "Total time (A+B)", formula: "(A × B) / (A + B)" },
      ],
    },
    {
      title: "Speed, Time & Distance",
      icon: "🚗",
      formulas: [
        { name: "Speed", formula: "Distance / Time" },
        { name: "Distance", formula: "Speed × Time" },
        { name: "Time", formula: "Distance / Speed" },
        { name: "Avg Speed", formula: "2×S1×S2 / (S1+S2)" },
        { name: "km/h → m/s", formula: "× 5/18" },
        { name: "m/s → km/h", formula: "× 18/5" },
      ],
    },
    {
      title: "Averages",
      icon: "📊",
      formulas: [
        { name: "Average", formula: "Sum / Count" },
        { name: "Sum", formula: "Average × Count" },
        { name: "Weighted Avg", formula: "Σ(value × weight) / Σweight" },
      ],
    },
    {
      title: "Ratios & Proportions",
      icon: "⚖️",
      formulas: [
        { name: "Ratio a:b", formula: "a/b" },
        { name: "Proportion", formula: "a:b = c:d → a×d = b×c" },
        { name: "Part from ratio", formula: "(Part/Total parts) × Total" },
      ],
    },
  ];

  return (
    <div className="grid md:grid-cols-2 gap-5">
      {categories.map((cat, index) => (
        <div key={index} className="bg-slate-800/40 backdrop-blur-sm rounded-2xl border border-slate-700/40 p-5 transition-all duration-200 hover:border-slate-600/60 hover:bg-slate-800/50">
          <div className="flex items-center gap-2.5 mb-4 pb-3 border-b border-slate-700/40">
            <span className="text-xl">{cat.icon}</span>
            <h3 className="font-medium text-white">{cat.title}</h3>
          </div>
          <div className="space-y-2.5">
            {cat.formulas.map((f, i) => (
              <div key={i} className="flex justify-between items-center py-1.5">
                <span className="text-gray-400/90 text-sm">{f.name}</span>
                <code className="text-emerald-400 text-sm bg-slate-900/50 px-2.5 py-1 rounded-lg font-mono">{f.formula}</code>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ==================== HR QUESTIONS ====================
function HRQuestionsSection({ copyToClipboard, copiedIndex }: { copyToClipboard: (text: string, index: number) => void; copiedIndex: number | null }) {
  const questions = [
    {
      q: "Tell me about yourself",
      a: "Use the self-intro template. Focus on: Name → Education → Skills → Projects → Career goal. Keep it 1-2 minutes.",
    },
    {
      q: "Why should we hire you?",
      a: "I have the required technical skills [mention 2-3], I'm a quick learner, and I'm genuinely passionate about this field. I'm ready to contribute from day one and grow with the company.",
    },
    {
      q: "What are your strengths?",
      a: "I'm a quick learner and adapt easily to new technologies. I'm good at problem-solving and can work well both independently and in a team. [Give a brief example]",
    },
    {
      q: "What are your weaknesses?",
      a: "Sometimes I focus too much on details, which can slow me down. But I've been working on balancing perfectionism with efficiency by setting time limits for tasks.",
    },
    {
      q: "Where do you see yourself in 5 years?",
      a: "I see myself as a skilled professional in [your field], having taken on more responsibilities and possibly mentoring juniors. I want to grow technically while contributing to impactful projects.",
    },
    {
      q: "Why do you want to join our company?",
      a: "[Research the company first!] I'm impressed by [company's product/culture/growth]. I believe my skills in [relevant skills] align well with your work, and I'm excited about the learning opportunities here.",
    },
    {
      q: "What is your expected salary?",
      a: "I'm flexible and open to a fair offer based on the role and my skills. I'm more focused on learning and growth at this stage. However, I'd expect something in line with industry standards for freshers.",
    },
    {
      q: "Do you have any questions for us?",
      a: "Yes! 1) What does a typical day look like for this role? 2) What are the growth opportunities? 3) What's the team structure? [Always ask at least 1-2 questions]",
    },
    {
      q: "Tell me about a challenge you faced",
      a: "During my project [name], I faced [specific challenge]. I [action you took] by [how you solved it]. The result was [positive outcome]. This taught me [learning].",
    },
    {
      q: "Are you comfortable with relocation?",
      a: "Yes, I'm open to relocation. I understand it's part of professional growth, and I'm flexible about working from different locations.",
    },
  ];

  return (
    <div className="space-y-5">
      {/* HR Tips Card - Enhanced glassmorphism */}
      <div className="bg-slate-800/40 backdrop-blur-sm border border-amber-500/20 rounded-2xl p-5 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500/8 blur-3xl rounded-full -mr-16 -mt-16 pointer-events-none"></div>
        <div className="flex items-center gap-2.5 mb-3 relative">
          <div className="w-8 h-8 bg-amber-500/15 rounded-lg flex items-center justify-center text-amber-400 text-sm">💡</div>
          <h3 className="text-white font-medium">HR Round Tips</h3>
        </div>
        <ul className="text-sm text-gray-400 space-y-2 relative">
          <li className="flex items-start gap-2"><span className="text-amber-400/60 mt-0.5">•</span><span>Be honest - don’t make up stories</span></li>
          <li className="flex items-start gap-2"><span className="text-amber-400/60 mt-0.5">•</span><span>Use STAR method: Situation → Task → Action → Result</span></li>
          <li className="flex items-start gap-2"><span className="text-amber-400/60 mt-0.5">•</span><span>Research the company before interview</span></li>
          <li className="flex items-start gap-2"><span className="text-amber-400/60 mt-0.5">•</span><span>Stay positive, never badmouth previous experiences</span></li>
        </ul>
      </div>

      {questions.map((item, index) => (
        <div key={index} className="bg-slate-800/40 backdrop-blur-sm rounded-2xl border border-slate-700/40 p-5 transition-all duration-200 hover:border-slate-600/60 hover:bg-slate-800/50">
          <div className="flex justify-between items-start gap-4 mb-3">
            <h4 className="font-medium text-blue-400">Q: {item.q}</h4>
            <button
              onClick={() => copyToClipboard(item.a, index + 100)}
              className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 flex items-center gap-1.5 flex-shrink-0 ${copiedIndex === index + 100
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                : "bg-slate-700/60 text-gray-300 hover:bg-slate-600 hover:text-white border border-slate-600/50"
                }`}
            >
              {copiedIndex === index + 100 ? (
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
              ) : (
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" /></svg>
              )}
            </button>
          </div>
          <p className="text-gray-400/90 text-sm leading-relaxed">{item.a}</p>
        </div>
      ))}
    </div>
  );
}

// ==================== TECHNICAL BASICS ====================
function TechnicalSection() {
  const topics = [
    {
      title: "OOP Concepts",
      items: [
        { term: "Class", def: "Blueprint for creating objects" },
        { term: "Object", def: "Instance of a class" },
        { term: "Encapsulation", def: "Bundling data + methods, hiding internals" },
        { term: "Inheritance", def: "Child class inherits from parent class" },
        { term: "Polymorphism", def: "Same method, different behaviors" },
        { term: "Abstraction", def: "Hiding complexity, showing only essentials" },
      ],
    },
    {
      title: "DBMS Basics",
      items: [
        { term: "Primary Key", def: "Unique identifier for each row" },
        { term: "Foreign Key", def: "Links two tables together" },
        { term: "Normalization", def: "Organizing data to reduce redundancy" },
        { term: "JOIN", def: "Combines rows from 2+ tables" },
        { term: "INDEX", def: "Speeds up data retrieval" },
        { term: "ACID", def: "Atomicity, Consistency, Isolation, Durability" },
      ],
    },
    {
      title: "Data Structures",
      items: [
        { term: "Array", def: "Fixed size, same type, O(1) access" },
        { term: "Linked List", def: "Dynamic size, nodes with pointers" },
        { term: "Stack", def: "LIFO - Last In First Out" },
        { term: "Queue", def: "FIFO - First In First Out" },
        { term: "Tree", def: "Hierarchical structure with root node" },
        { term: "Hash Table", def: "Key-value pairs, O(1) average lookup" },
      ],
    },
    {
      title: "Web Basics",
      items: [
        { term: "HTML", def: "Structure of web pages" },
        { term: "CSS", def: "Styling and layout" },
        { term: "JavaScript", def: "Interactivity and logic" },
        { term: "API", def: "Interface for software communication" },
        { term: "REST", def: "Stateless, HTTP-based API design" },
        { term: "JSON", def: "Lightweight data format" },
      ],
    },
    {
      title: "Git Commands",
      items: [
        { term: "git init", def: "Initialize new repository" },
        { term: "git clone", def: "Copy remote repo locally" },
        { term: "git add .", def: "Stage all changes" },
        { term: "git commit -m", def: "Save changes with message" },
        { term: "git push", def: "Upload to remote" },
        { term: "git pull", def: "Download & merge changes" },
      ],
    },
    {
      title: "Complexity (Big O)",
      items: [
        { term: "O(1)", def: "Constant - best" },
        { term: "O(log n)", def: "Logarithmic - binary search" },
        { term: "O(n)", def: "Linear - single loop" },
        { term: "O(n log n)", def: "Merge sort, quick sort" },
        { term: "O(n²)", def: "Quadratic - nested loops" },
        { term: "O(2ⁿ)", def: "Exponential - very slow" },
      ],
    },
  ];

  return (
    <div className="grid md:grid-cols-2 gap-5">
      {topics.map((topic, index) => (
        <div key={index} className="bg-slate-800/40 backdrop-blur-sm rounded-2xl border border-slate-700/40 p-5 transition-all duration-200 hover:border-slate-600/60 hover:bg-slate-800/50">
          <h3 className="font-medium text-white mb-4 pb-3 border-b border-slate-700/40">{topic.title}</h3>
          <div className="space-y-2.5">
            {topic.items.map((item, i) => (
              <div key={i} className="flex gap-3">
                <code className="text-blue-400 text-sm font-medium font-mono min-w-[100px]">{item.term}</code>
                <span className="text-gray-400/90 text-sm">— {item.def}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ==================== TIPS ====================
function TipsSection() {
  const tipCategories = [
    {
      title: "Before Interview",
      icon: "📋",
      tips: [
        "Research the company - products, culture, recent news",
        "Review your resume - be ready to explain everything",
        "Prepare 2-3 questions to ask the interviewer",
        "Test your internet/camera/mic if virtual interview",
        "Keep your documents ready (resume, ID, certificates)",
        "Sleep well the night before",
      ],
    },
    {
      title: "During Interview",
      icon: "🎯",
      tips: [
        "Arrive 10-15 minutes early",
        "Maintain eye contact and good posture",
        "Listen carefully before answering",
        "It's okay to take a moment to think",
        "If you don't know, say 'I'm not sure, but I would...'",
        "Ask for clarification if question is unclear",
        "Be enthusiastic but genuine",
      ],
    },
    {
      title: "Technical Round",
      icon: "💻",
      tips: [
        "Think aloud - explain your approach",
        "Start with brute force, then optimize",
        "Ask about edge cases",
        "Write clean, readable code",
        "Test your solution with examples",
        "Don't panic if stuck - ask for hints",
      ],
    },
    {
      title: "Body Language",
      icon: "🤝",
      tips: [
        "Firm handshake (if in-person)",
        "Sit straight, don't slouch",
        "Smile naturally",
        "Nod to show you're listening",
        "Avoid crossing arms",
        "Don't fidget or touch your face",
      ],
    },
    {
      title: "Common Mistakes to Avoid",
      icon: "⚠️",
      tips: [
        "Don't badmouth previous company/college",
        "Don't lie or exaggerate",
        "Don't interrupt the interviewer",
        "Don't give one-word answers",
        "Don't say 'I have no weaknesses'",
        "Don't forget to follow up with thank you email",
      ],
    },
    {
      title: "Virtual Interview Tips",
      icon: "🖥️",
      tips: [
        "Use a plain, tidy background",
        "Good lighting on your face",
        "Look at camera, not screen",
        "Mute when not speaking",
        "Have backup internet plan",
        "Close unnecessary tabs/apps",
      ],
    },
  ];

  return (
    <div className="grid md:grid-cols-2 gap-5">
      {tipCategories.map((cat, index) => (
        <div key={index} className="bg-slate-800/40 backdrop-blur-sm rounded-2xl border border-slate-700/40 p-5 transition-all duration-200 hover:border-slate-600/60 hover:bg-slate-800/50">
          <div className="flex items-center gap-2.5 mb-4 pb-3 border-b border-slate-700/40">
            <span className="text-xl">{cat.icon}</span>
            <h3 className="font-medium text-white">{cat.title}</h3>
          </div>
          <ul className="space-y-2.5">
            {cat.tips.map((tip, i) => (
              <li key={i} className="flex items-start gap-2.5 text-sm text-gray-400/90">
                <span className="text-emerald-400/80 mt-0.5 flex-shrink-0">✓</span>
                <span>{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}