import pandas as pd
import json
import matplotlib.pyplot as plt
from datetime import datetime
from collections import Counter
import os
import time
import random

# ==========================================
# 👇 PASTE YOUR GOOGLE SHEET CSV LINK HERE 👇
LIVE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTQO1O6tuJ-BykB1-96MjCERmbqV205_0QFGRT6s5h1opfAFygWJb98gBvvuXLBKLb7-LG8Q1Uh0MMI/pub?gid=2101622849&single=true&output=csv" 
# ==========================================

def update_portfolio():
    print("🚀 Starting Engine...")

    # 1. THE CACHE BUSTER
    if "?" in LIVE_SHEET_URL:
        secure_url = f"{LIVE_SHEET_URL}&cb={int(time.time())}"
    else:
        secure_url = f"{LIVE_SHEET_URL}?cb={int(time.time())}"
        
    print(f"🔗 Fetching from: {secure_url}")

    # 2. READ DATA
    try:
        df = pd.read_csv(secure_url)
        print(f"✅ Downloaded {len(df)} rows.")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return

    problems = []
    
    # 3. PROCESS DATA
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

    # 4. SORTING LOGIC (UPDATED FOR LATEST-FIRST)
    try:
        # STEP A: Reverse the list first. 
        # This ensures that for problems on the SAME day, the one you added LAST (bottom of sheet) comes FIRST.
        problems.reverse()

        # STEP B: Sort by Date Descending.
        # Python's sort is "Stable", so it keeps the relative order from Step A for same-day items.
        problems.sort(key=lambda x: datetime.strptime(x['date'], "%d/%m/%Y"), reverse=True)
    except:
        print("⚠️ Date sorting skipped (Check date format in Sheet).")

    # 5. UPDATE JSON
    with open("problems.json", "w") as f:
        json.dump(problems, f, indent=2)
    print(f"✅ Updated problems.json with {len(problems)} records.")

    # 6. GENERATE PIE CHART
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

    # 7. UPDATE README.md
    total_count = len(problems)
    readme_content = f"""# 🚀 Ananth's Engineering Log
### ⚡ Automated Career Tracker
- **Total Problems Solved:** {total_count} 🔥
- **System Status:** Online 🟢

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
    
    readme_content += "\n[View Full Archive](https://ananth9911.github.io)"

    with open("README.md", "w") as f:
        f.write(readme_content)
    print("✅ Updated README.md")

if __name__ == "__main__":
    update_portfolio()
