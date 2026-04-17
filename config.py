"""アングル分類タクソノミと補助関数"""
from __future__ import annotations

ANGLE_TAXONOMY: dict[str, dict[str, dict[str, str]]] = {
    "水平視点": {
        "正面":           {"booru": "front_view",         "text": "front view portrait"},
        "3/4ビュー":      {"booru": "three-quarter_view", "text": "three quarter view"},
        "真横":           {"booru": "from_side",          "text": "side profile"},
        "斜め後ろ":       {"booru": "looking_back",       "text": "looking over shoulder"},
        "真後ろ":         {"booru": "from_behind",        "text": "back view from behind"},
    },
    "垂直視点": {
        "アオリ":         {"booru": "from_below",         "text": "low angle shot"},
        "フカン":         {"booru": "from_above",         "text": "high angle overhead"},
    },
    "距離": {
        "全身":           {"booru": "full_body",          "text": "full body shot"},
        "カウボーイ":     {"booru": "cowboy_shot",        "text": "cowboy shot mid thigh"},
        "ウエストアップ": {"booru": "upper_body",         "text": "waist up portrait"},
        "バストアップ":   {"booru": "portrait",           "text": "bust shot head and shoulders"},
        "クローズアップ": {"booru": "close-up",           "text": "face close up portrait"},
    },
    "特殊": {
        "ダッチアングル": {"booru": "dutch_angle",        "text": "dutch angle tilted"},
        "魚眼":           {"booru": "fisheye",            "text": "fisheye lens"},
        "POV":            {"booru": "pov",                "text": "first person pov"},
        "あお向け":       {"booru": "on_back",            "text": "lying on back"},
        "うつ伏せ":       {"booru": "on_stomach",         "text": "lying on stomach"},
    },
}

KEYWORD_TRANSLATIONS: dict[str, str] = {
    "女性": "1girl",
    "女の子": "1girl",
    "少女": "1girl",
    "男性": "1boy",
    "男の子": "1boy",
    "少年": "1boy",
    "立ち絵": "standing",
    "座り": "sitting",
    "笑顔": "smile",
    "ポートレート": "portrait",
    "イラスト": "illustration",
    "アニメ": "anime",
}


def translate_keyword(keyword: str) -> str:
    """日本語→英語の簡易変換。未登録語はそのまま通す。"""
    if not keyword:
        return ""
    return " ".join(
        KEYWORD_TRANSLATIONS.get(part, part)
        for part in keyword.strip().split()
    )


def iter_angles():
    """(category, angle_name, cfg) をイテレート"""
    for cat, angles in ANGLE_TAXONOMY.items():
        for name, cfg in angles.items():
            yield cat, name, cfg
