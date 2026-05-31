import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import html
from urllib.parse import quote, unquote

APP_VERSION = "1.5"

# ==========================================
# 頁面與底色初始化
# ==========================================
st.set_page_config(page_title="台股掃圖", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    [data-testid="stSidebar"] { display: none; }
    .block-container { padding-top: 2rem; padding-bottom: 0rem; }

    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #ffffff !important;
    }

    .stApp * {
        color: #000000 !important;
        font-family: "Arial", sans-serif !important;
    }

    [data-testid="stSidebar"] { display: none; }
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }

    .pagination-nav {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 14px;
        font-size: 1rem;
        line-height: 1.6;
        padding: 4px 0 10px;
    }
    .pagination-nav a {
        color: #000000 !important;
        text-decoration: none !important;
        padding: 0 2px;
    }
    .pagination-nav a:hover {
        text-decoration: underline !important;
    }
    .pagination-nav .current-page {
        font-weight: 900;
        text-decoration: underline;
    }
    .pagination-nav .disabled-page {
        opacity: 0.45;
    }
    .stock-title {
        position: relative;
        display: inline-block;
        font-weight: 900;
        cursor: help;
    }
    .stock-title .stock-tooltip {
        visibility: hidden;
        opacity: 0;
        position: absolute;
        z-index: 20;
        left: 0;
        top: 1.8rem;
        width: max-content;
        max-width: 320px;
        padding: 8px 10px;
        border: 1px solid #d9d9d9;
        border-radius: 4px;
        background: #ffffff;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.14);
        font-size: 0.85rem;
        font-weight: 400;
        line-height: 1.5;
        white-space: normal;
    }
    .stock-title:hover .stock-tooltip {
        visibility: visible;
        opacity: 1;
    }
    .theme-board {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 18px;
        margin: 10px 0 14px;
    }
    .theme-panel-title {
        font-size: 0.95rem;
        font-weight: 900;
        margin: 0 0 7px;
    }
    .theme-block-grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 8px;
    }
    .theme-block {
        display: block;
        min-height: 70px;
        padding: 8px 9px;
        border: 1px solid #d9d9d9;
        border-radius: 6px;
        background: #ffffff;
        text-decoration: none !important;
    }
    .theme-block:hover {
        border-color: #000000;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
    }
    .theme-block.active {
        border: 2px solid #000000;
    }
    .theme-block-name {
        display: block;
        font-size: 0.85rem;
        font-weight: 900;
        line-height: 1.25;
        margin-bottom: 5px;
        word-break: break-word;
    }
    .theme-block-meta {
        display: block;
        font-size: 0.75rem;
        line-height: 1.35;
    }
    .theme-strong .theme-block-meta strong {
        color: #E32636 !important;
    }
    .theme-weak .theme-block-meta strong {
        color: #008F39 !important;
    }
    .theme-selected-bar {
        font-size: 0.9rem;
        font-weight: 800;
        margin: 8px 0 12px;
    }
    .theme-selected-bar a {
        color: #000000 !important;
        text-decoration: underline !important;
    }
    .download-actions {
        display: flex;
        align-items: center;
        gap: 0;
        padding-top: 0;
    }
    .download-link {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 38px;
        padding: 0 14px;
        border: 1px solid #d0d0d0;
        border-radius: 6px;
        background: #ffffff;
        color: #000000 !important;
        font-size: 0.92rem;
        font-weight: 600;
        line-height: 1;
        text-decoration: none !important;
        white-space: nowrap;
    }
    .download-link + .download-link {
        margin-left: 0;
    }
    .download-link:hover {
        border-color: #000000;
        background: #f7f7f7;
    }
    @media (max-width: 900px) {
        .theme-board { grid-template-columns: 1fr; }
        .theme-block-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .download-actions { flex-wrap: wrap; }
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 1. 載入 JSON 資料
# ==========================================
def load_analysis_results():
    try:
        with open('uptrend_results.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def load_stock_notes():
    try:
        with open('stock_notes.json', 'r', encoding='utf-8') as f:
            notes = json.load(f)
            return notes if isinstance(notes, dict) else {}
    except FileNotFoundError:
        return {}

def load_stock_concepts_data():
    try:
        with open('stock_concepts.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}

    return data if isinstance(data, dict) else {}

def load_stock_concepts():
    data = load_stock_concepts_data()
    concepts = data.get('stock_concepts', data) if isinstance(data, dict) else {}
    return concepts if isinstance(concepts, dict) else {}

def load_market_themes():
    data = load_stock_concepts_data()
    themes = data.get('market_theme_rankings', []) if isinstance(data, dict) else []
    return themes if isinstance(themes, list) else []

data_store = load_analysis_results()

if not data_store or 'results' not in data_store:
    st.error("找不到分析數據或格式錯誤，請先執行 update_data.py")
    st.stop()

# ==========================================
# 2. 標題與更新時間
# ==========================================
last_updated = data_store.get('last_updated', '未知')

st.markdown(f"""
    <div style='display: flex; justify-content: space-between; align-items: baseline;
                border-bottom: 2px solid #000000; padding-top: 25px; padding-bottom: 5px; margin-bottom: 10px;'>
        <div style='font-size: 2.2rem; font-weight: 900; color: #000000; line-height: 1.2;'>台股掃圖</div>
        <div style='font-size: 0.9rem; font-weight: 800; color: #000000;'>版本：{APP_VERSION} ｜ 更新：{last_updated}</div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 3. 準備渲染資料
# ==========================================
all_results = data_store['results']
name_map = data_store.get('name_map', {})
sector_map = data_store.get('sector_map', {})
business_map = data_store.get('business_map', {})
stock_notes = load_stock_notes()
stock_concepts = load_stock_concepts()
market_themes = load_market_themes()

def get_stock_note(symbol, code, sector):
    note = (
        stock_notes.get(symbol)
        or stock_notes.get(code)
        or business_map.get(symbol)
        or business_map.get(code)
    )
    if note:
        return str(note)
    if stock_concepts.get(symbol) or stock_concepts.get(code):
        return ''
    if sector:
        return f"產業別：{sector}"
    return ""

def get_stock_concepts(symbol, code):
    concepts = stock_concepts.get(symbol) or stock_concepts.get(code) or []
    if isinstance(concepts, str):
        concepts = [concepts]
    return [str(item).strip() for item in concepts if str(item).strip()]

def normalize_code(symbol):
    return str(symbol).upper().replace('.TWO', '').replace('.TW', '')

def get_selected_theme_slug():
    try:
        raw_theme = st.query_params.get('theme')
    except AttributeError:
        raw_theme = st.experimental_get_query_params().get('theme')

    if isinstance(raw_theme, list):
        raw_theme = raw_theme[0] if raw_theme else ''
    return unquote(raw_theme or '')

def build_theme_blocks(base_symbols):
    base_codes = {normalize_code(sym) for sym in base_symbols}

    items = []
    for item in market_themes:
        stock_ids = {
            normalize_code(stock_id)
            for stock_id in item.get("stock_ids", [])
            if str(stock_id).strip()
        }
        matched_count = len(base_codes & stock_ids) if stock_ids else 0
        items.append({
            **item,
            "count": matched_count,
        })

    items = [item for item in items if item["count"] > 0]

    strong = sorted(
        items,
        key=lambda item: (item["strength"], item["market_count"], item["name"]),
        reverse=True,
    )[:5]
    weak = sorted(
        items,
        key=lambda item: (item["strength"], -item["market_count"], item["name"]),
    )[:5]
    return strong, weak

def theme_matches_symbol(theme_item, symbol):
    return normalize_code(symbol) in set(theme_item.get("stock_ids") or [])

def get_selected_theme_item(strong_themes, weak_themes):
    selected_theme_slug = get_selected_theme_slug()
    if not selected_theme_slug:
        return None
    for item in strong_themes + weak_themes:
        if item.get("slug") == selected_theme_slug:
            return item
    for item in market_themes:
        if item.get("slug") == selected_theme_slug:
            return item
    return None

def get_selected_query_text():
    return ','.join(sorted(st.session_state.get('selected', set())))

def get_query_value(key, default=''):
    try:
        raw_value = st.query_params.get(key)
    except AttributeError:
        raw_value = st.experimental_get_query_params().get(key)

    if isinstance(raw_value, list):
        raw_value = raw_value[0] if raw_value else default
    return raw_value or default

def build_page_href(page_number, theme_slug=None, include_theme=True):
    params = [f'page={page_number}']
    active_theme = get_selected_theme_slug() if theme_slug is None else theme_slug
    if include_theme and active_theme:
        params.append(f'theme={quote(active_theme)}')
    if selected_type:
        params.append(f'type={quote(selected_type)}')
    if selected_sector != '全部產業':
        params.append(f'sector={quote(selected_sector)}')
    selected_text = get_selected_query_text()
    if selected_text:
        params.append(f'selected={quote(selected_text)}')
    return '?' + '&'.join(params)

def render_theme_blocks(title, items, css_class):
    selected_theme_slug = get_selected_theme_slug()
    blocks = []
    for item in items:
        active_class = ' active' if item['slug'] == selected_theme_slug else ''
        href = build_page_href(1, theme_slug=item['slug'])
        blocks.append(
            f'<a class="theme-block {css_class}{active_class}" href="{href}" target="_self">'
            f'<span class="theme-block-name">{html.escape(item["name"])}</span>'
            f'<span class="theme-block-meta"><strong>{item["strength"]:+.2f}%</strong><br>篩出 {item["count"]} 檔</span>'
            '</a>'
        )
    st.markdown(
        f'<div><div class="theme-panel-title">{html.escape(title)}</div>'
        f'<div class="theme-block-grid">{"".join(blocks)}</div></div>',
        unsafe_allow_html=True,
    )

# 先初始化收藏，讓主題/分頁連結能保留 selected query param
if 'selected' not in st.session_state:
    try:
        raw_selected = st.query_params.get('selected')
    except AttributeError:
        raw_selected = st.experimental_get_query_params().get('selected')
    if isinstance(raw_selected, list):
        raw_selected = raw_selected[0] if raw_selected else ''
    st.session_state.selected = {
        item.strip().upper()
        for item in str(raw_selected or '').split(',')
        if item.strip()
    }

# 篩選列
filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    type_options = {'全部': None, '漲後整理（型態A）': 'A', '多頭排列（型態B）': 'B', '回撤反彈（例外C）': 'C'}
    query_type = get_query_value('type')
    type_values = list(type_options.values())
    type_labels = list(type_options.keys())
    type_index = type_values.index(query_type) if query_type in type_values else 0
    selected_label = st.selectbox('型態選擇', type_labels, index=type_index)
    selected_type = type_options[selected_label]

with filter_col2:
    all_sectors = sorted({v for v in sector_map.values() if v})
    sector_options = ['全部產業'] + all_sectors
    query_sector = get_query_value('sector')
    sector_index = sector_options.index(query_sector) if query_sector in sector_options else 0
    selected_sector = st.selectbox('產業類別', sector_options, index=sector_index)

if selected_type:
    filtered = {k: v for k, v in all_results.items() if v.get('type') == selected_type}
else:
    filtered = all_results

if selected_sector != '全部產業':
    filtered = {k: v for k, v in filtered.items() if v.get('sector') == selected_sector}

base_filtered = filtered
strong_themes, weak_themes = build_theme_blocks(base_filtered.keys())
if strong_themes or weak_themes:
    strong_col, weak_col = st.columns(2)
    with strong_col:
        render_theme_blocks('今日領漲族群', strong_themes, 'theme-strong')
    with weak_col:
        render_theme_blocks('今日領跌族群', weak_themes, 'theme-weak')

selected_theme_item = get_selected_theme_item(strong_themes, weak_themes)
if selected_theme_item:
    clear_href = build_page_href(1, include_theme=False)
    st.markdown(
        f'<div class="theme-selected-bar">目前主題：{html.escape(selected_theme_item["name"])}'
        f' ｜ <a href="{clear_href}" target="_self">清除主題</a></div>',
        unsafe_allow_html=True,
    )
    filtered = {
        k: v for k, v in base_filtered.items()
        if theme_matches_symbol(selected_theme_item, k)
    }

symbol_list = sorted(list(filtered.keys()))

if not symbol_list:
    st.info("本次分析未發現符合條件的標的。")
    st.stop()

all_results = filtered

# ==========================================
# 4. 收藏狀態初始化
# ==========================================
if 'selected' not in st.session_state:
    st.session_state.selected = set()

def sync_selected_to_query():
    selected_text = get_selected_query_text()
    try:
        if selected_text:
            st.query_params['selected'] = selected_text
        elif 'selected' in st.query_params:
            del st.query_params['selected']
    except AttributeError:
        params = st.experimental_get_query_params()
        if selected_text:
            params['selected'] = selected_text
        else:
            params.pop('selected', None)
        theme_slug = get_selected_theme_slug()
        if theme_slug:
            params['theme'] = theme_slug
        if selected_type:
            params['type'] = selected_type
        else:
            params.pop('type', None)
        if selected_sector != '全部產業':
            params['sector'] = selected_sector
        else:
            params.pop('sector', None)
        st.experimental_set_query_params(**params)

def sync_selected_from_checkboxes():
    selected = set(st.session_state.selected)
    prefix = 'chk_'
    for key, checked in st.session_state.items():
        if not key.startswith(prefix):
            continue
        sym = key[len(prefix):]
        if checked:
            selected.add(sym)
        else:
            selected.discard(sym)
    st.session_state.selected = selected
    sync_selected_to_query()

def toggle_selected(sym):
    if st.session_state.get(f'chk_{sym}', False):
        st.session_state.selected.add(sym)
    else:
        st.session_state.selected.discard(sym)
    sync_selected_to_query()

# ==========================================
# 5. 分頁設定
# ==========================================
PAGE_SIZE = 40
total = len(symbol_list)
total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

def get_query_page():
    try:
        raw_page = st.query_params.get('page')
    except AttributeError:
        raw_page = st.experimental_get_query_params().get('page')

    if isinstance(raw_page, list):
        raw_page = raw_page[0] if raw_page else None

    try:
        return int(raw_page)
    except (TypeError, ValueError):
        return None

def set_query_page(page_number):
    try:
        st.query_params['page'] = str(page_number)
        selected_text = get_selected_query_text()
        if selected_text:
            st.query_params['selected'] = selected_text
        elif 'selected' in st.query_params:
            del st.query_params['selected']
        theme_slug = get_selected_theme_slug()
        if theme_slug:
            st.query_params['theme'] = theme_slug
        if selected_type:
            st.query_params['type'] = selected_type
        elif 'type' in st.query_params:
            del st.query_params['type']
        if selected_sector != '全部產業':
            st.query_params['sector'] = selected_sector
        elif 'sector' in st.query_params:
            del st.query_params['sector']
    except AttributeError:
        params = {'page': page_number}
        selected_text = get_selected_query_text()
        if selected_text:
            params['selected'] = selected_text
        theme_slug = get_selected_theme_slug()
        if theme_slug:
            params['theme'] = theme_slug
        if selected_type:
            params['type'] = selected_type
        if selected_sector != '全部產業':
            params['sector'] = selected_sector
        st.experimental_set_query_params(**params)

if 'current_page' not in st.session_state:
    st.session_state.current_page = 1

query_page = get_query_page()
if query_page is not None:
    st.session_state.current_page = query_page

st.session_state.current_page = max(1, min(st.session_state.current_page, total_pages))

col_info, col_page = st.columns([3, 1])
with col_page:
    page = st.selectbox('頁碼', list(range(1, total_pages + 1)),
                        index=st.session_state.current_page - 1,
                        label_visibility='collapsed')
    st.session_state.current_page = page
    if page != query_page:
        set_query_page(page)
with col_info:
    st.markdown(f"<div style='font-size:0.9rem; color:#000; padding-top:6px;'>共 {total} 檔，第 {page}/{total_pages} 頁</div>", unsafe_allow_html=True)

start = (page - 1) * PAGE_SIZE
page_symbols = symbol_list[start:start + PAGE_SIZE]
sync_selected_from_checkboxes()

def get_export_industry(symbol):
    stock_data = data_store.get('results', {}).get(symbol, {})
    industry = (
        sector_map.get(symbol)
        or stock_data.get('sector')
        or '未分類'
    )
    return str(industry).strip() or '未分類'

def to_tradingview_symbol(symbol):
    code = normalize_code(symbol)
    return ('TWSE:' if str(symbol).upper().endswith('.TW') else 'TPEX:') + code

def build_export_groups(selected_symbols):
    groups = {}
    for sym in sorted({str(item).upper() for item in selected_symbols}):
        industry_label = get_export_industry(sym)
        groups.setdefault(industry_label, []).append(sym)
    return [(industry_label, groups[industry_label]) for industry_label in sorted(groups)]

def build_tradingview_watchlist(selected_symbols):
    lines = []
    for industry_label, symbols in build_export_groups(selected_symbols):
        lines.append(f'###{industry_label},')
        lines.append(','.join(to_tradingview_symbol(sym) for sym in symbols) + ',')
        lines.append('')
    return '\n'.join(lines).strip() + '\n'

def build_xq_csv(selected_symbols):
    lines = []
    for industry_label, symbols in build_export_groups(selected_symbols):
        lines.append(industry_label)
        lines.extend(f'{normalize_code(sym)}.TW' for sym in symbols)
    return '\r\n'.join(lines) + ('\r\n' if lines else '')

@st.fragment
def render_download_buttons(selected_symbols, count):
    tv_col, xq_col = st.columns([1.45, 1.05], gap=None)
    with tv_col:
        st.download_button(
            f'⬇ TradingView清單（{count} 檔）',
            data=('\ufeff' + build_tradingview_watchlist(selected_symbols)).encode('utf-8'),
            file_name='watchlist.txt',
            mime='text/plain; charset=utf-8',
            key='download_tradingview_watchlist',
            on_click='ignore',
            use_container_width=True,
        )
    with xq_col:
        st.download_button(
            f'⬇ XQ清單（{count} 檔）',
            data=build_xq_csv(selected_symbols).encode('big5', errors='replace'),
            file_name='xq_watchlist.csv',
            mime='text/csv; charset=big5',
            key='download_xq_watchlist',
            on_click='ignore',
            use_container_width=True,
        )

# 收藏下載列
sel_count = len(st.session_state.selected)
dl_col, clr_col, _ = st.columns([2.55, 0.9, 5.55], gap=None)
with dl_col:
    if sel_count > 0:
        render_download_buttons(st.session_state.selected, sel_count)
    else:
        st.markdown("<div style='padding-top:8px; font-size:0.85rem; color:#888;'>尚未勾選任何標的</div>", unsafe_allow_html=True)
with clr_col:
    if sel_count > 0 and st.button('清除全部'):
        st.session_state.selected = set()
        for key in list(st.session_state.keys()):
            if key.startswith('chk_'):
                st.session_state[key] = False
        sync_selected_to_query()
        st.rerun()

# ==========================================
# 6. 繪圖渲染（雙欄極致看板模式）
# ==========================================
for i, sym in enumerate(page_symbols):
    try:
        k_data = all_results[sym]
        plot_df = pd.DataFrame(k_data)

        if plot_df.empty:
            continue

        # 均線由後端預計算，直接使用
        plot_df['MA10'] = plot_df.get('ma10')
        plot_df['MA20'] = plot_df.get('ma20')
        plot_df['MA60'] = plot_df.get('ma60')

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            row_heights=[0.8, 0.2], vertical_spacing=0.03)

        # K線
        fig.add_trace(go.Candlestick(
            x=plot_df['date'], open=plot_df['open'], high=plot_df['high'],
            low=plot_df['low'], close=plot_df['close'],
            increasing_line_color='#E32636', decreasing_line_color='#008F39',
            increasing_fillcolor='#E32636', decreasing_fillcolor='#008F39',
            increasing_line_width=0.7, decreasing_line_width=0.7,
            name='K線'
        ), row=1, col=1)

        # 均線
        fig.add_trace(go.Scatter(x=plot_df['date'], y=plot_df['MA10'],
                                 line=dict(color='#f6c23e', width=1), name='10MA'), row=1, col=1)
        fig.add_trace(go.Scatter(x=plot_df['date'], y=plot_df['MA20'],
                                 line=dict(color='#8e44ad', width=1), name='20MA'), row=1, col=1)
        fig.add_trace(go.Scatter(x=plot_df['date'], y=plot_df['MA60'],
                                 line=dict(color='#36b9cc', width=1), name='60MA'), row=1, col=1)

        # 成交量
        v_colors = ['#ef5350' if c >= o else '#26a69a'
                    for c, o in zip(plot_df['close'], plot_df['open'])]
        fig.add_trace(go.Bar(x=plot_df['date'], y=plot_df['volume'],
                             marker_color=v_colors, name='量'), row=2, col=1)

        fig.update_layout(
            height=350,
            margin=dict(l=5, r=40, t=8, b=20),
            xaxis_rangeslider_visible=False,
            template="plotly_white",
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(color='black'),
            showlegend=False,
            dragmode=False,
            hovermode=False
        )

        fig.update_xaxes(type='category', nticks=10, showgrid=False, zeroline=False,
                         fixedrange=True, tickfont=dict(color='black', size=12), row=1, col=1)
        fig.update_xaxes(type='category', nticks=10, showgrid=False, zeroline=False,
                         fixedrange=True, tickfont=dict(color='black', size=11), row=2, col=1)
        fig.update_yaxes(showgrid=False, zeroline=False, fixedrange=True,
                         tickfont=dict(color='black', size=12), side='right', row=1, col=1)
        fig.update_yaxes(showgrid=False, zeroline=False, fixedrange=True,
                         showticklabels=False, row=2, col=1)

        if i % 2 == 0:
            cols = st.columns(2)

        code = sym.replace('.TWO', '').replace('.TW', '')
        sector = k_data.get('sector', '')
        stock_name = name_map.get(sym, '').rstrip('*')
        stock_note = get_stock_note(sym, code, sector)
        concepts = get_stock_concepts(sym, code)
        tooltip_lines = []
        if stock_note:
            tooltip_lines.append(stock_note)
        if concepts:
            tooltip_lines.append(f"市場主題：{'、'.join(concepts)}")
        if sector and not any(line.startswith('產業別：') for line in tooltip_lines):
            tooltip_lines.append(f"產業別：{sector}")
        stock_note_html = html.escape('\n'.join(tooltip_lines) or '暫無市場主題').replace('\n', '<br>')
        type_text = {
            'A': '漲後整理',
            'B': '多頭排列',
            'C': '回撤反彈'
        }.get(k_data.get('type'), '多頭排列')
        title_text = (
            f"{code} {stock_name}"
            f" ｜{type_text}"
            f"{f'  [{sector}]' if sector else ''}"
            f"{'  🔵外資' if k_data.get('inst_foreign') else ''}"
            f"{'  🟢投信' if k_data.get('inst_trust') else ''}"
            f"{'  VOL🔺' if k_data.get('vol_surge') else ''}"
        )
        title_html = (
            '<span class="stock-title">'
            f'{html.escape(title_text)}'
            f'<span class="stock-tooltip">{stock_note_html}</span>'
            '</span>'
        )

        with cols[i % 2]:
            chk_col, title_col = st.columns([0.05, 0.95])
            with chk_col:
                checked = st.checkbox('', value=sym in st.session_state.selected,
                                      key=f"chk_{sym}", label_visibility='collapsed',
                                      on_change=toggle_selected, args=(sym,))
            with title_col:
                st.markdown(title_html, unsafe_allow_html=True)

            st.plotly_chart(
                fig,
                use_container_width=True,
                key=f"fig_{page}_{sym}",
                theme=None,
                config={
                    'toImageButtonOptions': {
                        'format': 'png',
                        'filename': f'{sym}_Analysis',
                        'scale': 2
                    },
                    'staticPlot': True,
                    'displayModeBar': False
                }
            )
            st.markdown("<br>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"渲染 {sym} 時發生錯誤: {e}")
        continue

st.markdown("---")

# 底部分頁導覽
def get_page_range(current, total):
    if total <= 9:
        return list(range(1, total + 1))
    pages = set([1, total])
    for p in range(max(1, current - 2), min(total, current + 2) + 1):
        pages.add(p)
    result, prev = [], None
    for p in sorted(pages):
        if prev and p - prev > 1:
            result.append('...')
        result.append(p)
        prev = p
    return result

page_range = get_page_range(page, total_pages)

# 底部右對齊導覽：純文字連結，target=_self 保持在同一個視窗切換
nav_items = []
if page > 1:
    nav_items.append(f'<a href="{build_page_href(page - 1)}" target="_self">◀ 前一頁</a>')
else:
    nav_items.append('<span class="disabled-page">◀ 前一頁</span>')

for p in page_range:
    if p == '...':
        nav_items.append('<span>…</span>')
    elif p == page:
        nav_items.append(f'<span class="current-page">{p}</span>')
    else:
        nav_items.append(f'<a href="{build_page_href(p)}" target="_self">{p}</a>')

if page < total_pages:
    nav_items.append(f'<a href="{build_page_href(page + 1)}" target="_self">下一頁 ▶</a>')
else:
    nav_items.append('<span class="disabled-page">下一頁 ▶</span>')

st.markdown(
    f'<nav class="pagination-nav">{"".join(nav_items)}</nav>',
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)
