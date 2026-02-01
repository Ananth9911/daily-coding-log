import pandas as pd
import json
import matplotlib.pyplot as plt
from datetime import datetime
from collections import Counter
import os
import time
import random

# ==========================================
# 👇 CONFIGURATION SECTION 👇
# 1. YOUR PROBLEMS CSV (Keep existing)
LIVE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTQO1O6tuJ-BykB1-96MjCERmbqV205_0QFGRT6s5h1opfAFygWJb98gBvvuXLBKLb7-LG8Q1Uh0MMI/pub?gid=2101622849&single=true&output=csv"

# 2. YOUR MASTER PLAN CSV (Paste the NEW link here)
# Go to File > Share > Publish to Web > Select "Master_PLAN" > Select "CSV"
PLAN_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTQO1O6tuJ-BykB1-96MjCERmbqV205_0QFGRT6s5h1opfAFygWJb98gBvvuXLBKLb7-LG8Q1Uh0MMI/pub?gid=0&single=true&output=csv"
# ==========================================

def make_progress_bar(percent, length=10):
    # Generates a text bar like: [███████░░░]
    filled_length = int(length * percent // 100)
    bar = '█' * filled_length + '░' * (length - filled_length)
    return f"`[{bar}]` **{int(percent)}%**"

def get_curriculum_stats():
    # Fetches the Master Plan and calculates progress
    print("📊 Fetching Curriculum Data...")
    try:
        if "PASTE_YOUR" in PLAN_SHEET_URL:
            return "*(Configure PLAN_SHEET_URL in scripts/update_portfolio.py to see progress)*"
            
        # Cache Buster
        url = f"{PLAN_SHEET_URL}&cb={int(time.time())}" if "?" in PLAN_SHEET_URL else f"{PLAN_SHEET_URL}?cb={int(time.time())}"
        
        df = pd.read_csv(url)
        print(f"✅ Loaded Plan: {len(df)} rows")
        
        # ---------------------------------------------------------
        # 🎯 CUSTOM MODULE GROUPING LOGIC
        # ---------------------------------------------------------
        modules = {
            "Foundation": ["Intro to Programming"],
            
            "DSA (Data Structures)": [
                "DSA 1", "DSA 2", "DSA 3", "DSA 4", "DSA 4.2", 
                "Problem Solving", "DSA Practice", "DSA Revision"
            ],
            
            "Core (SQL/CS Fund)": [
                "Databases", "SQL", "CS Fundamentals"
            ],
            
            "System Design (LLD/HLD)": [
                "LLD", "High Level Design", "System Design"
            ]
        }
        # ---------------------------------------------------------
        
        stats_md = ""
        
        for name, keywords in modules.items():
            # Filter rows where the 'Module' column contains ANY of the keywords
            # We treat everything as string to avoid errors with NaNs
            mask = df['Module'].astype(str).apply(lambda x: any(k in x for k in keywords))
            
            subset = df[mask]
            total = len(subset)
            
            if total == 0: 
                continue
            
            # Count "Done" status (Trim whitespace to be safe)
            done = len(subset[subset['Status'].astype(str).str.strip() == 'Done'])
            percent = (done / total) * 100 if total > 0 else 0
            
            bar = make_progress_bar(percent)
            stats_md += f"- **{name}** {bar} *({done}/{total})*\n"
            
        return stats_md
    except Exception as e:
        print(f"⚠️ Plan Sync Failed: {e}")
        return "*(System Error: Could not load Plan)*"

def update_portfolio():
    print("🚀 Starting Engine...")

    # --- PART 1: FETCH PROBLEM LOGS ---
    if "?" in LIVE_SHEET_URL:
        secure_url = f"{LIVE_SHEET_URL}&cb={int(time.time())}"
    else:
        secure_url = f"{LIVE_SHEET_URL}?cb={int(time.time())}"
        
    print(f"🔗 Fetching Problems from: {secure_url}")

    try:
        df = pd.read_csv(secure_url)
        print(f"✅ Downloaded {len(df)} rows.")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return

    problems = []
    
    # --- PART 2: PROCESS PROBLEMS ---
    for index, row in df.iterrows():
        try:
            date_val = str(row['Date']).strip()
            name_val = str(row['Problem Name']).strip()
            topic_val = str(row['Topic']).strip()
            source_val = str(row['Source (Scaler/LC)']).strip()
            
            # Strict Filter: If name is empty or 'nan', SKIP
            if name_val.lower() == 'nan' or name_val == '': 
                continue

            problems.append({
                "date": date_val,
                "name": name_val,
                "topic": topic_val,
                "source": source_val
            })
        except:
            continue

    # Sorting Logic (Latest First)
    try:
        problems.reverse()
        problems.sort(key=lambda x: datetime.strptime(x['date'], "%d/%m/%Y"), reverse=True)
    except:
        print("⚠️ Date sorting skipped (Check date format in Sheet).")

    # Update JSON
    with open("problems.json", "w") as f:
        json.dump(problems, f, indent=2)
    print(f"✅ Updated problems.json with {len(problems)} records.")

    # --- PART 3: GENERATE PIE CHART ---
    topics = [p['topic'] for p in problems if p['topic'] != 'nan']
    topic_counts = Counter(topics)
    
    plt.figure(figsize=(10, 6))
    plt.style.use('dark_background')

    if topic_counts:
        most_common = topic_counts.most_common(8)
        labels = [x[0] for x in most_common]
        sizes = [x[1] for x in most_common]
        colors = ['#4ADE80', '#2ea44f', '#22863a', '#1a7f37', '#60a5fa', '#3b82f6', '#2563eb', '#888888']
        
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors[:len(labels)])
        plt.title('Technical Focus', color='white')
    else:
        plt.text(0.5, 0.5, "No Data Logged Yet", ha='center', va='center', color='white', fontsize=14)
        plt.title('Technical Focus (Waiting for Logs)', color='white')

    plt.savefig('topic_breakdown.png', transparent=True)
    plt.close()
    print("✅ Generated Pie Chart")

    # --- PART 4: FETCH CURRICULUM STATS ---
    curriculum_section = get_curriculum_stats()

    # --- PART 5: UPDATE README.md ---
    total_count = len(problems)
    readme_content = f"""# 🚀 Ananth's Engineering Log
### ⚡ Automated Career Tracker
- **Total Problems Solved:** {total_count} 🔥
- **System Status:** Online 🟢

### 🎓 Progress
{curriculum_section}

![Topic Breakdown](topic_breakdown.png)

### ⏳ Latest 10 Solved
| Date | Problem Name | Topic | Source |
| :--- | :--- | :--- | :--- |
"""
    if total_count > 0:
        for p in problems[:10]:
            readme_content += f"| {p['date']} | {p['name']} | {p['topic']} | {p['source']} |\n"
    else:
        readme_content += "| - | No logs found yet | - | - |\n"
    
    readme_content += "\n[View Full Archive](https://ananth9911.github.io/Ananth-Porfolio/)"

    with open("README.md", "w") as f:
        f.write(readme_content)
    print("✅ Updated README.md")

if __name__ == "__main__":
    update_portfolio()
