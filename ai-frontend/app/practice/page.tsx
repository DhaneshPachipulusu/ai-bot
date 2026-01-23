"use client";

export default function PracticePage() {
  const topics = [
    { name: "Behavioral Questions", icon: "💬", count: 50, color: "blue" },
    { name: "Technical Questions", icon: "💻", count: 100, color: "green" },
    { name: "System Design", icon: "🏗️", count: 30, color: "purple" },
    { name: "Data Structures", icon: "📊", count: 75, color: "orange" },
  ];

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Quick Practice</h1>
        <p className="text-gray-600">Practice specific topics without uploading a resume</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {topics.map((topic) => (
          <div
            key={topic.name}
            className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 hover:shadow-lg hover:-translate-y-1 transition-all cursor-pointer group"
          >
            <div className="flex items-center gap-4 mb-4">
              <div className="w-14 h-14 bg-gradient-to-br from-blue-100 to-blue-200 rounded-xl flex items-center justify-center text-3xl group-hover:scale-110 transition-transform">
                {topic.icon}
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900">{topic.name}</h3>
                <p className="text-sm text-gray-500">{topic.count} questions available</p>
              </div>
            </div>
            <button className="w-full py-3 bg-gray-100 text-gray-700 font-medium rounded-xl hover:bg-gray-200 transition-colors">
              Start Practice
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}