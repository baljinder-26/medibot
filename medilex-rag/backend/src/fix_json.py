import json

def fix_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    changed = True
    while changed:
        changed = False
        try:
            json.loads(''.join(lines))
        except json.JSONDecodeError as e:
            print(f"Error at line {e.lineno}: {e.msg}")
            # Delete the offending line
            if "Expecting ':' delimiter" in e.msg or "Expecting ',' delimiter" in e.msg or "Expecting value" in e.msg:
                del lines[e.lineno - 1]
                changed = True
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Fixed json successfully")

fix_json(r'e:\medibot\medilex-rag\backend\src\auth_db.json')
