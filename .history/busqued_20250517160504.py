import os
import re

TEMPLATES_DIR = 'templates'

def find_url_for_usage():
    urlfor_re = re.compile(r"\{\{\s*url_for\(\s*[\"']([\w\.]+)[\"'].*\)")
    found = []

    for root, dirs, files in os.walk(TEMPLATES_DIR):
        for filename in files:
            if filename.endswith('.html'):
                filepath = os.path.join(root, filename)
                with open(filepath, encoding='utf-8') as f:
                    for num, line in enumerate(f, 1):
                        match = urlfor_re.search(line)
                        if match:
                            endpoint = match.group(1)
                            found.append((filepath, num, endpoint, line.strip()))

    return found

if __name__ == "__main__":
    results = find_url_for_usage()
    if not results:
        print("No se encontraron usos de url_for en los templates.")
    else:
        print("Usos encontrados de url_for:")
        for filepath, num, endpoint, line in results:
            print(f"{filepath}:{num}: endpoint: '{endpoint}'")
            print(f"    {line}")
