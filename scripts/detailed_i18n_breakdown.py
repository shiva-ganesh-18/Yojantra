import os
import re
import glob

# Load translations
with open("frontend/src/utils/translations.js", "r", encoding="utf-8") as f:
    content = f.read()

languages = ['en', 'hi', 'mr', 'ta', 'te', 'bn', 'gu', 'kn', 'ml', 'pa', 'or', 'as']

# Parse translations object accurately
# We can extract all keys per language block
lang_keys = {}
for lang in languages:
    pattern = rf'{lang}:\s*\{{([^}}]+(?:\{{[^}}]*\}}[^}}]*)*)\}}'
    m = re.search(pattern, content, re.DOTALL)
    if m:
        keys = re.findall(r'(\w+):\s*[\'"`]', m.group(1))
        lang_keys[lang] = set(keys)
    else:
        lang_keys[lang] = set()

en_keys = lang_keys.get('en', set())
print("Centralized Key Count per language:")
for lang, keys in lang_keys.items():
    print(f"  {lang}: {len(keys)} keys (Missing vs EN: {len(en_keys - keys)})")

# Scan components and pages
pages = glob.glob('frontend/src/pages/*.jsx')
components = glob.glob('frontend/src/components/*.jsx')

print("\n--- Scanning Pages ---")
page_issues = {}
for p in sorted(pages):
    with open(p, 'r', encoding='utf-8') as f:
        pcontent = f.read()
    t_calls = len(re.findall(r't\(', pcontent))
    # Count JSX text nodes
    raw_jsx = re.findall(r'>\s*([A-Za-z][^<>{}\n]{3,})\s*<', pcontent)
    # filter out code snippets or purely numbers
    clean_raw = []
    for r in raw_jsx:
        r_str = r.strip()
        if not any(k in r_str for k in ['&&', '||', '===', '=>', 'function', 'class']):
            clean_raw.append(r_str)
    
    print(f"{os.path.basename(p)}: {t_calls} t() calls, {len(clean_raw)} raw UI strings")
    if len(clean_raw) > 5 and t_calls < 5:
        page_issues[os.path.basename(p)] = "Needs full i18n integration"
    elif len(clean_raw) > 0:
        page_issues[os.path.basename(p)] = f"{len(clean_raw)} remaining raw strings"

print("\n--- Scanning Shared Components ---")
comp_issues = {}
for c in sorted(components):
    with open(c, 'r', encoding='utf-8') as f:
        ccontent = f.read()
    t_calls = len(re.findall(r't\(', ccontent))
    raw_jsx = re.findall(r'>\s*([A-Za-z][^<>{}\n]{3,})\s*<', ccontent)
    clean_raw = [r.strip() for r in raw_jsx if not any(k in r for k in ['&&', '||', '===', '=>', 'function'])]
    print(f"{os.path.basename(c)}: {t_calls} t() calls, {len(clean_raw)} raw UI strings")
    if len(clean_raw) > 3 and t_calls == 0:
        comp_issues[os.path.basename(c)] = f"{len(clean_raw)} raw strings (No t() hook)"
