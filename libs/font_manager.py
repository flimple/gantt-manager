import customtkinter as ctk
import os

fonts = {
    "Sorean Bold": {
        "file_name": "Sorean Bold.otf",
        "is_loaded": False
    }
}

def load_font(font_name: str, size: int = 20, weight: str = "normal") -> ctk.CTkFont | None:
    if font_name not in fonts:
        return None
    
    font_info = fonts[font_name]
    
    if not font_info["is_loaded"]:
        # Chemin absolu : marche peu importe le dossier depuis lequel on lance l'app
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        font_path = os.path.join(base_dir, "assets", "fonts", font_info["file_name"])
        if not os.path.exists(font_path):
            return None
        ctk.FontManager.load_font(font_path)
        font_info["is_loaded"] = True

    return ctk.CTkFont(family=font_name, size=size, weight=weight)