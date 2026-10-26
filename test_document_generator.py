
from document_generator import generate_document

sample_plan = {
    "title": "NOVA 30-Day Job Preparation Strategy",
    "sections": [
        {
            "heading": "Goal",
            "content": (
                "Prepare for entry-level software developer roles "
                "through Python, SQL, DSA, projects, and mock interviews."
            ),
        },
        {
            "heading": "Week 1: Fundamentals",
            "content": (
                "Days 1-3: Revise Python basics.\n"
                "Days 4-5: Practice SQL queries.\n"
                "Days 6-7: Solve beginner coding problems."
            ),
        },
        {
            "heading": "Week 2: Problem Solving",
            "content": (
                "Practice arrays, strings, dictionaries, and "
                "basic data structures."
            ),
        },
        {
            "heading": "Week 3: Projects and Interviews",
            "content": (
                "Revise your projects, practice explaining your code, "
                "and complete mock interviews."
            ),
        },
        {
            "heading": "Week 4: Applications and Revision",
            "content": (
                "Improve your resume, apply to suitable jobs, "
                "revise weak topics, and practice interviews daily."
            ),
        },
    ],
    "table": {
        "headers": ["Week", "Focus", "Target"],
        "rows": [
            ["Week 1", "Python and SQL", "Revise fundamentals"],
            ["Week 2", "DSA", "Solve practice problems"],
            ["Week 3", "Projects", "Prepare project explanations"],
            ["Week 4", "Revision", "Apply and practise interviews"],
        ],
    },
    "chart": {
        "title": "Illustrative Weekly Study Targets",
        "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
        "values": [25, 50, 75, 100],
        "ylabel": "Cumulative target (%)",
    },
}

for file_format in ["pdf", "docx", "pptx", "xlsx"]:
    output_path = generate_document(sample_plan, file_format)
    print(f"Created successfully: {output_path}")
