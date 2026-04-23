import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

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
        <div style='font-size: 0.9rem; font-weight: 800; color: #000000;'>更新：{last_updated}</div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 3. 準備渲染資料
# ==========================================
all_results = data_store['results']
name_map = data_store.get('name_map', {})

# 型態選單
type_options = {'全部': None, '漲後整理（型態A）': 'A', '多頭排列（型態B）': 'B'}
selected_label = st.selectbox('型態選擇', list(type_options.keys()), index=0)
selected_type = type_options[selected_label]

if selected_type:
    filtered = {k: v for k, v in all_results.items() if v.get('type') == selected_type}
else:
    filtered = all_results

symbol_list = sorted(list(filtered.keys()))

if not symbol_list:
    st.info("本次分析未發現符合條件的標的。")
    st.stop()

all_results = filtered

# ==========================================
# 4. 繪圖渲染（雙欄極致看板模式）
# ==========================================
for i, sym in enumerate(symbol_list):
    try:
        k_data = all_results[sym]
        plot_df = pd.DataFrame(k_data)

        if plot_df.empty:
            continue

        # 均線由前端即時計算（節省 JSON 容量）
        plot_df['MA10'] = plot_df['close'].rolling(window=10).mean()
        plot_df['MA20'] = plot_df['close'].rolling(window=20).mean()
        plot_df['MA60'] = plot_df['close'].rolling(window=60).mean()

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

        # 成交量（放量黃色鏈：首根 vol>=MA20*1.3，後續每根需>=前黃根*1.3）
        vol_ma20 = plot_df['volume'].rolling(window=20).mean()
        v_colors = []
        prev_yellow_vol = None
        for c, o, vol, ma20 in zip(plot_df['close'], plot_df['open'], plot_df['volume'], vol_ma20):
            if prev_yellow_vol is not None and vol >= prev_yellow_vol * 1.3:
                v_colors.append('#FFD700')
                prev_yellow_vol = vol
            elif pd.notna(ma20) and vol >= ma20 * 1.3:
                v_colors.append('#FFD700')
                prev_yellow_vol = vol
            else:
                v_colors.append('#ef5350' if c >= o else '#26a69a')
                prev_yellow_vol = None
        fig.add_trace(go.Bar(x=plot_df['date'], y=plot_df['volume'],
                             marker_color=v_colors, name='量'), row=2, col=1)

        fig.update_layout(
            height=350,
            margin=dict(l=5, r=40, t=50, b=20),
            xaxis_rangeslider_visible=False,
            template="plotly_white",
            paper_bgcolor='white',
            plot_bgcolor='white',
            title=dict(text=(
                f"<b>{sym.replace('.TW','').replace('.TWO','')} {name_map.get(sym,'')}"
                f" {'｜漲後整理' if k_data.get('type')=='A' else '｜多頭排列'}"
                f"{'  🔵外資' if k_data.get('inst_foreign') else ''}"
                f"{'  🟢投信' if k_data.get('inst_trust') else ''}"
                f"</b>"
            ), font=dict(color='black', size=22)),
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

        with cols[i % 2]:
            st.plotly_chart(
                fig,
                use_container_width=True,
                key=f"fig_{sym}",
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

st.write("---")
st.write("已經到底囉！")
