from __future__ import print_function
import os

path = os.path.join(os.path.dirname(__file__), "UnicodeData.txt")

f = open(path, "r")
text = f.read()
f.close()

result = []

openValue = None
for line in text.splitlines():
    line = line.split(";")
    value, name, category = line[:3]
    if category in ("Ps", "Pe", "Pi", "Pf"):
        if openValue is None:
            #assert category in ("Ps", "Pi")
            openValue = (value, name, category)
        else:
            #assert category in ("Pe", "Pf")
            if category not in ("Pe", "Pf"):
                result.append("#%s;%s;%s" % (value, name, category))
                result.append("")
            else:
                result.append("%s;%s;%s" % openValue)
                result.append("%s;%s;%s" % (value, name, category))
                result.append("")
                openValue = None

print("\n".join(result))
