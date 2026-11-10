from pathlib import Path
Path("../../escape.txt").write_text("escaped", encoding="utf-8")
print("done")
