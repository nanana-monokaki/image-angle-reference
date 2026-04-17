"""
アングル別リファレンス画像検索ツール
- 無料APIのみ (Danbooru / Openverse)
- 画像はサーバにキャッシュせずブラウザから直接CDNを参照
- サムネイルクリックではなく「元ページを開く」ボタンで権利元へ遷移
"""
from __future__ import annotations
import concurrent.futures as cf
import streamlit as st

from config import ANGLE_TAXONOMY, translate_keyword, iter_angles
from providers import ALL_PROVIDERS, ImageResult

st.set_page_config(
    page_title="アングル別リファレンス検索",
    page_icon="📐",
    layout="wide",
)


@st.cache_data(ttl=300, show_spinner=False)
def cached_search(
    provider_name: str,
    keyword: str,
    angle_tag: str,
    angle_text: str,
    safe: bool,
    limit: int,
) -> list[ImageResult]:
    provider = ALL_PROVIDERS[provider_name]()
    return provider.search(keyword, angle_tag, angle_text, safe, limit)


def run_search(
    keyword: str, providers: list[str], safe: bool, limit: int
) -> dict[tuple[str, str], list[ImageResult]]:
    tasks = [
        (cat, angle_name, p, cfg["booru"], cfg["text"])
        for cat, angle_name, cfg in iter_angles()
        for p in providers
    ]

    results: dict[tuple[str, str], list[ImageResult]] = {}

    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        futures = {
            ex.submit(
                cached_search, p, keyword, tag, text, safe, limit
            ): (cat, angle)
            for (cat, angle, p, tag, text) in tasks
        }
        for fut in cf.as_completed(futures):
            key = futures[fut]
            try:
                items = fut.result()
            except Exception:
                items = []
            results.setdefault(key, []).extend(items)

    return results


def render_grid(items: list[ImageResult], cols: int = 4) -> None:
    if not items:
        st.info("この条件での画像が見つかりませんでした。")
        return

    for row_start in range(0, len(items), cols):
        row = items[row_start : row_start + cols]
        columns = st.columns(cols)
        for col, item in zip(columns, row):
            with col:
                st.image(item.thumbnail_url, use_container_width=True)
                caption = (
                    f"**{item.title[:40]}**  \n"
                    f"👤 {item.author[:30]}  \n"
                    f"🌐 {item.source_name}"
                )
                if item.license:
                    caption += f"  \n📜 {item.license}"
                st.caption(caption)
                st.link_button(
                    "元ページを開く ↗",
                    item.source_url,
                    use_container_width=True,
                )


# --- Sidebar ---
with st.sidebar:
    st.title("📐 アングル別検索")
    st.caption("イラスト/アニメ制作のためのアングル参考ツール")

    keyword_raw = st.text_input(
        "キーワード",
        value="1girl",
        help="英語タグ (Danbooru形式) 推奨。例: 1girl, portrait, standing",
    )

    st.markdown("##### プロバイダ")
    selected_providers: list[str] = []
    for pname in ALL_PROVIDERS:
        if st.checkbox(pname, value=True, key=f"provider_{pname}"):
            selected_providers.append(pname)

    st.markdown("##### フィルタ")
    safe = st.toggle(
        "セーフサーチ",
        value=True,
        help="ONで年齢制限のある結果を除外（デフォルトON）",
    )
    if not safe:
        st.warning("⚠️ セーフサーチOFF: 年齢制限コンテンツが含まれる可能性があります")

    limit = st.slider("取得件数/アングル・プロバイダ", 5, 30, 12)

    search = st.button("🔍 検索", type="primary", use_container_width=True)

    st.markdown("---")
    st.caption(
        "🔒 画像はサーバにキャッシュしません  \n"
        "🔗 「元ページを開く」で権利元サイトへ遷移してください"
    )


# --- Search ---
if search:
    if not keyword_raw:
        st.warning("キーワードを入力してください。")
    elif not selected_providers:
        st.warning("プロバイダを1つ以上選択してください。")
    else:
        translated = translate_keyword(keyword_raw)
        with st.spinner("全アングルを並列検索中..."):
            st.session_state.results = run_search(
                translated, selected_providers, safe, limit
            )
        st.session_state.meta = {
            "keyword": keyword_raw,
            "translated": translated,
            "safe": safe,
            "providers": selected_providers,
        }


# --- Render ---
results = st.session_state.get("results")
meta = st.session_state.get("meta")

if not results:
    st.title("アングル別リファレンス画像検索")
    st.markdown(
        """
左のサイドバーで **キーワード** を入力して **検索** ボタンを押してください。

結果はアングル別タブで表示されます。
サムネイルはブラウザが直接プロバイダから読み込むため、このサーバには保存されません。
各画像の **「元ページを開く」** から権利元サイトへ遷移できます。

#### 検索ソース
- **Danbooru** — アニメ/イラスト系タグ付き画像 (rating g/s のみ表示)
- **Openverse** — CC ライセンスの一般画像 (写真含む)

#### 使い方のコツ
- Danbooru は英語タグが必要です: `1girl`, `standing`, `portrait` など
- 複数語で絞り込むと精度が上がります
- 有料 API (Twitter/X, Instagram, Pixiv 等) は規約上非対応
        """
    )
else:
    trans_note = (
        f" (→ `{meta['translated']}`)"
        if meta["translated"] != meta["keyword"]
        else ""
    )
    st.markdown(
        f"#### 🔎 `{meta['keyword']}`{trans_note}  "
        f"・ セーフサーチ: **{'ON' if meta['safe'] else 'OFF'}**  "
        f"・ ソース: {', '.join(meta['providers'])}"
    )

    category_tabs = st.tabs(list(ANGLE_TAXONOMY.keys()))
    for cat_tab, (category, angles) in zip(
        category_tabs, ANGLE_TAXONOMY.items()
    ):
        with cat_tab:
            angle_tabs = st.tabs(list(angles.keys()))
            for angle_tab, angle_name in zip(angle_tabs, angles.keys()):
                with angle_tab:
                    items = results.get((category, angle_name), [])
                    st.caption(f"**{len(items)}** 件")
                    render_grid(items, cols=4)
