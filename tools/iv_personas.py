"""Candidate personas for exercising the interview engine.

Answers are keyed by topic so the simulated candidate responds to what was
actually asked, without spending API calls on a second model driving them.
"""


def pick(bank, question, used):
    """Pick the answer whose keywords best match the question.

    Already-used answers are penalised so a persona does not parrot itself,
    but they stay available - a candidate repeating themselves is realistic
    and is exactly what the deflection logic needs to see.
    """
    q = (question or "").lower()
    best, best_score = None, 0
    for key, (kws, _text) in bank.items():
        score = sum(2 for k in kws if k in q)
        if key in used:
            score -= 3
        if score > best_score:
            best, best_score = key, score
    if best is None or best_score <= 0:
        best = next((k for k in bank if k not in used), list(bank)[-1])
    used.add(best)
    return bank[best][1]


STRONG = {
    "greet": (["how are you", "doing today", "feeling"],
        "im good thank you, bit nervous but excited"),
    "intro": (["yourself", "background", "introduce", "tell me about you"],
        "im Meera, final year cse. i did a six month internship at a fintech startup on "
        "their payments service, mostly java and spring boot. i owned the refunds api there"),
    "project": (["project", "built", "system did", "refunds"],
        "my main one is a refunds service. when a payment fails or a user asks for money "
        "back, my service reverses it. the tricky part is it has to be idempotent, because "
        "the payment gateway retries webhooks, so the same refund event arrives three or "
        "four times"),
    "role": (["your role", "personally", "you own", "contribution", "yourself build"],
        "i wrote the idempotency layer and the reconciliation job. another engineer did the "
        "gateway integration. the state machine for refund status was mine"),
    "howwork": (["how did", "how does", "mechanism", "under the hood", "walk me through"],
        "i keep an idempotency key which is the gateway event id, with a unique index on it "
        "in postgres. on insert conflict i return the existing refund instead of creating a "
        "second one. so a duplicate webhook becomes a no-op rather than a double refund"),
    "tradeoff": (["trade-off", "tradeoff", "downside", "why did you choose", "alternative"],
        "the unique index makes the write path slower and couples me to postgres. redis "
        "would be faster but if redis loses the key i double refund someone real money, so "
        "i chose durability over latency"),
    "db": (["database", "sql", "postgres", "mysql", "jpa", "index", "query", "transaction"],
        "postgres. unique index on gateway_event_id, composite index on user_id and "
        "created_at for the history screen. the refund write and the ledger entry go in one "
        "transaction, otherwise you can refund without recording it"),
    "java": (["java", "collection", "hashmap", "oop", "interface", "abstract", "thread",
              "concurren"],
        "hashmap isnt thread safe, two threads resizing it can corrupt the bucket array. "
        "concurrenthashmap locks per bucket so reads mostly dont block. i used it for a "
        "small in memory rate limiter"),
    "spring": (["spring", "dependency injection", "bean", "annotation", "rest"],
        "dependency injection means spring builds the objects and hands them to me instead "
        "of me calling new. i use constructor injection so the class cant exist in an "
        "invalid state and i can pass mocks in tests"),
    "docker": (["docker", "container", "kubernetes", "deploy", "devops"],
        "i containerised the refunds service. multi stage build, maven in the first stage, "
        "then just the jar on a jre base so the image is smaller. the db is not in the "
        "container, it is a managed instance, containers should be disposable"),
    "fail": (["went wrong", "failure", "bug", "hardest", "debug", "issue"],
        "we double refunded about forty users in staging. the gateway retried and my unique "
        "index wasnt there yet. the ledger reconciliation flagged the mismatch. that is why "
        "the idempotency key exists"),
    "test": (["test", "testing", "junit", "mock"],
        "junit and testcontainers, it spins a real postgres in docker for the repository "
        "tests. i specifically test the duplicate webhook case because that one costs money"),
    "scale": (["scale", "load", "performance", "concurrent", "bottleneck"],
        "about two hundred refunds a minute at peak. the bottleneck was the gateway call "
        "not my service, so i moved it to a queue and the api returns accepted immediately"),
    "behav": (["disagree", "team", "conflict", "difficult", "pressure", "deadline"],
        "i wanted the queue, my lead wanted a synchronous call for simplicity. i showed him "
        "our p99 was four seconds because of the gateway. we agreed to queue only the "
        "gateway call and keep the rest synchronous"),
    "strength": (["strength", "strong", "good at", "best qual"],
        "correctness under retries. i tend to ask what happens if this runs twice, which "
        "for payments matters a lot"),
    "goal": (["five years", "career", "goal", "future", "looking for"],
        "id like to go deep on distributed systems, especially exactly once processing"),
    "dunno": (["kafka", "microservice", "aws", "cloud", "security", "cache"],
        "honestly i havent used that in production. i understand the idea but id be "
        "guessing on the details, so id rather say i dont know it yet"),
}

OVERCLAIMER = {
    "greet": (["how are you", "doing today", "feeling"], "yeah im great sir very excited"),
    "intro": (["yourself", "background", "introduce"],
        "im Arjun, full stack developer, i have worked on microservices, docker, kubernetes, "
        "aws, kafka, redis, everything basically. i am very strong in java and system design"),
    "project": (["project", "built", "system did", "ecommerce"],
        "i built a scalable ecommerce microservices platform handling millions of requests, "
        "fully distributed with kafka and redis caching, deployed on kubernetes"),
    "role": (["your role", "personally", "you own", "contribution"],
        "i did everything sir, full architecture and backend and deployment, i was leading"),
    "howwork": (["how did", "how does", "mechanism", "under the hood", "walk me through",
                 "explain"],
        "basically it is microservices architecture so each service is independent and they "
        "communicate with each other and it is very scalable and fault tolerant"),
    "kafka": (["kafka", "queue", "event", "message", "broker"],
        "kafka is a message broker, it has producers and consumers and topics, used for real "
        "time streaming, it is very fast because it is distributed"),
    "docker": (["docker", "container", "kubernetes", "deploy", "orchestr"],
        "docker is containerisation, you write a dockerfile and build an image and run a "
        "container. kubernetes is orchestration, it manages containers and does auto scaling"),
    "db": (["database", "sql", "index", "query", "transaction", "postgres", "mysql", "redis"],
        "i used mysql and also mongodb, and redis for caching, it improves performance a lot"),
    "java": (["java", "hashmap", "collection", "thread", "concurren", "interface", "abstract"],
        "java is object oriented, we have inheritance polymorphism encapsulation abstraction. "
        "hashmap stores key value pairs and it is very fast, o of one"),
    "scale": (["scale", "load", "millions", "performance", "concurrent", "bottleneck"],
        "it can handle millions of requests because it is horizontally scalable with load "
        "balancer and auto scaling in kubernetes"),
    "specific": (["specific", "example", "exactly", "name one", "which", "how many",
                  "what number", "figure"],
        "sir it was a team project so i dont remember exact numbers but it was very large scale"),
    "fail": (["went wrong", "failure", "bug", "hardest", "debug"],
        "there were some bugs but we fixed them by debugging and testing, nothing major"),
    "behav": (["disagree", "team", "conflict", "pressure", "deadline"],
        "i always deliver on time sir, i work very hard and i am a good team player"),
    "goal": (["five years", "career", "goal", "future", "strength", "strong"],
        "in five years i want to be a solution architect, i am very passionate about tech"),
}

NERVOUS = {
    "greet": (["how are you", "doing today", "feeling"], "im fine sir"),
    "intro": (["yourself", "background", "introduce"],
        "im Kavya, btech it, fresher. i know python and little bit sql"),
    "project": (["project", "built", "system did", "library"],
        "i made a library management system in college. python and mysql"),
    "role": (["your role", "personally", "you own", "contribution"],
        "i did the database part mostly. my friend did the ui"),
    "howwork": (["how did", "how does", "mechanism", "walk me through", "explain",
                 "under the hood"],
        "um. it stores books and issues them to students. i think that is it"),
    "db": (["database", "sql", "mysql", "table", "query"],
        "i made three tables books students and issues. i used select and insert queries"),
    "join": (["join", "foreign key", "relationship", "normalis", "index"],
        "sorry sir i dont remember joins properly"),
    "python": (["python", "list", "dict", "function", "loop"],
        "i know lists and dictionaries and for loops. i have done basic programs"),
    "dunno1": (["docker", "kubernetes", "cloud", "aws", "deploy", "api", "rest"],
        "i dont know that sir sorry"),
    "dunno2": (["thread", "concurren", "cache", "performance", "scale", "security"],
        "i havent learned that yet"),
    "behav": (["team", "conflict", "difficult", "pressure", "challenge"],
        "in project my friend was not doing work so i did his part also"),
    "strength": (["strength", "strong", "good at"], "i am hardworking sir"),
    "goal": (["five years", "career", "goal", "future"],
        "i want to get a job first sir then learn more"),
}

RAMBLER = {
    "greet": (["how are you", "doing today", "feeling"], "im good sir thank you"),
    "intro": (["yourself", "background", "introduce"],
        "im Ravi Teja btech cse, i did one year internship as java developer, and i work on "
        "java spring boot my sequel"),
    "bus1": (["internship", "company", "responsib", "day to day", "worked on", "role"],
        "yeah so in that i made bus tracking system for our college, it shows real time "
        "location of buses to students using spring boot and google maps"),
    "bus2": (["project", "bus", "tracking", "built"],
        "the bus tracking one basically students dont know when bus is coming so i made the "
        "system, driver app sends location and student sees it in the map"),
    "bus3": (["how did", "mechanism", "receive", "real time", "actually", "walk me through"],
        "for that i used rest api only sir, controller service repository, my sequel with "
        "jpa hibernate"),
    "bus4": (["poll", "frequently", "how often", "many", "concurrent", "load", "scale"],
        "the student app calls the api again and again to get location. and i optimised it "
        "to reduce database writes"),
    "bus5": (["optimis", "threshold", "what did you change", "specific", "bottleneck"],
        "yeah in bus tracking i changed it so it updates only when the bus moves, that "
        "reduced the writes"),
    "java": (["java", "hashmap", "thread", "interface", "abstract", "collection"],
        "java i am comfortable sir, in bus tracking i used java only for the backend"),
    "spring": (["spring", "dependency injection", "bean", "jpa", "entity", "relationship"],
        "in my bus tracking project i used spring boot with jpa, standard structure only"),
    "docker": (["docker", "kubernetes", "deploy", "cloud", "aws"],
        "no sir i have not used docker much, only heard about it and seen videos, and cuber "
        "netties also i know it is for deployment"),
    "goal": (["five years", "career", "goal", "future", "strength", "strong"],
        "in five years i want to become senior java developer and learn aws cloud because "
        "everywhere it is required"),
}

PERSONAS = [
    ("Meera - strong, honest", "Meera Krishnan", STRONG, {
        "skills": ["Java", "Spring Boot", "PostgreSQL", "Docker", "JUnit"],
        "experience": [{"role": "Backend Engineering Intern",
                        "company": "fintech startup", "years": 1}],
        "projects": [{"name": "Refunds Service",
                      "technologies": ["Java", "Spring Boot", "PostgreSQL"]}]}),
    ("Arjun - overclaimer", "Arjun Reddy", OVERCLAIMER, {
        "skills": ["Java", "Microservices", "Kafka", "Docker", "Kubernetes", "AWS", "Redis"],
        "experience": [{"role": "Full Stack Developer", "years": 2}],
        "projects": [{"name": "Ecommerce Microservices Platform",
                      "technologies": ["Java", "Kafka", "Kubernetes", "Redis"]}]}),
    ("Kavya - nervous, low detail", "Kavya Sree", NERVOUS, {
        "skills": ["Python", "MySQL"],
        "projects": [{"name": "Library Management System",
                      "technologies": ["Python", "MySQL"]}]}),
    ("Ravi - deflects to one project", "Ravi Teja", RAMBLER, {
        "skills": ["Java", "Spring Boot", "MySQL", "Docker"],
        "experience": [{"role": "Java Developer Intern", "years": 1}],
        "projects": [{"name": "College Bus Tracking System",
                      "technologies": ["Java", "Spring Boot", "MySQL", "Google Maps API"]}]}),
]
