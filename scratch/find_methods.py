with open('backend/app/services/agent_nlp.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx1 = text.find('def detect_intent')
print("detect_intent index:", idx1)
# search for def after idx1
idx2 = text.find('    def ', idx1 + 20)
print("next method after detect_intent:", text[idx2:idx2+50])
