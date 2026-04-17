"""
アングル別リファレンス画像検索ツール
- 無料APIのみ (Danbooru / Openverse / Wallhaven)
- 画像はサーバにキャッシュせずブラウザから直接CDNを参照
- サムネイルクリックではなく「元ページを開く」ボタンで権利元へ遷移
"""
from __future__ import annotations
import concurrent.futures as cf
from collections import defaultdict
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


def _build_tasks(
    keyword: str, providers: list[str], limit: int
) -> list[tuple[str, str, str, str, str]]:
    """
    (category, angle_name, provider_name, angle_tag, angle_text) のタスクリストを生成。
    Danbooru は booru_tags のバリアント毎に 1 タスク(タグ別に並列検索→後でマージ)。
    Openverse / Wallhaven は angle 毎に 1 タスク(テキスト検索)。
    """
    tasks: list[tuple[str, str, str, str, str]] = []
    for cat, angle, cfg in iter_angles():
        booru_tags: list[str] = cfg.get("booru_tags") or []  # type: ignore
        text: str = cfg.get("text") or ""  # type: ignore
        for p in providers:
            if p == "Danbooru":
                for tag in booru_tags:
                    tasks.append((cat, angle, p, tag, ""))
            else:
                tasks.append((cat, angle, p, "", text))
    return tasks


def _interleave_by_source(items: list[ImageResult]) -> list[ImageResult]:
    """ソース別にラウンドロビンで並べ替え、偏りを減らす"""
    buckets: dict[str, list[ImageResult]] = defaultdict(list)
    for it in items:
        buckets[it.source_name].append(it)
    if not buckets:
        return items
    out: list[ImageResult] = []
    max_len = max(len(v) for v in buckets.values())
    for i in range(max_len):
        for src in buckets:
            if i < len(buckets[src]):
                out.append(buckets[src][i])
    return out


def run_search(
    keyword: str, providers: list[str], safe: bool, limit: int
) -> dict[tuple[str, str], list[ImageResult]]:
    tasks = _build_tasks(keyword, providers, limit)
    raw: dict[tuple[str, str], list[ImageResult]] = defaultdict(list)

    with cf.ThreadPoolExecutor(max_workers=12) as ex:
        futures = {
            ex.submit(cached_search, p, keyword, tag, text, safe, limit): (cat, angle)
            for (cat, angle, p, tag, text) in tasks
        }
        for fut in cf.as_completed(futures):
            key = futures[fut]
            try:
                raw[key].extend(fut.result())
            except Exception:
                pass

    # Dedup by thumbnail_url, then interleave by source for diversity
    merged: dict[tuple[str, str], list[ImageResult]] = {}
    for key, items in raw.items():
        seen: set[str] = set()
        deduped: list[ImageResult] = []
        for it in items:
            if it.thumbnail_url in seen:
                continue
            seen.add(it.thumbnail_url)
            deduped.append(it)
        merged[key] = _interleave_by_source(deduped)
    return merged


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
        help="英語タグ (Danbooru形式) 推奨。単語 1 個だけにするとアングルタグと組合せ検索されます",
    )

    st.markdown("##### プロバイダ")
    provider_helps = {
        "Danbooru": "アニメ/イラスト (英語タグ検索)",
        "Openverse": "CC ライセンスの一般画像 (写真含む)",
        "Wallhaven": "壁紙DB (一般/アニメ/人物)",
    }
    selected_providers: list[str] = []
    for pname in ALL_PROVIDERS:
        if st.checkbox(
            pname, value=True, key=f"provider_{pname}",
            help=provider_helps.get(pname, ""),
        ):
            selected_providers.append(pname)

    st.markdown("##### フィルタ")
    safe = st.toggle(
        "セーフサーチ",
        value=True,
        help="ONで年齢制限のある結果を除外（デフォルトON）",
    )
    if not safe:
        st.warning("⚠️ セーフサーチOFF: 年齢制限コンテンツが含まれる可能性があります")

    limit = st.slider(
        "取得件数/クエリ",
        min_value=5,
        max_value=50,
        value=20,
        help="プロバイダ × タグバリアント毎の件数。多いほど結果は増えますが検索が遅くなります",
    )

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
        with st.spinner("全アングル × 全プロバイダを並列検索中..."):
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
    total_angles = sum(len(a) for a in ANGLE_TAXONOMY.values())
    st.markdown(
        f"""
左のサイドバーで **キーワード** を入力して **検索** ボタンを押してください。

**{len(ANGLE_TAXONOMY)} カテゴリ / {total_angles} アングル** に分けて並列検索します。
サムネイルはブラウザが直接プロバイダから読み込むため、このサーバには保存されません。
各画像の **「元ページを開く」** から権利元サイトへ遷移できます。

#### 検索ソース
- **Danbooru** — アニメ/イラスト系タグ付き画像 (rating g/s のみ表示)
- **Openverse** — CC ライセンスの一般画像 (写真含む)
- **Wallhaven** — 壁紙DB (一般/アニメ/人物、sfw のみ)

#### 使い方のコツ
- Danbooru は英語タグ 1 つ(例: `1girl`) にするとアングルタグと組み合わせ検索されます
- 日本語も一部 (女の子, 立ち絵, 笑顔 ...) は自動で英語化されます
- 件数が少なければ「取得件数/クエリ」スライダを上げてみてください
        """
    )
else:
    trans_note = (
        f" (→ `{meta['translated']}`)"
        if meta["translated"] != meta["keyword"]
        else ""
    )
    total_hits = sum(len(v) for v in results.values())
    st.markdown(
        f"#### 🔎 `{meta['keyword']}`{trans_note}  "
        f"・ セーフサーチ: **{'ON' if meta['safe'] else 'OFF'}**  "
        f"・ ソース: {', '.join(meta['providers'])}  "
        f"・ 合計 **{total_hits}** 件"
    )

    category_tabs = st.tabs(list(ANGLE_TAXONOMY.keys()))
    for cat_tab, (category, angles) in zip(
        category_tabs, ANGLE_TAXONOMY.items()
    ):
        with cat_tab:
            angle_labels = [
                f"{name} ({len(results.get((category, name), []))})"
                for name in angles.keys()
            ]
            angle_tabs = st.tabs(angle_labels)
            for angle_tab, angle_name in zip(angle_tabs, angles.keys()):
                with angle_tab:
                    items = results.get((category, angle_name), [])
                    render_grid(items, cols=4)
