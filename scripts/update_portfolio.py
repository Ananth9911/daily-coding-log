import pandas as pd
import json
import matplotlib.pyplot as plt
from datetime import datetime
from collections import Counter
import os

# ==========================================
# 👇 PASTE YOUR GOOGLE SHEET LINK HERE 👇
LIVE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTQO1O6tuJ-BykB1-96MjCERmbqV205_0QFGRT6s5h1opfAFygWJb98gBvvuXLBKLb7-LG8Q1Uh0MMI/pub?gid=2101622849&single=true&output=csv" 
# ==========================================

def update_portfolio():
    print("🚀 Connecting to Google Cloud Sheet...")
    
    # 1. READ THE LIVE DATA
    try:
        # This reads the CSV directly from the URL
        df = pd.read_csv(LIVE_SHEET_URL)
        print(f"✅ Connection Successful. Found {len(df)} rows.")
    except Exception as e:
        print(f"❌ Error reading Sheet: {e}")
        return

    problems = []
    
    # 2. PROCESS DATA (Using your exact column names)
    for index, row in df.iterrows():
        try:
            # Skip empty rows
            date_val = str(row['Date']).strip()
            name_val = str(row['Problem Name']).strip()
            
            if date_val == 'nan' or name_val == 'nan' or date_val == '': 
                continue

            problems.append({
                "date": date_val,
                "name": name_val,
                "topic": str(row['Topic']).strip(),
                "source": str(row['Source (Scaler/LC)']).strip()
            })
        except:
            continue

    # 3. SORT BY DATE
    try:
        # Assuming date format is DD/MM/YYYY or similar
        problems.sort(key=lambda x: datetime.strptime(x['date'], "%d/%m/%Y"), reverse=True)
    except:
        print("⚠️ Date format warning (Expected DD/MM/YYYY). Sorting as text.")

    # 4. SAVE TO JSON (This updates the website content)
    with open("problems.json", "w") as f:
        json.dump(problems, f, indent=2)
    print(f"✅ Saved {len(problems)} problems to database.")

    # 5. GENERATE PIE CHART IMAGE
    topics = [p['topic'] for p in problems if p['topic'] != 'nan']
    topic_counts = Counter(topics)
    
    if topic_counts:
        plt.figure(figsize=(10, 6))
        plt.style.use('dark_background')
        
        most_common = topic_counts.most_common(8)
        labels = [x[0] for x in most_common]
        sizes = [x[1] for x in most_common]
        colors = ['#4ADE80', '#2ea44f', '#22863a', '#1a7f37', '#60a5fa', '#3b82f6', '#2563eb', '#888888']
        
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors[:len(labels)])
        plt.title('Technical Focus', color='white')
        
        # Save explicitly to the root directory
        plt.savefig('topic_breakdown.png', transparent=True)
        print("✅ Generated Pie Chart.")

if __name__ == "__main__":
    update_portfolio()
