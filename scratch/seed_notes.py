import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import StudyMaterial
from app.utils import generate_unique_slug

app = create_app()

preset_data = [
    # Python Notes & Coding
    ('140 + Basic Python Programs', 'Python Notes & Coding', 'python/140 + Basic Python Programs (1).pdf', 'bi-filetype-py', 'Complete beginner to advanced Python practice code collection.'),
    ('Python Interview Codes & Solutions', 'Python Notes & Coding', 'python/python interview codes.pdf', 'bi-code-square', 'Handpicked Python interview coding questions with step-by-step logic.'),
    ('Project Interview Guide', 'Python Notes & Coding', 'python/Project_Interview_Guide.pdf', 'bi-journal-code', 'How to explain Python projects in technical interviews.'),
    ('Pandas Data Analysis Notes', 'Python Notes & Coding', 'pandas.pdf', 'bi-table', 'Comprehensive Pandas library cheat sheet & data manipulation notes.'),

    # Java & OOPs Notes
    ('Java Core Complete Notes (Part 1)', 'Java & OOPs Notes', 'java.pdf', 'bi-filetype-java', 'Fundamentals of Java programming & OOPs concepts.'),
    ('Java Advanced Notes (Part 2)', 'Java & OOPs Notes', 'java1.pdf', 'bi-filetype-java', 'Classes, Objects, Inheritance & Interfaces in Java.'),
    ('Java Collections & Exception Notes', 'Java & OOPs Notes', 'java2.pdf', 'bi-filetype-java', 'Lists, Sets, Maps, and Exception Handling.'),
    ('Java Master Placement Guide', 'Java & OOPs Notes', 'Jaava4.pdf', 'bi-journal-bookmark', 'Java interview questions and placement prep notes.'),
    ('Java Conditional Statements Practice', 'Java & OOPs Notes', 'Java_Conditional_Statements_Questions_Aligned.pdf', 'bi-check-square', 'If-else and switch-case practice problems.'),
    ('Java I/O Questions & Solutions', 'Java & OOPs Notes', 'Java_IO_Questions.pdf', 'bi-hdd', 'File reading, writing & Scanner class questions.'),
    ('Java Looping Problems', 'Java & OOPs Notes', 'Java_Looping_Problems.pdf', 'bi-arrow-repeat', 'For loops, while loops, and pattern printing questions.'),
    ('Java Medium to Hard Problems', 'Java & OOPs Notes', 'Java_Problems_Medium_Hard.pdf', 'bi-exclamation-triangle', 'Advanced logic & problem solving in Java.'),
    ('Java String Problems', 'Java & OOPs Notes', 'Java_String_Problems.pdf', 'bi-type', 'String manipulation, reversal, and substring questions.'),

    # SQL & Database Notes
    ('Master SQL Complete Notes', 'SQL & Database Notes', 'sq/Master SQl.pdf', 'bi-database-fill', 'Complete SQL tutorial from basic SELECT to advanced JOINs.'),
    ('SQL 100 Interview Questions', 'SQL & Database Notes', 'sq/SQL 100.pdf', 'bi-database-check', 'Top 100 SQL questions asked in technical rounds.'),
    ('SQL 45 Important Questions', 'SQL & Database Notes', 'sq/SQL 45 questions.pdf', 'bi-database-gear', '45 high-frequency SQL problem sets with solutions.'),
    ('SQL Questions by Google', 'SQL & Database Notes', 'sq/SQL questions by Google.pdf', 'bi-google', 'Real SQL interview problems asked in Google drives.'),
    ('SQL Placement Questions', 'SQL & Database Notes', 'sq/SQL questions for placement .pdf', 'bi-briefcase', 'Campus placement specific SQL question bank.'),
    ('SQL Joins Master Notes', 'SQL & Database Notes', 'sq/SQl Joins.pdf', 'bi-diagram-3-fill', 'Visual guide to INNER, LEFT, RIGHT & FULL OUTER JOINs.'),
    ('SQL Window Functions Guide', 'SQL & Database Notes', 'sq/Window Function.pdf', 'bi-window-stack', 'ROW_NUMBER(), RANK(), DENSE_RANK(), and LEAD/LAG.'),
    ('SQL Cheat Sheet', 'SQL & Database Notes', 'sq/sql Cheat Sheet.pdf', 'bi-file-earmark-code', 'Handy SQL syntax cheat sheet for quick revision.'),
    ('SQL Business Analyst Notes', 'SQL & Database Notes', 'sq/sql business analsyt.pdf', 'bi-graph-up', 'Data analysis queries for Business Analyst roles.'),
    ('SQL Definitions & Theory', 'SQL & Database Notes', 'sq/sql definitions.pdf', 'bi-book-half', 'DDL, DML, DCL, TCL, ACID properties & Normalization.'),
    ('SQL Full Notes & Queries', 'SQL & Database Notes', 'sq/sql full notes.pdf', 'bi-file-earmark-text', 'Full handwritten SQL notes with query examples.'),
    ('MongoDB Interview Questions', 'SQL & Database Notes', 'MongoDB_Interview_Questions.pdf', 'bi-filetype-json', 'NoSQL & MongoDB interview question bank.'),

    # Aptitude & Reasoning Notes
    ('Aptitude Topics & Shortcuts', 'Aptitude & Reasoning Notes', 'apptitude/Aptitude Topics.pdf', 'bi-calculator', 'Quantitative aptitude formulas & shortcut calculation tricks.'),
    ('Complete Placement Aptitude Guide', 'Aptitude & Reasoning Notes', 'apptitude/topics.pdf', 'bi-puzzle', 'Comprehensive aptitude, logical & verbal reasoning notes.'),

    # Company Specific Placement Notes
    ('TCS NQT Complete Study Material', 'Company Specific Placement Notes', 'Tcs NQT.pdf', 'bi-building-fill-check', 'TCS NQT exam pattern, previous papers & sample questions.'),
    ('Deloitte Placement Guide', 'Company Specific Placement Notes', 'Deloitee.pdf', 'bi-building', 'Deloitte Analyst interview questions & test syllabus.'),
    ('Cognizant Data Analyst Material', 'Company Specific Placement Notes', 'Cognizant Data analyst.pdf', 'bi-file-earmark-bar-graph', 'Cognizant Data Analyst test pattern & preparation notes.'),
    ('Cognizant 2025 Interview Questions', 'Company Specific Placement Notes', 'Cognizant_Interview_Questions_2025.pdf', 'bi-question-circle', 'Recent Cognizant interview questions.'),
    ('Data Structures & Algorithms (DSA)', 'Company Specific Placement Notes', 'DSA.pdf', 'bi-diagram-2', 'Complete DSA notes covering Trees, Graphs & Dynamic Programming.'),

    # Data Science & Power BI Notes
    ('Power BI Master Notes', 'Data Science & Power BI Notes', 'Power bi.pdf', 'bi-bar-chart-line-fill', 'Complete Power BI visual dashboards & DAX formulas.'),
    ('Power BI Interview QnA', 'Data Science & Power BI Notes', 'Power_BI_interview_QnA[1].pdf', 'bi-file-earmark-easel', 'Top Power BI interview questions & answers.'),
    ('Myntra Data Analyst Interview Questions', 'Data Science & Power BI Notes', 'Myntra Data Analyst Interview.pdf', 'bi-bag-check', 'Real Myntra Data Analyst interview case studies.'),
    ('Roadmap for Data Analyst Career', 'Data Science & Power BI Notes', 'Roadmap for data analysis.pdf', 'bi-signpost-split', 'Step-by-step career path to become a Data Analyst.'),
    ('AWS Cloud Practitioner Guide', 'Data Science & Power BI Notes', 'aws.pdf', 'bi-cloud-check', 'AWS cloud services, S3, EC2 & certification basics.')
]

with app.app_context():
    added = 0
    for title, cat, rel_file, icon, desc in preset_data:
        existing = StudyMaterial.query.filter_by(title=title).first()
        if not existing:
            slug = generate_unique_slug(StudyMaterial, title)
            mat = StudyMaterial(
                title=title,
                slug=slug,
                category=cat,
                description=desc,
                file_path=f"static/notes/{rel_file}",
                icon=icon
            )
            db.session.add(mat)
            added += 1
    db.session.commit()
    print(f"Successfully seeded {added} preset PDF study materials into database! Total in DB: {StudyMaterial.query.count()}")
