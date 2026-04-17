"""アングル分類タクソノミと補助関数

各アングルは以下を持つ:
- booru_tags: Danbooru系タグ候補 (複数あれば並列検索してマージ)
- text: Openverse/Wallhaven 向けフリーテキストクエリ
"""
from __future__ import annotations

ANGLE_TAXONOMY: dict[str, dict[str, dict[str, list[str] | str]]] = {
    "水平視点": {
        "正面 (Front)": {
            "booru_tags": ["front_view", "facing_viewer"],
            "text": "front view facing camera portrait",
        },
        "3/4ビュー (前)": {
            "booru_tags": ["three-quarter_view"],
            "text": "three quarter view front angle",
        },
        "真横 (Profile)": {
            "booru_tags": ["from_side", "profile"],
            "text": "side profile view",
        },
        "斜め後ろ (3/4 後)": {
            "booru_tags": ["looking_back"],
            "text": "looking over shoulder three quarter back",
        },
        "真後ろ (Back)": {
            "booru_tags": ["from_behind"],
            "text": "back view from behind",
        },
    },
    "垂直視点": {
        "アオリ (ローアングル)": {
            "booru_tags": ["from_below"],
            "text": "low angle shot looking up",
        },
        "フカン (ハイアングル)": {
            "booru_tags": ["from_above"],
            "text": "high angle shot looking down",
        },
        "俯瞰 (Bird's eye)": {
            "booru_tags": ["from_above"],
            "text": "bird eye view top down overhead",
        },
        "蟻の目 (Worm's eye)": {
            "booru_tags": ["from_below"],
            "text": "worms eye view from ground",
        },
        "見上げ": {
            "booru_tags": ["looking_up"],
            "text": "looking upward",
        },
        "見下ろし": {
            "booru_tags": ["looking_down"],
            "text": "looking downward",
        },
        "アイレベル": {
            "booru_tags": ["eye_contact"],
            "text": "eye level shot portrait",
        },
    },
    "ショット (距離)": {
        "エスタブリッシング": {
            "booru_tags": ["scenery"],
            "text": "establishing wide shot landscape with figure",
        },
        "ロングショット": {
            "booru_tags": ["full_body"],
            "text": "long shot full figure distant",
        },
        "全身 (Full Body)": {
            "booru_tags": ["full_body"],
            "text": "full body shot standing",
        },
        "カウボーイ/ニー": {
            "booru_tags": ["cowboy_shot"],
            "text": "cowboy shot knee up american shot",
        },
        "ウエストアップ (Medium)": {
            "booru_tags": ["upper_body"],
            "text": "medium shot waist up",
        },
        "バストアップ (MCU)": {
            "booru_tags": ["portrait"],
            "text": "medium close up bust shot chest up",
        },
        "クローズアップ (CU)": {
            "booru_tags": ["close-up"],
            "text": "close up face shoulders",
        },
        "フェイスアップ (BCU)": {
            "booru_tags": ["face"],
            "text": "face close up big close up headshot",
        },
        "ECU (目・唇)": {
            "booru_tags": ["eye_focus"],
            "text": "extreme close up eye lip detail",
        },
    },
    "特殊アングル": {
        "ダッチアングル (傾き)": {
            "booru_tags": ["dutch_angle"],
            "text": "dutch angle tilted canted",
        },
        "魚眼レンズ": {
            "booru_tags": ["fisheye"],
            "text": "fisheye lens wide distorted",
        },
        "POV (一人称)": {
            "booru_tags": ["pov"],
            "text": "first person point of view pov",
        },
        "OTS (肩越し)": {
            "booru_tags": ["over_shoulder"],
            "text": "over the shoulder ots shot",
        },
        "仰向け (On Back)": {
            "booru_tags": ["on_back"],
            "text": "lying on back supine",
        },
        "うつ伏せ (On Stomach)": {
            "booru_tags": ["on_stomach"],
            "text": "lying on stomach prone",
        },
        "横向き寝 (On Side)": {
            "booru_tags": ["on_side"],
            "text": "lying on side",
        },
        "空中/浮遊": {
            "booru_tags": ["midair", "floating"],
            "text": "midair floating levitating",
        },
        "ジャンプ": {
            "booru_tags": ["jumping"],
            "text": "jumping action pose",
        },
        "ダイナミックアングル": {
            "booru_tags": ["dynamic_angle", "action"],
            "text": "dynamic angle action shot",
        },
    },
    "光・構図": {
        "シルエット": {
            "booru_tags": ["silhouette"],
            "text": "silhouette backlit",
        },
        "逆光": {
            "booru_tags": ["backlighting"],
            "text": "backlight rim light sun behind",
        },
        "鏡越し": {
            "booru_tags": ["mirror", "reflection"],
            "text": "reflection in mirror",
        },
        "窓越し": {
            "booru_tags": ["window"],
            "text": "through window frame shot",
        },
        "シンメトリー": {
            "booru_tags": ["symmetry"],
            "text": "symmetrical composition centered",
        },
        "消失点/一点透視": {
            "booru_tags": ["vanishing_point"],
            "text": "vanishing point one point perspective",
        },
        "枠構図": {
            "booru_tags": ["framed"],
            "text": "frame within frame composition",
        },
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
