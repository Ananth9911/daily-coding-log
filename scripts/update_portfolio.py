"""
update_portfolio.py v2
- Enriched problems.json (all fields except time_taken which you don't fill)
- Auto-generates cues.json and friction_stats.json
- Keeps existing pie chart, adds friction chart
- README now shows mastery % and difficulty breakdown
"""
import pandas as pd
import json
import matplotlib.pyplot as plt
from datetime import datetime
from collections import Counter, defaultdict
import time

LIVE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTQO1O6tuJ-BykB1-96MjCERmbqV205_0QFGRT6s5h1opfAFygWJb98gBvvuXLBKLb7-LG8Q1Uh0MMI/pub?gid=2101622849&single=true&output=csv"
PLAN_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTQO1O6tuJ-BykB1-96MjCERmbqV205_0QFGRT6s5h1opfAFygWJb98gBvvuXLBKLb7-LG8Q1Uh0MMI/pub?gid=0&single=true&output=csv"

def make_progress_bar(percent, length=10):
    filled = int(length * percent // 100)
    return f"`[{'█'*filled}{'░'*(length-filled)}]` **{int(percent)}%**"

def safe(val, fallback=""):
    s = str(val).strip()
    return fallback if s.lower() in ('nan','') else s

def get_curriculum_stats():
    try:
        df = pd.read_csv(f"{PLAN_SHEET_URL}&cb={int(time.time())}")
        modules = {
            "Foundation":             ["Intro to Programming"],
            "DSA":                    ["DSA 1","DSA 2","DSA 3","DSA 4","DSA 4.2","Problem Solving","DSA Practice","DSA Revision"],
            "Core (SQL/CS)":          ["Databases","SQL","CS Fundamentals"],
            "System Design (LLD/HLD)":["LLD","High Level Design","System Design"]
        }
        md = ""
        for name, keys in modules.items():
            mask   = df['Module'].astype(str).apply(lambda x: any(k in x for k in keys))
            subset = df[mask]
            total  = len(subset)
            if total == 0: continue
            done   = len(subset[subset['Status'].astype(str).str.strip() == 'Done'])
            pct    = (done/total)*100
            md    += f"- **{name}** {make_progress_bar(pct)} *({done}/{total})*\n"
        return md
    except Exception as ex:
        print(f"⚠️ Plan fetch failed: {ex}")
        return "*(Could not load plan)*"

def update_portfolio():
    print("🚀 Starting v2 Engine...")
    try:
        df = pd.read_csv(f"{LIVE_SHEET_URL}&cb={int(time.time())}")
        print(f"✅ {len(df)} rows downloaded")
    except Exception as ex:
        print(f"❌ Sheet fetch failed: {ex}"); return

    problems        = []
    cue_seen        = set()
    cues            = []
    topic_friction  = defaultdict(lambda: {"smooth":0,"struggled":0,"hard":0,"total":0})
    SKIP_NOTES      = {"review-not needed","need to redo","do recursion","simple array",
                       "basic maths","new 1","smooth","struggled","","nan"}

    for _, row in df.iterrows():
        name = safe(row.get('Problem Name',''))
        if not name: continue

        date       = safe(row.get('Date',''))
        topic      = safe(row.get('Topic',''),'Uncategorized')
        source     = safe(row.get('Source (Scaler/LC)',''),'Scaler')
        difficulty = safe(row.get('Difficulty (H/M/L)',''),'M')
        friction   = safe(row.get('Friction Level(Smooth/Struggled)',''),'Smooth')
        notes      = safe(row.get('Notes / Pattern Used',''))
        one_liner  = safe(row.get('One Sentence Idea',''))
        attempts   = safe(row.get('Attempt Count',''),'1')
        phase      = safe(row.get('Phase',''))
        review     = safe(row.get('Next Review Date',''))
        last_solved= safe(row.get('Last Solved Date',''))
        url        = safe(row.get('URL',''))

        problems.append({
            "date": date, "name": name, "topic": topic,
            "source": source, "difficulty": difficulty,
            "friction": friction, "notes": notes,
            "oneLiner": one_liner, "attempts": attempts,
            "phase": phase, "reviewDate": review,
            "lastSolved": last_solved, "url": url
        })

        # friction stats
        topic_friction[topic]["total"] += 1
        if 'smooth' in friction.lower():    topic_friction[topic]["smooth"] += 1
        if 'struggled' in friction.lower(): topic_friction[topic]["struggled"] += 1
        if difficulty == 'H':               topic_friction[topic]["hard"] += 1

        # cue extraction — skip trivial notes
        if notes and notes.lower().strip()[:25] not in SKIP_NOTES and len(notes) > 20:
            ck = (topic + notes[:40]).lower()
            if ck not in cue_seen:
                cue_seen.add(ck)
                cues.append({
                    "topic": topic, "cue": notes[:150],
                    "exampleProblem": name, "oneLiner": one_liner,
                    "difficulty": difficulty, "friction": friction
                })

    # sort latest first
    try:
        problems.sort(key=lambda x: datetime.strptime(x['date'],"%d/%m/%Y"), reverse=True)
    except: pass

    # ── WRITE JSONs ──────────────────────────────────────────
    with open("problems.json","w") as f: json.dump(problems, f, indent=2)
    print(f"✅ problems.json → {len(problems)} records (enriched)")

    with open("cues.json","w") as f: json.dump(cues, f, indent=2)
    print(f"✅ cues.json → {len(cues)} entries")

    friction_list = []
    for topic, c in topic_friction.items():
        mastery = round((c["smooth"]/c["total"])*100) if c["total"] else 0
        friction_list.append({**c, "topic": topic, "mastery": mastery})
    friction_list.sort(key=lambda x: x["total"], reverse=True)
    with open("friction_stats.json","w") as f: json.dump(friction_list, f, indent=2)
    print(f"✅ friction_stats.json → {len(friction_list)} topics")

    # ── PIE CHART (unchanged) ─────────────────────────────────
    plt.figure(figsize=(10,6)); plt.style.use('dark_background')
    tc = Counter(p['topic'] for p in problems if p['topic'] not in ('nan',''))
    mc = tc.most_common(8)
    if mc:
        labels = [x[0] for x in mc]; sizes = [x[1] for x in mc]
        colors = ['#4ADE80','#2ea44f','#22863a','#1a7f37','#60a5fa','#3b82f6','#2563eb','#888']
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors[:len(labels)])
        plt.title('Technical Focus', color='white')
    plt.savefig('topic_breakdown.png', transparent=True); plt.close()
    print("✅ topic_breakdown.png")

    # ── MASTERY BAR CHART (new) ───────────────────────────────
    top10 = [x for x in friction_list if x["total"] >= 5][:10]
    if top10:
        fig, ax = plt.subplots(figsize=(10,5)); fig.patch.set_alpha(0); ax.set_facecolor('none')
        labels_b = [x["topic"] for x in top10]
        mastery_b = [x["mastery"] for x in top10]
        colors_b = ['#4ADE80' if m>=70 else '#eab308' if m>=40 else '#ef4444' for m in mastery_b]
        ax.barh(labels_b, mastery_b, color=colors_b, height=0.6)
        ax.set_xlim(0,100); ax.set_xlabel('Mastery %', color='#888')
        ax.set_title('Topic Mastery (Smooth Rate)', color='white', pad=15)
        ax.tick_params(colors='#aaa')
        for sp in ax.spines.values(): sp.set_edgecolor('#333')
        plt.tight_layout()
        plt.savefig('mastery_chart.png', transparent=True, dpi=120); plt.close()
        print("✅ mastery_chart.png")

    # ── README ────────────────────────────────────────────────
    total   = len(problems)
    smooth  = sum(1 for p in problems if 'smooth' in p['friction'].lower())
    mastery = round((smooth/total)*100) if total else 0
    hard_c  = sum(1 for p in problems if p['difficulty']=='H')
    med_c   = sum(1 for p in problems if p['difficulty']=='M')
    curriculum = get_curriculum_stats()

    readme = f"""# 🚀 Ananth's Engineering Log
### ⚡ Automated Career Tracker
- **Total Problems Solved:** {total} 🔥  
- **Overall Mastery:** {mastery}% Smooth | Hard: {hard_c} | Medium: {med_c}
- **System Status:** Online 🟢

### 🎓 Curriculum Progress
{curriculum}
![Topic Breakdown](topic_breakdown.png)

### ⏳ Latest 10 Solved
| Date | Problem | Topic | Difficulty | Friction |
| :--- | :--- | :--- | :---: | :---: |
"""
    for p in problems[:10]:
        diff  = "🔴" if p['difficulty']=='H' else "🟡" if p['difficulty']=='M' else "🟢"
        fri   = "✅" if 'smooth' in p['friction'].lower() else "⚠️"
        readme += f"| {p['date']} | {p['name']} | {p['topic']} | {diff} | {fri} |\n"
    readme += "\n[→ View Full Archive](https://ananth9911.github.io/Ananth-Porfolio/)"

    with open("README.md","w") as f: f.write(readme)
    print(f"✅ README.md\n\n🎯 Done: {total} problems | {mastery}% mastery | {len(cues)} cues")

if __name__ == "__main__": update_portfolio()
