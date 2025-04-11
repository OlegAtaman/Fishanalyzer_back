import os
import shutil
import tempfile

# 🔧 Заміни на повний шлях до твого файлу
ORIGINAL_FILE = "D:/projects/fin_stand/back/fish_serv/files/attachments/123123123123.rar"

def test_safe_open(filepath):
    print(f"[i] Перевірка відкриття файлу через тимчасову копію:")
    print(f"    Оригінальний шлях: {filepath}")

    if not os.path.exists(filepath):
        print(f"[✗] Файл не існує.")
        return

    try:
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, os.path.basename(filepath))
        shutil.copy(filepath, temp_path)

        print(f"[→] Створено копію: {temp_path}")

        with open(temp_path, "rb") as f:
            first_bytes = f.read(64)
            print(f"[✓] Успішно відкрито. Перші байти: {first_bytes.hex()[:32]}...")

        # 🔄 Можна видалити копію одразу після перевірки (опціонально)
        os.remove(temp_path)
        print(f"[•] Тимчасову копію видалено.")

    except Exception as e:
        print(f"[✗] Помилка: {e}")


if __name__ == "__main__":
    test_safe_open(ORIGINAL_FILE)
