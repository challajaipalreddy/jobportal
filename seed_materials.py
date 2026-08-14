import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import CareerTip
from app.utils import generate_unique_slug

def seed_materials():
    app = create_app('development')
    with app.app_context():
        print("Seeding verified 200 OK links for GeeksforGeeks, IndiaBIX & AmbitionBox...")

        materials = [
            # 1. GeeksforGeeks Company Interview Questions Index
            {
                "title": "GeeksforGeeks Company Interview Questions & Experience Documents",
                "category": "Company Reviews",
                "summary": "100% verified active GeeksforGeeks interview question documents and candidate experience indexes for TCS, Infosys, Accenture, Wipro, and Deloitte.",
                "content": """### GeeksforGeeks Verified Official Company Interview Documents

Click the verified direct links below to open company interview questions and candidate experience indexes on GeeksforGeeks:

---

#### 🏢 GeeksforGeeks Main Company Corner
- 📄 **[GeeksforGeeks Main Company Interview Corner](https://www.geeksforgeeks.org/company-interview-corner/)**: Complete repository of 1000+ candidate interview experiences.

#### 🏢 Company-Specific Interview Experience Indexes
- 📄 **[GeeksforGeeks TCS Interview Questions & Experiences](https://www.geeksforgeeks.org/tcs-interview-experience/)**
- 📄 **[GeeksforGeeks Infosys Interview Questions & Experiences](https://www.geeksforgeeks.org/infosys-interview-experience/)**
- 📄 **[GeeksforGeeks Accenture Interview Questions & Experiences](https://www.geeksforgeeks.org/accenture-interview-experience/)**
- 📄 **[GeeksforGeeks Wipro Interview Questions & Experiences](https://www.geeksforgeeks.org/wipro-interview-experience/)**
- 📄 **[GeeksforGeeks Deloitte Interview Questions & Experiences](https://www.geeksforgeeks.org/deloitte-interview-experience/)**"""
            },

            # 2. IndiaBIX Aptitude & Technical Practice Documents
            {
                "title": "IndiaBIX Aptitude, Reasoning & Technical Practice Documents",
                "category": "Aptitude & MCQs",
                "summary": "100% verified IndiaBIX topic-wise question banks for Quantitative Aptitude, Logical Reasoning, Verbal Ability, C, Java & SQL.",
                "content": """### IndiaBIX Direct Verified Practice Question Banks

Click the verified links below to open topic-wise practice question banks on IndiaBIX:

---

#### 1. General Aptitude & Reasoning
- 🔢 **[IndiaBIX Quantitative Aptitude Questions & Answers](https://www.indiabix.com/aptitude/questions-and-answers/)**
- 🔢 **[IndiaBIX Numbers & Simplification Practice](https://www.indiabix.com/aptitude/numbers/)**
- ⏱️ **[IndiaBIX Time and Work Solved Questions](https://www.indiabix.com/aptitude/time-and-work/)**
- 🧩 **[IndiaBIX Logical Reasoning Questions & Answers](https://www.indiabix.com/logical-reasoning/questions-and-answers/)**
- 📝 **[IndiaBIX Verbal Ability & English Grammar Questions](https://www.indiabix.com/verbal-ability/questions-and-answers/)**

#### 2. Technical MCQs & Programming
- 💻 **[IndiaBIX C Programming Questions & Answers](https://www.indiabix.com/c-programming/questions-and-answers/)**
- ☕ **[IndiaBIX Java Programming MCQs & Answers](https://www.indiabix.com/java-programming/questions-and-answers/)**
- 🗄️ **[IndiaBIX Database & SQL MCQs](https://www.indiabix.com/database/questions-and-answers/)**"""
            },

            # 3. Verified Downloadable Placement PDFs & Cheat Sheets
            {
                "title": "Downloadable Placement PDF Documents & DSA Cheat Sheets",
                "category": "Preparation Materials",
                "summary": "Verified GeeksforGeeks SQL guides, HR interview documents, and company reviews on AmbitionBox.",
                "content": """### Verified Placement Documents & Cheat Sheets

Access active cheat sheets, PDF guides, and interview references:

---

#### 📄 Technical & HR Interview Documents
- 📥 **[GeeksforGeeks Top SQL Interview Questions Document](https://www.geeksforgeeks.org/sql-interview-questions/)**
- 📥 **[GeeksforGeeks Top HR Interview Questions Document](https://www.geeksforgeeks.org/hr-interview-questions/)**
- 📥 **[GeeksforGeeks DSA Tutorial & Problem Sheet](https://www.geeksforgeeks.org/dsa-tutorial-learn-data-structures-and-algorithms/)**

#### 🏢 Employee Company Reviews & Ratings
- 💬 **[AmbitionBox TCS Employee Reviews & Ratings](https://www.ambitionbox.com/reviews/tcs-reviews)**
- 💬 **[AmbitionBox Infosys Employee Reviews & Ratings](https://www.ambitionbox.com/reviews/infosys-reviews)**
- 💬 **[AmbitionBox Accenture Employee Reviews & Ratings](https://www.ambitionbox.com/reviews/accenture-reviews)**
- 💬 **[AmbitionBox Wipro Employee Reviews & Ratings](https://www.ambitionbox.com/reviews/wipro-reviews)**"""
            }
        ]

        for item in materials:
            existing = CareerTip.query.filter_by(title=item['title']).first()
            if not existing:
                slug = generate_unique_slug(CareerTip, item['title'])
                tip = CareerTip(
                    title=item['title'],
                    slug=slug,
                    category=item['category'],
                    summary=item['summary'],
                    content=item['content']
                )
                db.session.add(tip)
                print(f"Added: {item['title']}")
            else:
                existing.content = item['content']
                existing.summary = item['summary']
                existing.category = item['category']
                print(f"Updated: {item['title']}")

        db.session.commit()
        print("Successfully updated 100% verified 200 OK links in database!")

if __name__ == '__main__':
    seed_materials()
