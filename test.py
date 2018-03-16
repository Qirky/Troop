import re

text = "111112211222"

p_id = 1

r = "{}+"

for match in re.finditer("{}+", text):
    print(match.start(), match.end())