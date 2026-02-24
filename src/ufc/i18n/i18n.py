import json
from pathlib import Path
from typing import Dict

class I18nManager:
    """Manages translations for the GUI."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(I18nManager, cls).__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        self.locale = "en-US"
        self.locales_dir = Path(__file__).parent.parent / "locales"
        self.strings: Dict[str, Dict[str, str]] = {}
        self._load_all()

    def _load_all(self) -> None:
        if not self.locales_dir.exists():
            return
        for file in self.locales_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                lang_code = file.stem
                self.strings[lang_code] = data
            except Exception as e:
                print(f"Failed to load locale {file}: {e}")

    def set_locale(self, locale: str) -> None:
        self.locale = locale

    def get_available_locales(self) -> list[str]:
        return sorted(self.strings.keys())

    def t(self, key: str) -> str:
        """Translate key to current locale, fallback to en-US, then to the key itself."""
        if self.locale in self.strings and key in self.strings[self.locale]:
            return self.strings[self.locale][key]
        if "en-US" in self.strings and key in self.strings["en-US"]:
            return self.strings["en-US"][key]
        return key

i18n = I18nManager()
