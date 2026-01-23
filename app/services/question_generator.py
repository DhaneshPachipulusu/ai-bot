import json
from app.config import USE_MOCK_AI, client

# ==========================================
# STANDARD INTERVIEW QUESTIONS
# ==========================================

INTRO_QUESTION = {
    "type": "introduction",
    "topic": "Self Introduction",
    "question": "Let's start with a brief introduction. Tell me about yourself, your background, and what interests you about this role."
}

BEHAVIORAL_QUESTIONS = [
    {
        "type": "behavioral",
        "topic": "Strengths",
        "question": "What would you say are your greatest strengths that make you suitable for this role?"
    },
    {
        "type": "behavioral",
        "topic": "Challenges",
        "question": "Tell me about a challenging project or situation you faced. How did you handle it?"
    },
    {
        "type": "behavioral",
        "topic": "Teamwork",
        "question": "Describe a time when you had to work closely with a team to achieve a goal. What was your role?"
    },
    {
        "type": "behavioral",
        "topic": "Learning",
        "question": "Tell me about a time when you had to learn something new quickly. How did you approach it?"
    },
]

CLOSING_QUESTION = {
    "type": "closing",
    "topic": "Questions & Closing",
    "question": "That concludes our technical questions. Do you have any questions about the role or company? Also, is there anything else you'd like to share that we haven't covered?"
}

THANK_YOU_MESSAGE = {
    "type": "thank_you",
    "topic": "Interview Complete",
    "question": "Thank you for your time today! You've done a great job answering the questions. We appreciate your interest and effort. You'll receive your detailed feedback report shortly. Best of luck!"
}


# ==========================================
# ROLE-BASED QUESTIONS (Mock Data)
# ==========================================

ROLE_QUESTIONS = {
    "Data Analyst": {
        "Entry Level": [
            {"type": "technical", "topic": "SQL", "question": "Write a SQL query to find the top 5 customers by total purchase amount from a sales table."},
            {"type": "technical", "topic": "Excel", "question": "What Excel functions do you use most frequently for data analysis? Explain VLOOKUP vs INDEX-MATCH."},
            {"type": "technical", "topic": "Statistics", "question": "Explain the difference between mean, median, and mode. When would you use each?"},
            {"type": "scenario", "topic": "Data Cleaning", "question": "You receive a dataset with missing values and duplicates. Walk me through your data cleaning process."},
            {"type": "technical", "topic": "Visualization", "question": "What makes an effective data visualization? Which chart types would you use for comparing categories vs showing trends?"},
        ],
        "Mid Level": [
            {"type": "technical", "topic": "SQL", "question": "Explain window functions in SQL. Write a query using ROW_NUMBER, RANK, or LAG."},
            {"type": "technical", "topic": "Python/R", "question": "How would you use pandas to merge multiple datasets and handle missing data?"},
            {"type": "scenario", "topic": "Analysis", "question": "Sales dropped 15% last quarter. Walk me through how you would investigate the cause."},
            {"type": "technical", "topic": "Statistics", "question": "Explain A/B testing. What statistical tests would you use to determine significance?"},
            {"type": "scenario", "topic": "Stakeholders", "question": "A non-technical stakeholder asks for a report. How do you present complex findings simply?"},
        ],
        "Senior": [
            {"type": "technical", "topic": "Architecture", "question": "Design a data pipeline for real-time sales analytics. What tools and architecture would you use?"},
            {"type": "scenario", "topic": "Strategy", "question": "How would you build a data-driven culture in an organization that relies heavily on intuition?"},
            {"type": "technical", "topic": "ML", "question": "When would you use regression vs classification? Explain a use case for each in business analytics."},
            {"type": "scenario", "topic": "Leadership", "question": "How do you mentor junior analysts and ensure quality in their deliverables?"},
            {"type": "technical", "topic": "Tools", "question": "Compare Tableau, Power BI, and Looker. In what scenarios would you choose each?"},
        ],
    },
    "Frontend Developer": {
        "Junior": [
            {"type": "technical", "topic": "HTML/CSS", "question": "Explain the CSS box model. How do margin, padding, and border work together?"},
            {"type": "technical", "topic": "JavaScript", "question": "What is the difference between let, const, and var in JavaScript?"},
            {"type": "technical", "topic": "React", "question": "Explain the difference between state and props in React. When would you use each?"},
            {"type": "scenario", "topic": "Responsive Design", "question": "How would you make a website responsive for mobile, tablet, and desktop?"},
            {"type": "technical", "topic": "DOM", "question": "What is the Virtual DOM and why does React use it?"},
        ],
        "Mid Level": [
            {"type": "technical", "topic": "React", "question": "Explain React hooks. When would you use useEffect vs useLayoutEffect?"},
            {"type": "technical", "topic": "State Management", "question": "Compare Redux, Context API, and Zustand. When would you choose each?"},
            {"type": "scenario", "topic": "Performance", "question": "A page is loading slowly. How would you diagnose and optimize it?"},
            {"type": "technical", "topic": "TypeScript", "question": "What are the benefits of TypeScript? Explain generics with an example."},
            {"type": "scenario", "topic": "API", "question": "How do you handle API errors gracefully in a React application?"},
        ],
        "Senior": [
            {"type": "technical", "topic": "Architecture", "question": "Design the frontend architecture for a large-scale e-commerce application."},
            {"type": "scenario", "topic": "Performance", "question": "Explain code splitting, lazy loading, and how you would implement them."},
            {"type": "technical", "topic": "Testing", "question": "What's your testing strategy? Compare unit, integration, and e2e testing."},
            {"type": "scenario", "topic": "Leadership", "question": "How do you establish coding standards and review practices in a frontend team?"},
            {"type": "technical", "topic": "SSR", "question": "Explain Server-Side Rendering vs Static Site Generation. When would you use Next.js?"},
        ],
    },
    "Backend Developer": {
        "Junior": [
            {"type": "technical", "topic": "APIs", "question": "What is REST? Explain the difference between GET, POST, PUT, and DELETE."},
            {"type": "technical", "topic": "Database", "question": "What is the difference between SQL and NoSQL databases? When would you use each?"},
            {"type": "technical", "topic": "Python", "question": "Explain how you would create a simple API endpoint using FastAPI or Flask."},
            {"type": "scenario", "topic": "Debugging", "question": "An API endpoint returns a 500 error. How would you debug it?"},
            {"type": "technical", "topic": "Security", "question": "What is SQL injection and how do you prevent it?"},
        ],
        "Mid Level": [
            {"type": "technical", "topic": "Architecture", "question": "Explain microservices vs monolithic architecture. When would you choose each?"},
            {"type": "technical", "topic": "Database", "question": "How do you optimize a slow database query? Explain indexing and query planning."},
            {"type": "scenario", "topic": "Scaling", "question": "Your API handles 1000 requests/second. How would you scale it to handle 100,000?"},
            {"type": "technical", "topic": "Caching", "question": "Explain caching strategies. When would you use Redis vs in-memory caching?"},
            {"type": "technical", "topic": "Authentication", "question": "Compare JWT, OAuth, and session-based authentication. Implement token refresh."},
        ],
        "Senior": [
            {"type": "technical", "topic": "System Design", "question": "Design a URL shortener like bit.ly. Consider scale, storage, and analytics."},
            {"type": "scenario", "topic": "Production", "question": "A production service goes down at 2 AM. Walk me through your incident response."},
            {"type": "technical", "topic": "Distributed Systems", "question": "Explain CAP theorem. How do you handle consistency in distributed systems?"},
            {"type": "scenario", "topic": "Migration", "question": "How would you migrate a legacy monolith to microservices without downtime?"},
            {"type": "technical", "topic": "DevOps", "question": "Design a CI/CD pipeline for a backend service. What tools and stages would you include?"},
        ],
    },
    "DevOps Engineer": {
        "Junior": [
            {"type": "technical", "topic": "Docker", "question": "What is Docker? Explain the difference between an image and a container."},
            {"type": "technical", "topic": "Linux", "question": "How would you check disk usage, running processes, and network connections in Linux?"},
            {"type": "technical", "topic": "Git", "question": "Explain git branching strategies. What is the difference between merge and rebase?"},
            {"type": "scenario", "topic": "CI/CD", "question": "Explain what happens in a typical CI/CD pipeline from code commit to deployment."},
            {"type": "technical", "topic": "Cloud", "question": "What is the difference between EC2, Lambda, and ECS in AWS?"},
        ],
        "Mid Level": [
            {"type": "technical", "topic": "Kubernetes", "question": "Explain Kubernetes architecture. What are pods, services, and deployments?"},
            {"type": "technical", "topic": "IaC", "question": "Compare Terraform and CloudFormation. How do you manage infrastructure state?"},
            {"type": "scenario", "topic": "Monitoring", "question": "Design a monitoring and alerting strategy for a microservices application."},
            {"type": "technical", "topic": "Networking", "question": "Explain VPC, subnets, security groups, and load balancers in AWS."},
            {"type": "scenario", "topic": "Troubleshooting", "question": "Pods are in CrashLoopBackOff state. How do you diagnose and fix it?"},
        ],
        "Senior": [
            {"type": "technical", "topic": "Architecture", "question": "Design a multi-region, highly available infrastructure for a global application."},
            {"type": "scenario", "topic": "Security", "question": "How do you implement security best practices in a Kubernetes cluster?"},
            {"type": "technical", "topic": "Cost", "question": "How would you optimize cloud costs while maintaining performance and reliability?"},
            {"type": "scenario", "topic": "Disaster Recovery", "question": "Design a disaster recovery plan with RTO of 15 minutes and RPO of 5 minutes."},
            {"type": "technical", "topic": "GitOps", "question": "Explain GitOps. How would you implement it using ArgoCD or Flux?"},
        ],
    },
}

# Default questions for roles not in the dictionary
DEFAULT_QUESTIONS = [
    {"type": "technical", "topic": "Core Skills", "question": "What technical skills do you consider most important for this role?"},
    {"type": "technical", "topic": "Tools", "question": "What tools and technologies have you worked with that are relevant to this position?"},
    {"type": "scenario", "topic": "Problem Solving", "question": "Describe a complex problem you solved in your previous work. What was your approach?"},
    {"type": "technical", "topic": "Best Practices", "question": "What best practices do you follow in your work? Why are they important?"},
    {"type": "scenario", "topic": "Project", "question": "Tell me about a project you're proud of. What was your contribution and the outcome?"},
]


# ==========================================
# QUESTION GENERATION FUNCTIONS
# ==========================================

def generate_role_questions(role: str, level: str) -> dict:
    """
    Generate interview questions based on role and level.
    Returns a complete interview flow including intro, technical, behavioral, and closing.
    """
    
    if USE_MOCK_AI:
        return _get_mock_questions(role, level)
    
    try:
        prompt = f"""
Generate interview questions for a {level} {role} position.

Return ONLY valid JSON with this structure:
{{
    "role": "{role}",
    "difficulty": "{level}",
    "questions": [
        {{"type": "introduction", "topic": "Self Introduction", "question": "Tell me about yourself..."}},
        {{"type": "technical", "topic": "...", "question": "..."}},
        {{"type": "technical", "topic": "...", "question": "..."}},
        {{"type": "technical", "topic": "...", "question": "..."}},
        {{"type": "scenario", "topic": "...", "question": "..."}},
        {{"type": "behavioral", "topic": "Strengths", "question": "What are your strengths..."}},
        {{"type": "behavioral", "topic": "Challenges", "question": "Tell me about a challenge..."}},
        {{"type": "closing", "topic": "Questions", "question": "Do you have any questions for us?"}}
    ]
}}

Include:
1. Self introduction (first question)
2. 4-5 technical questions specific to {role} at {level} level
3. 2 behavioral questions (strengths, challenges)
4. 1 closing question

Make questions appropriate for {level} difficulty.
"""

        response = client.models.generate_content(
            model="models/gemini-flash-lite-latest",
            contents=prompt
        )

        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        return json.loads(text.strip())

    except Exception as e:
        print(f"Question generation error: {e}")
        return _get_mock_questions(role, level)


def _get_mock_questions(role: str, level: str) -> dict:
    """
    Get mock questions for a role and level.
    Used when AI is disabled or fails.
    """
    
    # Get role-specific questions or default
    role_data = ROLE_QUESTIONS.get(role, {})
    technical_questions = role_data.get(level, DEFAULT_QUESTIONS)
    
    # Build complete interview flow
    questions = []
    
    # 1. Introduction
    questions.append(INTRO_QUESTION)
    
    # 2. Technical questions (take 4-5)
    questions.extend(technical_questions[:5])
    
    # 3. Behavioral questions (take 2)
    questions.extend(BEHAVIORAL_QUESTIONS[:2])
    
    # 4. Closing
    questions.append(CLOSING_QUESTION)
    
    return {
        "role": role,
        "difficulty": level,
        "questions": questions
    }


def add_interview_flow_to_questions(questions: list, role: str = "Unknown") -> list:
    """
    Add intro, behavioral, and closing questions to existing question list.
    Use this for resume-based interviews to add standard interview flow.
    """
    
    flow_questions = []
    
    # 1. Start with introduction
    flow_questions.append(INTRO_QUESTION)
    
    # 2. Add original questions (technical/project)
    flow_questions.extend(questions[:5])  # Limit to 5 main questions
    
    # 3. Add behavioral questions
    flow_questions.append(BEHAVIORAL_QUESTIONS[0])  # Strengths
    flow_questions.append(BEHAVIORAL_QUESTIONS[1])  # Challenges
    
    # 4. End with closing
    flow_questions.append(CLOSING_QUESTION)
    
    return flow_questions


# ==========================================
# EXISTING RESUME-BASED GENERATION
# ==========================================

def generate_questions(parsed_resume: dict) -> dict:
    """
    Generate questions based on parsed resume.
    Now includes intro, behavioral, and closing questions.
    """
    
    if USE_MOCK_AI:
        # Extract skills and create basic questions
        skills = parsed_resume.get("skills", [])[:5]
        projects = parsed_resume.get("projects", [])[:2]
        
        base_questions = []
        
        for skill in skills:
            base_questions.append({
                "type": "skill",
                "topic": skill,
                "question": f"You listed {skill} in your skills. Can you explain your experience with it?"
            })
        
        for proj in projects:
            proj_name = proj.get("name", "your project") if isinstance(proj, dict) else proj
            base_questions.append({
                "type": "project",
                "topic": proj_name,
                "question": f"Tell me about {proj_name}. What was your role and what challenges did you face?"
            })
        
        # Add interview flow (intro, behavioral, closing)
        questions_with_flow = add_interview_flow_to_questions(base_questions)
        
        return {
            "role": parsed_resume.get("target_role", "Software Developer"),
            "difficulty": "intermediate",
            "questions": questions_with_flow
        }
    
    # AI-based generation
    try:
        prompt = f"""
Based on this resume, generate personalized interview questions.

Resume: {json.dumps(parsed_resume)}

Return ONLY valid JSON:
{{
    "role": "<detected role>",
    "difficulty": "<junior/intermediate/senior>",
    "questions": [
        {{"type": "introduction", "topic": "Self Introduction", "question": "Tell me about yourself and your background..."}},
        {{"type": "skill", "topic": "<skill from resume>", "question": "<specific question>"}},
        {{"type": "project", "topic": "<project name>", "question": "<specific question>"}},
        ...
        {{"type": "behavioral", "topic": "Strengths", "question": "What are your key strengths?"}},
        {{"type": "behavioral", "topic": "Challenges", "question": "Tell me about a challenge you overcame..."}},
        {{"type": "closing", "topic": "Questions", "question": "Do you have any questions for us?"}}
    ]
}}

Include 8-10 questions total:
1. Introduction (first)
2. 4-5 skill/project questions from resume
3. 2 behavioral questions
4. Closing question (last)
"""

        response = client.models.generate_content(
            model="models/gemini-flash-lite-latest",
            contents=prompt
        )

        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        return json.loads(text.strip())

    except Exception as e:
        print(f"Resume question generation error: {e}")
        # Fallback to mock
        return generate_questions.__wrapped__(parsed_resume) if hasattr(generate_questions, '__wrapped__') else {
            "role": "Software Developer",
            "difficulty": "intermediate", 
            "questions": [INTRO_QUESTION] + DEFAULT_QUESTIONS[:5] + BEHAVIORAL_QUESTIONS[:2] + [CLOSING_QUESTION]
        }