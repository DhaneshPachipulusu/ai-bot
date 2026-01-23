"use client";

import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

const CAREERS_DATA: any = {
  "data-analyst": {
    title: "Data Analyst",
    icon: "📊",
    color: "blue",
    description: "Data Analysts transform raw data into actionable insights that drive business decisions. They work with databases, create visualizations, and help organizations understand patterns in their data.",
    salary: "$65,000 - $95,000",
    demand: "High",
    skillsCount: 5,
    techStack: [
      "Python (Pandas, NumPy, Matplotlib)",
      "SQL (MySQL, PostgreSQL)",
      "Excel & Google Sheets",
      "Tableau / Power BI",
      "Statistics & Probability"
    ],
    responsibilities: [
      "Extract and analyze data from databases",
      "Create dashboards and visualizations",
      "Identify trends and patterns in datasets",
      "Present findings to stakeholders",
      "Collaborate with business teams to define KPIs"
    ],
    resources: [
      { name: "GeeksforGeeks - SQL Tutorial", url: "https://www.geeksforgeeks.org/sql-tutorial/" },
      { name: "W3Schools - Python", url: "https://www.w3schools.com/python/" },
      { name: "Kaggle - Data Analysis Courses", url: "https://www.kaggle.com/learn" },
      { name: "Tableau Public - Free Training", url: "https://public.tableau.com/en-us/s/resources" }
    ],
    sampleQuestions: [
      "What is the difference between WHERE and HAVING clauses in SQL?",
      "Explain how you would handle missing data in a dataset",
      "What are the key steps in the data analysis workflow?",
      "How do you create a pivot table and when would you use it?",
      "Explain the difference between correlation and causation"
    ],
    careerPath: [
      "Junior Data Analyst (0-2 years)",
      "Data Analyst (2-4 years)",
      "Senior Data Analyst (4-6 years)",
      "Lead Data Analyst / Data Scientist (6+ years)"
    ]
  },
  "python-fullstack": {
    title: "Python Full Stack Developer",
    icon: "🐍",
    color: "green",
    description: "Python Full Stack Developers build complete web applications using Python frameworks for backend and modern JavaScript frameworks for frontend. They handle everything from databases to user interfaces.",
    salary: "$75,000 - $120,000",
    demand: "Very High",
    skillsCount: 6,
    techStack: [
      "Python (Django / Flask)",
      "React.js / Vue.js",
      "PostgreSQL / MongoDB",
      "REST APIs",
      "HTML, CSS, JavaScript",
      "Docker & Git"
    ],
    responsibilities: [
      "Design and develop web applications",
      "Build RESTful APIs and microservices",
      "Implement database schemas",
      "Create responsive user interfaces",
      "Deploy and maintain applications"
    ],
    resources: [
      { name: "Django Documentation", url: "https://docs.djangoproject.com/" },
      { name: "Flask Mega-Tutorial", url: "https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world" },
      { name: "React Official Docs", url: "https://react.dev/" },
      { name: "GeeksforGeeks - REST API", url: "https://www.geeksforgeeks.org/rest-api-introduction/" }
    ],
    sampleQuestions: [
      "Explain the difference between Django and Flask",
      "How do you implement authentication in a REST API?",
      "What is the Virtual DOM in React?",
      "How do you handle database migrations in Django?",
      "Explain the concept of middleware in web frameworks"
    ],
    careerPath: [
      "Junior Full Stack Developer (0-2 years)",
      "Full Stack Developer (2-4 years)",
      "Senior Full Stack Developer (4-6 years)",
      "Tech Lead / Solutions Architect (6+ years)"
    ]
  },
  "java-fullstack": {
    title: "Java Full Stack Developer",
    icon: "☕",
    color: "orange",
    description: "Java Full Stack Developers build enterprise-grade applications using Spring Boot for backend and Angular/React for frontend. They work on scalable, maintainable systems for large organizations.",
    salary: "$80,000 - $130,000",
    demand: "Very High",
    skillsCount: 6,
    techStack: [
      "Java (Spring Boot)",
      "Angular / React",
      "MySQL / Oracle",
      "Microservices",
      "REST & SOAP APIs",
      "Maven / Gradle"
    ],
    responsibilities: [
      "Develop enterprise applications",
      "Design microservices architecture",
      "Implement security and authentication",
      "Optimize database performance",
      "Write unit and integration tests"
    ],
    resources: [
      { name: "Spring Boot Guide", url: "https://spring.io/guides" },
      { name: "Baeldung - Java Tutorials", url: "https://www.baeldung.com/" },
      { name: "Angular Documentation", url: "https://angular.io/docs" },
      { name: "GeeksforGeeks - Java", url: "https://www.geeksforgeeks.org/java/" }
    ],
    sampleQuestions: [
      "What are the benefits of Spring Boot over traditional Spring?",
      "Explain dependency injection in Spring",
      "How do you handle exceptions in a REST API?",
      "What is the difference between @Component and @Service?",
      "Explain the concept of JPA and Hibernate"
    ],
    careerPath: [
      "Junior Java Developer (0-2 years)",
      "Java Full Stack Developer (2-4 years)",
      "Senior Java Developer (4-6 years)",
      "Technical Architect (6+ years)"
    ]
  },
  "devops": {
    title: "DevOps Engineer",
    icon: "⚙️",
    color: "purple",
    description: "DevOps Engineers bridge the gap between development and operations, automating deployments, managing infrastructure, and ensuring system reliability. They work with cloud platforms, containers, and CI/CD pipelines.",
    salary: "$85,000 - $140,000",
    demand: "Extremely High",
    skillsCount: 6,
    techStack: [
      "Docker & Kubernetes",
      "AWS / Azure / GCP",
      "CI/CD (Jenkins, GitLab CI)",
      "Terraform / Ansible",
      "Linux & Shell Scripting",
      "Monitoring (Prometheus, Grafana)"
    ],
    responsibilities: [
      "Automate deployment pipelines",
      "Manage cloud infrastructure",
      "Monitor system performance",
      "Implement security best practices",
      "Troubleshoot production issues"
    ],
    resources: [
      { name: "Docker Documentation", url: "https://docs.docker.com/" },
      { name: "Kubernetes Docs", url: "https://kubernetes.io/docs/home/" },
      { name: "AWS Free Tier", url: "https://aws.amazon.com/free/" },
      { name: "DevOps Roadmap", url: "https://roadmap.sh/devops" }
    ],
    sampleQuestions: [
      "What is the difference between Docker and Kubernetes?",
      "Explain CI/CD pipeline",
      "How do you handle secret management in production?",
      "What is Infrastructure as Code (IaC)?",
      "How do you troubleshoot a production outage?"
    ],
    careerPath: [
      "Junior DevOps Engineer (0-2 years)",
      "DevOps Engineer (2-4 years)",
      "Senior DevOps Engineer (4-6 years)",
      "DevOps Architect / SRE Lead (6+ years)"
    ]
  }
};

export default function CareerDetailPage() {
  const params = useParams();
  const router = useRouter();
  const careerId = params.id as string;
  const career = CAREERS_DATA[careerId];

  if (!career) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Career Not Found</h1>
        <Link href="/careers" className="text-blue-600 hover:underline">
          ← Back to Careers
        </Link>
      </div>
    );
  }

  const colorClasses: any = {
    blue: {
      gradient: "from-blue-600 to-blue-700",
      bg: "bg-blue-50",
      text: "text-blue-700",
      badge: "bg-blue-100 text-blue-700"
    },
    green: {
      gradient: "from-green-600 to-green-700",
      bg: "bg-green-50",
      text: "text-green-700",
      badge: "bg-green-100 text-green-700"
    },
    orange: {
      gradient: "from-orange-600 to-orange-700",
      bg: "bg-orange-50",
      text: "text-orange-700",
      badge: "bg-orange-100 text-orange-700"
    },
    purple: {
      gradient: "from-purple-600 to-purple-700",
      bg: "bg-purple-50",
      text: "text-purple-700",
      badge: "bg-purple-100 text-purple-700"
    }
  };

  const colors = colorClasses[career.color];

  return (
    <div className="max-w-6xl mx-auto">
      
      {/* Back Button */}
      <button
        onClick={() => router.back()}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6 transition-colors"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to Careers
      </button>

      {/* Hero Section */}
      <div className={`bg-gradient-to-r ${colors.gradient} rounded-3xl p-12 text-white mb-8 shadow-2xl`}>
        <div className="flex items-center gap-6 mb-6">
          <div className="w-24 h-24 bg-white/20 backdrop-blur-sm rounded-3xl flex items-center justify-center text-5xl shadow-xl">
            {career.icon}
          </div>
          <div>
            <h1 className="text-5xl font-bold mb-2">{career.title}</h1>
            <div className="flex gap-3">
              <span className="px-4 py-1.5 bg-white/20 backdrop-blur-sm rounded-full text-sm font-medium">
                💰 {career.salary}
              </span>
              <span className="px-4 py-1.5 bg-white/20 backdrop-blur-sm rounded-full text-sm font-medium">
                🔥 Demand: {career.demand}
              </span>
            </div>
          </div>
        </div>
        <p className="text-lg text-white/90 leading-relaxed max-w-4xl">
          {career.description}
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-8">
        
        {/* LEFT COLUMN */}
        <div className="md:col-span-2 space-y-8">
          
          {/* Tech Stack */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
              <span className="text-3xl">🛠️</span>
              Tech Stack
            </h2>
            <div className="grid sm:grid-cols-2 gap-3">
              {career.techStack.map((tech: string, idx: number) => (
                <div key={idx} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <svg className="w-5 h-5 text-green-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span className="text-gray-800 font-medium">{tech}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Responsibilities */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
              <span className="text-3xl">💼</span>
              Key Responsibilities
            </h2>
            <ul className="space-y-3">
              {career.responsibilities.map((resp: string, idx: number) => (
                <li key={idx} className="flex items-start gap-3">
                  <span className="text-blue-600 font-bold text-xl">•</span>
                  <span className="text-gray-700">{resp}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Interview Questions */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
              <span className="text-3xl">❓</span>
              Sample Interview Questions
            </h2>
            <ol className="space-y-4">
              {career.sampleQuestions.map((q: string, idx: number) => (
                <li key={idx} className="flex gap-3">
                  <span className="font-bold text-gray-400">{idx + 1}.</span>
                  <span className="text-gray-700">{q}</span>
                </li>
              ))}
            </ol>
          </div>

        </div>

        {/* RIGHT COLUMN */}
        <div className="space-y-6">
          
          {/* Career Path */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span className="text-2xl">📈</span>
              Career Path
            </h3>
            <div className="space-y-3">
              {career.careerPath.map((step: string, idx: number) => (
                <div key={idx} className="flex items-start gap-3">
                  <div className={`w-8 h-8 rounded-full ${colors.bg} ${colors.text} flex items-center justify-center font-bold flex-shrink-0`}>
                    {idx + 1}
                  </div>
                  <p className="text-sm text-gray-700 pt-1">{step}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Learning Resources */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span className="text-2xl">📚</span>
              Learning Resources
            </h3>
            <div className="space-y-3">
              {career.resources.map((resource: any, idx: number) => (
                <a
                  key={idx}
                  href={resource.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 hover:underline group"
                >
                  <svg className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                  {resource.name}
                </a>
              ))}
            </div>
          </div>

          {/* Practice Button */}
          <Link
            href="/interview"
            className={`block w-full py-4 px-6 bg-gradient-to-r ${colors.gradient} text-white font-bold rounded-xl text-center shadow-lg hover:shadow-xl transform hover:scale-105 transition-all`}
          >
            Practice Interview
          </Link>

        </div>

      </div>

    </div>
  );
}