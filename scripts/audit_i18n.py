import os
import re
import glob
import json

def audit_frontend_multilingual():
    frontend_dir = os.path.abspath("frontend/src")
    jsx_files = glob.glob(os.path.join(frontend_dir, "**", "*.jsx"), recursive=True)
    js_files = glob.glob(os.path.join(frontend_dir, "**", "*.js"), recursive=True)
    all_files = jsx_files + js_files

    # 1. Load centralized translation dictionary
    from translations_inspect import get_translation_keys
    keys, lang_count = get_translation_keys()
    
    print(f"Total Centralized Translation Keys: {len(keys)}")
    print(f"Languages in Centralized System: {lang_count}")

if __name__ == "__main__":
    pass
