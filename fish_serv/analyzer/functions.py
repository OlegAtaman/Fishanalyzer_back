import os
from django.conf import settings


SETTINGS_FILE_PATH = os.path.join(settings.BASE_DIR, 'settings.txt')

def write_settings(data):
    lines = [
        f"RULES_UPDT={'TRUE' if data.get('rules_update') else 'FALSE'}",
        f"SETTINGS_UPDT={'TRUE' if data.get('settings_update') else 'FALSE'}",
        "",
        f"SAVE_DROP={'ON' if data.get('save_drop') else 'OFF'}",
        f"REDIRECT_TO_SEC={'ON' if data.get('redirect_to_sec') else 'OFF'}",
        f"SEC_EMAIL={data.get('sec_email', '')}",
    ]
    with open(SETTINGS_FILE_PATH, 'w') as f:
        f.write('\n'.join(lines))

def read_settings():
    settings_data = {
        'rules_update': False,
        'settings_update': False,
        'save_drop': False,
        'redirect_to_sec': False,
        'sec_email': ''
    }

    if not os.path.exists(SETTINGS_FILE_PATH):
        return settings_data

    with open(SETTINGS_FILE_PATH, 'r') as f:
        for line in f.readlines():
            if line.startswith("SAVE_DROP="):
                settings_data['save_drop'] = line.strip().split("=")[1] == 'ON'
            elif line.startswith("REDIRECT_TO_SEC="):
                settings_data['redirect_to_sec'] = line.strip().split("=")[1] == 'ON'
            elif line.startswith("SEC_EMAIL="):
                settings_data['sec_email'] = line.strip().split("=")[1]
            elif line.startswith("RULES_UPDT="):
                settings_data['rules_update'] = line.strip().split("=")[1] == 'TRUE'
            elif line.startswith("SETTINGS_UPDT="):
                settings_data['settings_update'] = line.strip().split("=")[1] == 'TRUE'
    return settings_data