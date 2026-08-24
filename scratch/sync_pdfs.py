import os
import shutil

src_dir = r"C:\Users\hp\Desktop\Notes"
dest_dir = r"c:\Users\hp\Desktop\jobportal\static\notes"

# Clean dest_dir
if os.path.exists(dest_dir):
    shutil.rmtree(dest_dir)
os.makedirs(dest_dir, exist_ok=True)

target_files = [
    'python/140 + Basic Python Programs (1).pdf',
    'python/python interview codes.pdf',
    'python/Project_Interview_Guide.pdf',
    'pandas.pdf',
    'java.pdf',
    'java1.pdf',
    'java2.pdf',
    'Jaava4.pdf',
    'Java_Conditional_Statements_Questions_Aligned.pdf',
    'Java_IO_Questions.pdf',
    'Java_Looping_Problems.pdf',
    'Java_Problems_Medium_Hard.pdf',
    'Java_String_Problems.pdf',
    'sq/Master SQl.pdf',
    'sq/SQL 100.pdf',
    'sq/SQL 45 questions.pdf',
    'sq/SQL questions by Google.pdf',
    'sq/SQL questions for placement .pdf',
    'sq/SQl Joins.pdf',
    'sq/Window Function.pdf',
    'sq/sql Cheat Sheet.pdf',
    'sq/sql business analsyt.pdf',
    'sq/sql definitions.pdf',
    'sq/sql full notes.pdf',
    'MongoDB_Interview_Questions.pdf',
    'apptitude/Aptitude Topics.pdf',
    'apptitude/topics.pdf',
    'Tcs NQT.pdf',
    'Deloitee.pdf',
    'Cognizant Data analyst.pdf',
    'Cognizant_Interview_Questions_2025.pdf',
    'DSA.pdf',
    'Power bi.pdf',
    'Power_BI_interview_QnA[1].pdf',
    'Myntra Data Analyst Interview.pdf',
    'Roadmap for data analysis.pdf',
    'aws.pdf'
]

copied_count = 0
missing_count = 0

for rel_path in target_files:
    src_file = os.path.join(src_dir, rel_path.replace('/', os.sep))
    dest_file = os.path.join(dest_dir, rel_path.replace('/', os.sep))
    
    if os.path.exists(src_file):
        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
        shutil.copy2(src_file, dest_file)
        copied_count += 1
        print(f"COPIED ({copied_count}/37): {rel_path}")
    else:
        missing_count += 1
        print(f"MISSING: {rel_path}")

print(f"\nCompleted! Total Copied: {copied_count}, Missing: {missing_count}")
