# app/rich_articles.py
"""
High-Value Educational & Career Preparation Guides for Google AdSense Approval.
Provides unique, in-depth value to job seekers, freshers, and campus candidates.
"""

RICH_ARTICLES = [
    {
        "title": "Complete TCS NQT Placement & Selection Process Guide for Freshers",
        "category": "Placement Preparation",
        "summary": "Detailed breakdown of the TCS National Qualifier Test (NQT) syllabus, exam pattern, section-wise timing, coding questions, and technical interview strategies.",
        "content": """### TCS NQT Placement Guide: Exam Pattern, Syllabus & Interview Preparation

The Tata Consultancy Services (TCS) National Qualifier Test (NQT) is one of India's largest hiring exams for fresh engineering, computer application, and science graduates. Passing the TCS NQT opens doors to **TCS Ninja (3.36 LPA)** and **TCS Digital (7.0 - 9.0 LPA)** roles.

---

#### 1. TCS NQT Test Pattern & Time Duration

The assessment is divided into two major sections: **Foundation Section** and **Advanced Section**.

- **Foundation Section (75 Minutes)**:
  - *Numerical Ability*: 20 Questions (25 Mins) - Focuses on Percentages, Profit & Loss, Ages, Data Interpretation, and Number Systems.
  - *Verbal Ability*: 25 Questions (25 Mins) - Focuses on Reading Comprehension, Sentence Completion, Error Spotting, and Grammar.
  - *Reasoning Ability*: 20 Questions (25 Mins) - Focuses on Syllogisms, Blood Relations, Data Sufficiency, and Seating Arrangement.

- **Advanced Section (90 Minutes - For TCS Digital / Prime)**:
  - *Advanced Quantitative & Reasoning*: 15 Questions (25 Mins).
  - *Advanced Coding*: 2 Hands-on Coding Problems (60 Mins) in C, C++, Java, Python, or Perl.

---

#### 2. Key Coding Topics & Frequently Asked Questions

1. **Array & String Manipulation**:
   - Count frequency of elements in an array.
   - Reverse a string without changing special character positions.
   - Find all small/large elements and sub-array sums.

2. **Mathematical Algorithms**:
   - Prime number range checking & GCD/LCM calculation.
   - Armstrong number, Fibonacci series generation, and Factorial of large numbers.

---

#### 3. Technical & HR Interview Strategy

During the TCS Technical Interview round, candidates are typically evaluated on:
- **Core Fundamentals**: OOPs concepts (Polymorphism, Inheritance, Encapsulation), DBMS SQL queries (JOINs, GROUP BY), and Data Structures (LinkedLists vs Arrays).
- **Academic Project Deep Dive**: Be ready to explain your final year project's architecture, database schema, algorithms used, and your personal contribution.
- **HR Scenarios**: Willingness to relocate, night shift flexibility, and 2-year service agreement terms."""
    },
    {
        "title": "Top 20 Technical HR Interview Questions & Standard STAR Answers",
        "category": "Interview Tips",
        "summary": "Master the STAR (Situation, Task, Action, Result) method to answer behavioral, situational, and HR interview questions confidently.",
        "content": """### How to Answer Behavioral & Technical HR Interview Questions

HR rounds assess your communication skills, cultural fit, problem-solving mindset, and professional attitude. The most effective framework to structure your answers is the **STAR Method** (Situation, Task, Action, Result).

---

#### 1. What is the STAR Method?

- **S - Situation**: Describe the specific background or context of the challenge you faced.
- **T - Task**: Explain your responsibility or goal in that situation.
- **A - Action**: Detail the concrete steps you took to address the problem.
- **R - Result**: Quantify the outcome and share what you learned from the experience.

---

#### 2. Top 5 Frequently Asked HR Questions & Model Responses

##### Q1: "Tell me about a time you faced a difficult conflict in a team project."
- **Situation**: During our 3rd-year web development project, our group had a disagreement regarding whether to use SQL or MongoDB.
- **Task**: As team coordinator, I needed to resolve the conflict without delaying our project delivery milestone.
- **Action**: I organized a 30-minute structured comparison meeting where both sub-teams benchmarked query speed, schema requirements, and deployment complexity.
- **Result**: We mutually decided on PostgreSQL, met our project deadline, and received an 'A' grade for our technical documentation.

##### Q2: "Where do you see yourself in 5 years?"
- **Answer Focus**: Emphasize learning continuous technical skills, taking on module lead responsibilities, and adding measurable value to the organization rather than giving static title designations.

---

#### 3. General Rules for Freshers

- Never criticize past teammates or professors.
- Always highlight your eagerness to learn new tech stacks.
- Ask 1 or 2 thoughtful questions at the end of the interview about team culture or ongoing tech projects."""
    },
    {
        "title": "Data Structures & Algorithms (DSA) Roadmap for Campus Placements",
        "category": "Coding & DSA",
        "summary": "Step-by-step 90-day roadmap to master Arrays, Strings, Hashing, Trees, Dynamic Programming, and Graph algorithms for product and service hiring drives.",
        "content": r"""### 90-Day DSA Learning Roadmap for Software Engineering Roles

Mastering Data Structures and Algorithms (DSA) is essential for cracking coding rounds at companies like TCS Digital, Wipro, Infosys, Accenture, Amazon, and product startups.

---

#### Phase 1: Foundations & Time Complexity (Days 1 to 15)

1. **Pick One Language**: Stick to C++, Java, or Python. Master standard libraries (`std::vector`, `ArrayList`, `List`, `HashMap`).
2. **Big-O Notation**: Understand Time Complexity ($O(1), O(\log N), O(N), O(N \log N), O(N^2)$) and Space Complexity.
3. **Arrays & Strings**: Sliding Window technique, Two-Pointer technique, Prefix Sum, and Cadence's Algorithm.

---

#### Phase 2: Core Data Structures (Days 16 to 45)

- **Hashing & HashMaps**: Constant time lookup $O(1)$ for sub-array sum problems and frequency counting.
- **Linked Lists**: Single/Double Linked List reversal, cycle detection (Floyd's Cycle Algorithm), and merging sorted lists.
- **Stacks & Queues**: Next Greater Element, Valid Parentheses matching, and Queue implementation using Stacks.

---

#### Phase 3: Trees, Graphs & Dynamic Programming (Days 46 to 90)

1. **Binary Search Trees (BST)**: Inorder/Preorder/Postorder traversals, Lowest Common Ancestor (LCA), and Height/Diameter of Binary Trees.
2. **Graph Algorithms**: Breadth-First Search (BFS), Depth-First Search (DFS), Dijkstra's Shortest Path Algorithm, and Topological Sorting.
3. **Dynamic Programming (DP)**: 0/1 Knapsack, Longest Common Subsequence (LCS), Coin Change problem, and Fibonacci memoization."""
    },
    {
        "title": "Top 25 Real-World SQL Query Interview Questions & Answers",
        "category": "Database & SQL",
        "summary": "Master SQL queries involving Nth highest salary, INNER/LEFT JOINs, GROUP BY aggregation, HAVING clause, and Window Functions (ROW_NUMBER, DENSE_RANK).",
        "content": """### SQL Query Interview Guide for Freshers & Developers

Structured Query Language (SQL) is tested in almost every technical round for Software Engineers, Data Analysts, and System Engineers.

---

#### 1. How to Find the 2nd Highest Salary in an Employee Table

```sql
SELECT MAX(salary) AS SecondHighestSalary 
FROM Employees 
WHERE salary < (SELECT MAX(salary) FROM Employees);
```

Or using SQL Window Functions (`DENSE_RANK`):

```sql
WITH RankedSalaries AS (
    SELECT name, salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk
    FROM Employees
)
SELECT name, salary FROM RankedSalaries WHERE rnk = 2;
```

---

#### 2. Difference Between WHERE and HAVING Clause

| Feature | WHERE Clause | HAVING Clause |
| :--- | :--- | :--- |
| **Filter Target** | Filters individual rows before aggregation | Filters aggregated groups after `GROUP BY` |
| **Aggregate Functions** | Cannot contain aggregate functions like `SUM()`, `AVG()` | Used with aggregate functions like `HAVING COUNT(*) > 5` |
| **Performance** | Evaluated earlier in statement execution | Evaluated after `GROUP BY` clause |

---

#### 3. Difference Between INNER JOIN and LEFT JOIN

- **INNER JOIN**: Returns only matching rows where the key exists in both the left and right tables.
- **LEFT JOIN (OUTER JOIN)**: Returns all rows from the left table, plus matching rows from the right table. Non-matching right table columns return `NULL`."""
    },
    {
        "title": "Infosys Off-Campus & System Engineer Hiring Complete Guide",
        "category": "Placement Preparation",
        "summary": "Everything you need to know about Infosys System Engineer (SE) and Specialist Programmer (SP) selection rounds, test pattern, and interview questions.",
        "content": """### Infosys Off-Campus Recruitment Guide: Pattern, Test Sections & Interview Tips

Infosys hires thousands of fresh graduates annually for **System Engineer (3.6 LPA)**, **Senior System Engineer (5.0 LPA)**, and **Specialist Programmer (9.5 LPA)** positions.

---

#### 1. Infosys Online Test Breakdown

The Infosys online exam tests mathematical ability, logical reasoning, verbal ability, pseudo-code analysis, and puzzle solving.

1. **Reasoning Ability**: 15 Questions (25 Mins).
2. **Mathematical Ability**: 10 Questions (35 Mins).
3. **Verbal Ability**: 20 Questions (20 Mins).
4. **Pseudo-code Section**: 5 Questions (10 Mins) - Evaluates code tracing, loop outputs, and Bitwise operations.
5. **Puzzle Solving**: 4 Questions (10 Mins) - High-difficulty logical puzzles.

---

#### 2. Key Focus Areas for Infosys Interviews

- **Object-Oriented Programming (OOPs)**: Be prepared to define Abstraction vs Encapsulation with real-world examples (e.g. ATM machine interface vs internal banking logic).
- **Basic Data Structures**: Arrays, Stacks, Queues, Binary Trees.
- **DBMS & SQL**: Write basic `SELECT`, `JOIN`, `GROUP BY` queries on live whiteboard/screen.
- **Communication & Adaptability**: Clear, professional verbal communication and readiness for project allocations across any technology domain."""
    }
]

def seed_rich_articles(app, db, CareerTip, generate_unique_slug):
    """Seed rich educational articles into database if not present."""
    with app.app_context():
        added_count = 0
        for article in RICH_ARTICLES:
            existing = CareerTip.query.filter_by(title=article['title']).first()
            if not existing:
                slug = generate_unique_slug(CareerTip, article['title'])
                tip = CareerTip(
                    title=article['title'],
                    slug=slug,
                    category=article['category'],
                    summary=article['summary'],
                    content=article['content'],
                    author='Campus to Career Experts'
                )
                db.session.add(tip)
                added_count += 1
            else:
                existing.summary = article['summary']
                existing.content = article['content']
                existing.category = article['category']
        
        if added_count > 0:
            db.session.commit()
            print(f"Successfully seeded {added_count} rich educational guides into database for AdSense compliance!")
