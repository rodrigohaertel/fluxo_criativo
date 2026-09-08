import re
import sys

path = sys.argv[1]
out = sys.argv[2]
html = open(path, encoding="utf-8").read()
text = re.sub(r"<script.*?</script>", "", html, flags=re.S)
text = re.sub(r"<style.*?</style>", "", text, flags=re.S)
text = re.sub(r"<[^>]+>", "\n", text)
text = re.sub(r"\n\s*\n+", "\n", text)
open(out, "w", encoding="utf-8").write(text)
print(len(text))
