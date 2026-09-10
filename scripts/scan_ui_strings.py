import os
import re
import glob

# Load translations.js directly
with open("frontend/src/utils/translations.js", "r", encoding="utf-8") as f:
    trans_content = f.read()

# Extract keys from translations.js
key_matches = re.findall(r'(\w+):\s*[\'"`]', trans_content)
# Let's parse languages in translations object
languages = ['en', 'hi', 'mr', 'ta', 'te', 'bn', 'gu', 'kn', 'ml', 'pa', 'or', 'as']

# Find all keys under 'en:'
en_block_match = re.search(r'en:\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}', trans_content, re.DOTALL)
if en_block_match:
    en_keys = re.findall(r'(\w+):\s*[\'"`]', en_block_match.group(1))
else:
    en_keys = []

print(f"Total English Keys in translations.js: {len(en_keys)}")

# Scan all JSX and JS files for raw user-visible strings vs t(...) calls
files_to_scan = glob.glob('frontend/src/**/*.jsx', recursive=True) + glob.glob('frontend/src/**/*.js', recursive=True)

# Ignore translations.js itself and index.js
files_to_scan = [f for f in files_to_scan if not f.endswith('translations.js') and not f.endswith('index.js')]

total_raw_strings = 0
hardcoded_strings = []
legit_invariants = []
untranslated_strings = []

# Regex patterns
jsx_text_pattern = re.compile(r'>\s*([A-Za-z0-9₹][^<>{}\n]+)\s*<')
t_pattern = re.compile(r"t\(\s*['\"]([^'\"]+)['\"]\s*(?:,\s*['\"]([^'\"]*)['\"])?\s*\)")

t_calls_found = []

for fpath in files_to_scan:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find t() calls
    for match in t_pattern.finditer(content):
        t_calls_found.append((fpath, match.group(1), match.group(2)))

    # Find JSX text nodes
    for match in jsx_text_pattern.finditer(content):
        text = match.group(1).strip()
        if not text:
            continue
        # Skip pure numbers, symbols, single characters
        if text.isdigit() or text in ['&rarr;', '&larr;', '•', '✓', '—', '/', ':', '₹']:
            continue
        
        # Check if legitimate invariant (Official names, ministries, acronyms, reference codes)
        is_invariant = False
        lower = text.lower()
        if any(inv in lower for inv in ['pmegp', 'mudra', 'stand-up india', 'cgtmse', 'nsfdc', 'nbcfdc', 'nskfdc', 'kvic', 'msme', 'dpdp act 2023', 'yojantra', 'aadhaar', 'pan', 'udyam', 'dbt', 'csc', 'rrb', 'sca']):
            legit_invariants.append((fpath, text))
            is_invariant = True
        elif any(term in text for term in ['₹', '%', 'Mo Grace', 'Mo', 'Cr', 'Lakh']):
            legit_invariants.append((fpath, text))
            is_invariant = True
        else:
            untranslated_strings.append((fpath, text))

print(f"Total files scanned: {len(files_to_scan)}")
print(f"Total t() translation calls found across components: {len(t_calls_found)}")
print(f"Legitimate intentional invariants: {len(legit_invariants)}")
print(f"Untranslated strings found: {len(untranslated_strings)}")

if untranslated_strings:
    print("\nSample untranslated strings:")
    for fpath, text in untranslated_strings[:20]:
        print(f"  [{os.path.basename(fpath)}] {text}")
