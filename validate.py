#!/usr/bin/env python3
"""SesliDefter index.html dogrulama scripti"""
import re, collections, subprocess, sys

try:
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
except FileNotFoundError:
    print("index.html bulunamadi!")
    sys.exit(1)

errors = []

# Ana scripti bul
scripts = list(re.finditer(r"<script>(.+?)</script>", content, re.DOTALL))
main_js = next((s.group(1) for s in scripts if "async function _appBaslat" in s.group(1)), None)

if not main_js:
    errors.append("Ana script (_appBaslat) bulunamadi!")
else:
    # 1. Syntax
    with open("/tmp/sd_check.js", "w") as f:
        f.write(main_js)
    r = subprocess.run(["node", "--check", "/tmp/sd_check.js"], capture_output=True, text=True)
    if r.returncode != 0:
        errors.append("SYNTAX HATASI:\n" + r.stderr)

    # 2. Global let duplicate (sadece satir basi - fonksiyon icindekiler local sayilir)
    global_lets = re.findall(r"(?m)^let (\w+)", main_js)
    dupes = {k:v for k,v in collections.Counter(global_lets).items() if v > 1}
    if dupes:
        errors.append(f"Duplicate global let: {dupes}")

    # 3. Kritik fonksiyonlar
    defined = set(re.findall(r"(?:async\s+)?function\s+(\w+)\s*\(", main_js))
    critical = ["_appBaslat","init","profilYukle","verileriYukle",
                "guncelleUI","go","rAna","sesBaslat","sesDurdur",
                "kayitKaydet","lsGizle","authGoster","rTakvim"]
    for fn in critical:
        if fn not in defined:
            errors.append(f"KRITIK FONKSIYON EKSIK: {fn}()")

    # 4. Brace dengesi
    opens, closes = main_js.count("{"), main_js.count("}")
    if opens != closes:
        errors.append(f"Parantez dengesi bozuk: {{ {opens} vs }} {closes}")

    # 5. Backtick
    if main_js.count("`") % 2 != 0:
        errors.append("Template literal kapanmamis!")

print("\n=== SesliDefter Dogrulama ===")
if errors:
    print(f"HATA ({len(errors)} adet):")
    for e in errors:
        print(f"  x {e}")
    sys.exit(1)
else:
    print("Tum kontroller gecti - deploy edilebilir!")
