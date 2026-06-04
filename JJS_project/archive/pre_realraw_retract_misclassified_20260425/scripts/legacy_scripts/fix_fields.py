with open('scripts/generate_jjs_report.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace field accesses
content = content.replace("disps = [c['disp'] for c in curves]", "disps = [c['disp_nm'] for c in curves]")
content = content.replace("c['disp']", "c['disp_nm']")
content = content.replace("c['snap_f']", "c['snap_f_nN']")

with open('scripts/generate_jjs_report.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed field names')
