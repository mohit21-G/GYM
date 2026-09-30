with open("app/services/agent_nlp.py", "rb") as f:
    data = f.read()

bad = b"]\xaa\xaa\xe0\xaa\xbe\xe0\xaa\xa8\xe0\xab\x80|\xe0\xa4\xaa\xe0\xa4\xbe\xe0\xa4\xa8\xe0\xa5\x80)\""
good = b"]"
if bad in data:
    fixed = data.replace(bad, good, 1)
    with open("app/services/agent_nlp.py", "wb") as f:
        f.write(fixed)
    print("FIXED successfully!")
else:
    print("Bad sequence not found")

# Verify utf-8 decode
with open("app/services/agent_nlp.py", "r", encoding="utf-8") as f:
    text = f.read()
print("UTF-8 decoded successfully, total characters:", len(text))
