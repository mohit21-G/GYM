with open('backend/app/services/agent_nlp.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'def ' in l:
        print(f"{i+1}: {l.strip()}")
