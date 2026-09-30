"""
Taiwan Alpha Radar V8.3 Return-First Research App (Operations & Watchlist Enhanced).
Five mobile views. Return-First EV, Tail Risk ES10, Strict Price Gating, On-Demand Fallback.
Run: streamlit run app.py
"""
from __future__ import annotations

from pathlib import Path
import html
import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

import radar_service as service
from market_data import DailyPriceStore, _taipei_timestamp
from trading_calendar import calendar_reference, daily_freshness, entry_review_allowed, save_closure_notice
from input_validation import publish_inputs
from presentation import plain_summary
from policy_engine import ENGINE_VERSION, HORIZONS
from return_first_model import finite_scalar

ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("ALPHA_RADAR_DATA_DIR", str(ROOT / "data")))
VIEW_LABELS = ["⭐ 極選", "⚡ 短線", "📈 中線", "🧭 長波段", "🔎 個股"]
HORIZON_LABELS = {"short": "短線 · 10交易日", "mid": "中線 · 40交易日", "long": "長波段 · 120交易日"}
FAMILY_LABELS = {
    "價量研究｜無財報／法人代理": "price_only",
    "基本面確認｜需要歷史公告資料": "business_confirmed",
    "法人確認｜需要歷史籌碼資料": "flow_confirmed",
    "完整證據｜基本面＋法人": "full",
}
SETUP_LABELS = {
    "BREAKOUT": "平台突破", "PULLBACK": "趨勢回測", "RECLAIM": "重新站回",
    "TREND": "趨勢延續觀察", "BASE": "整理觀察", "DRYUP": "低量新低觀察",
}
STATE_LABELS = {
    "CONDITIONS_MET_NOT_FILLED": "收盤條件符合，次日開盤再確認",
    "WAIT_ENTRY_ZONE": "等待回到布局區",
    "WAIT_BREAKOUT": "等待突破確認",
    "WAIT_CONFIRMATION": "量價確認尚未成立",
    "DO_NOT_CHASE": "超出追價上限，等待新機會",
    "INVALIDATED": "原結構已失效",
    "DATA_UNVERIFIED": "資料待核對",
    "PLAN_EXPIRED_REBUILD_NOT_REANCHOR": "計畫已過期，需重新評估",
    "QUOTE_BEFORE_PLAN": "報價早於計畫",
    "NO_RETURN_ESTIMATE": "沒有可用的報酬估計",
    "LIQUIDITY_GATE": "目前流動性／歷史資料不符合交易條件",
}

CSS = """
<style>
:root{--ink:#17243b;--muted:#66748b;--line:#e5eaf2;--blue:#1d4ed8;}
.stApp{background:#f5f7fb;color:var(--ink)}
.block-container{max-width:1020px;padding-top:1.1rem;padding-bottom:4rem;}
.hero{padding:24px;border-radius:24px;background:linear-gradient(125deg,#102139,#173c70 65%,#126975);color:white;margin-bottom:18px;}
.hero .eyebrow{letter-spacing:.12em;font-size:.75rem;opacity:.8}
.hero h1{font-size:1.9rem;line-height:1.25;color:white;margin:.35rem 0;}
.hero p{font-size:1rem;opacity:.85;margin:.45rem 0 0;line-height:1.6}
.topnote{padding:14px 17px;border:1px solid #d7e1f3;background:#eef4ff;border-radius:14px;margin:12px 0;color:#334a70;font-size:.94rem;line-height:1.7}
.statusline{font-size:.89rem;color:#556580;line-height:1.65;margin:8px 0 14px}
.card{background:white;border:1px solid var(--line);border-radius:21px;padding:22px;margin:14px 0 10px;box-shadow:0 6px 24px rgba(19,42,80,.04)}
.card-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;}
.card-title{font-size:1.3rem;font-weight:850;line-height:1.4}
.card-code{font-size:.83rem;color:var(--muted);margin-top:4px}
.card-price{font-size:1.22rem;font-weight:800;text-align:right;white-space:nowrap}
.badge{display:inline-block;font-size:.78rem;font-weight:700;padding:5px 9px;border-radius:8px;background:#f0f3f8;color:#52617a;margin:10px 5px 7px 0}
.badge-blue{color:#234aaa;background:#eaf0ff}
.badge-amber{color:#b45309;background:#fef3c7}
.return-box{background:#f6f9ff;border:1px solid #e4ebf9;border-radius:15px;padding:15px;margin:12px 0;}
.return-k{font-size:.9rem;color:#4c5c75}.return-v{font-size:2.15rem;font-weight:900;letter-spacing:-.04em;line-height:1.4;color:#1e46a3;}
.return-desc{font-size:.82rem;color:#708098;line-height:1.5}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin:12px 0;}
.stat{border:1px solid #edf0f6;background:#fcfdff;padding:12px 10px;border-radius:12px;}
.stat .k{font-size:.77rem;color:#6a7890;line-height:1.4}.stat .v{font-size:1.1rem;font-weight:800;margin-top:5px;}
.decision{padding:13px 15px;border-radius:12px;background:#fff5df;border:1px solid #f4dfb1;color:#88621a;font-weight:750;font-size:.99rem;line-height:1.6}
.decision-ok{background:#eaf6f0;border-color:#d1e9dd;color:#225e44}
.levels{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;}
.level{background:#f8fafc;border:1px solid #edf0f5;border-radius:11px;padding:10px}
.level .k{font-size:.8rem;color:#62718a}.level .v{font-weight:800;font-size:1rem;margin-top:5px;}
.subnote{font-size:.85rem;color:#758198;line-height:1.65;margin:10px 0}
@media(max-width:650px){
 .block-container{padding:.8rem .8rem 3rem;}.hero{padding:19px 17px;border-radius:19px}.hero h1{font-size:1.5rem}.hero p{font-size:.9rem}
 .card{padding:17px 14px;border-radius:17px}.card-title{font-size:1.15rem}.card-price{font-size:1.13rem}.return-v{font-size:1.92rem}
 .stats{grid-template-columns:repeat(2,1fr)}.levels{grid-template-columns:repeat(2,1fr)}
 .stat .v{font-size:1.12rem}
}
</style>
"""

def esc(value): return html.escape(str(value))

def percent(value, signed=True):
    v = finite_scalar(value)
    return "—" if not np.isfinite(v) else f"{v*100:{'+' if signed else ''}.2f}%"

def money(value):
    v = finite_scalar(value)
    return "—" if not np.isfinite(v) else f"{v:,.2f}".rstrip("0").rstrip(".")

def calc_confidence_metric(f: dict, evidence: dict) -> tuple[str, float, str]:
    if not isinstance(f, dict): f = {}
    if not isinstance(evidence, dict): evidence = {}
    
    local_n = float(f.get("local_effective_n", 0.0))
    blocks = int(f.get("local_time_blocks", 0))
    shrinkage = float(f.get("local_weight", 0.5))
    bus_req = max(1, int(evidence.get("business_required", 4)))
    bus_has = int(evidence.get("business_fields", 0))
    data_ratio = min(1.0, bus_has / bus_req)
    
    sample_score = min(1.0, local_n / 25.0) * 0.45 + min(1.0, blocks / 5.0) * 0.25
    conf_score = (sample_score + shrinkage * 0.15 + data_ratio * 0.15) * 100.0
    
    if conf_score >= 75 and local_n >= 15:
        grade = "高可信度"
    elif conf_score >= 50 and local_n >= 8:
        grade = "中等可信度"
    else:
        grade = "參考性偏低"
    
    desc = f"{grade} ({conf_score:.0f}%)｜有效樣本 N={local_n:.1f} · {blocks}個獨立時段 · 數據完整度 {data_ratio*100:.0f}%"
    return grade, conf_score, desc

def render_chart(chart, plan, key):
    if not chart or "ohlcv" not in chart:
        st.caption("這檔 K 線未常駐記憶體；個股診斷會嘗試讀取同日期快取。")
        return
    d = pd.DataFrame(chart["ohlcv"], columns=["Open", "High", "Low", "Close", "Volume"])
    dates = chart.get("dates", [])
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=.045, row_heights=[.74, .26])
    fig.add_trace(go.Candlestick(x=dates, open=d.Open, high=d.High, low=d.Low, close=d.Close,
                                increasing_line_color="#d85053", decreasing_line_color="#22917e",
                                name="原始價格"), row=1, col=1)
    fig.add_trace(go.Bar(x=dates, y=d.Volume, name="成交量",
                        marker_color=np.where(d.Close >= d.Open, "#d85053", "#22917e")), row=2, col=1)
    if plan:
        fig.add_hrect(y0=plan.get("zone_low", 0), y1=plan.get("zone_high", 0), line_width=0,
                      fillcolor="rgba(43,102,210,.10)", row=1, col=1)
        fig.add_hline(y=plan.get("trigger", 0), line_color="#ca902b", line_dash="dot", row=1, col=1)
        fig.add_hline(y=plan.get("invalidation", 0), line_color="#ba5360", line_dash="dash", row=1, col=1)
    fig.update_layout(height=410, margin=dict(l=7, r=8, t=10, b=8), showlegend=False,
                      xaxis_rangeslider_visible=False, template="plotly_white", dragmode=False)
    fig.update_xaxes(type="category", nticks=5, fixedrange=True, showgrid=False)
    fig.update_yaxes(fixedrange=True, gridcolor="#e9edf4")
    st.plotly_chart(fig, use_container_width=True, key=key,
                    config={"displayModeBar": False, "displaylogo": False, "scrollZoom": False})

def card(obj, h, snap, view, chart=None, calendar=None, is_watchlist=False):
    if not isinstance(obj, dict): return
    block = obj.get("horizons", {}).get(h, {})
    f = block.get("forecast") or {}
    plan = block.get("plan")
    q = block.get("qualification") or {}
    summary = f.get("strategy") or {}
    asset = f.get("asset_potential") or {}
    enough = bool(f.get("estimate_available") and f.get("sample_supported"))
    qualified = bool(q.get("research_qualified"))
    condition = block.get("entry_state", "NO_RETURN_ESTIMATE")
    state_label = STATE_LABELS.get(condition, condition)
    
    calendar = calendar or calendar_reference(DATA_DIR, now=_taipei_timestamp())
    fresh = daily_freshness(obj.get("price_date", ""), calendar)
    review_ok = entry_review_allowed(obj.get("price_date", ""), plan, calendar)
    
    if is_watchlist:
        headline = f"🔍 潛力觀察標的｜未通過硬性門檻（{state_label}）"
    elif not enough:
        headline = "報酬證據不足，僅供觀察"
    elif not qualified:
        headline = "未通過研究篩選｜" + state_label
    else:
        headline = state_label

    if not fresh.get("current_daily", False):
        headline = "不是最近完成日線，請更新後再評估"
    
    evidence = obj.get("evidence", {})
    ev = percent(summary.get("mean")) if summary.get("mean") is not None else percent(asset.get("mean"))
    summary_sentence = plain_summary(f)
    status_badge = "合格研究候選" if qualified else "潛力觀察標的"
    setup = SETUP_LABELS.get(obj.get("setup"), obj.get("setup", ""))
    
    grade_str, conf_score, conf_desc = calc_confidence_metric(f, evidence)

    st.markdown(f"""
<div class="card">
 <div class="card-head"><div><div class="card-title">{esc(obj.get('name', obj.get('ticker', '')))}</div>
 <div class="card-code">{esc(obj.get('ticker', ''))} · {esc(obj.get('industry',''))}</div></div>
 <div class="card-price">{money(obj.get('price', 0))}<div class="card-code">{esc(obj.get('price_date', ''))} 日線</div></div></div>
 <span class="badge badge-blue">{esc(HORIZON_LABELS.get(h, h))}</span><span class="badge">{esc(setup)}</span>
 <span class="badge {'badge-blue' if qualified else 'badge-amber'}">{esc(status_badge)}</span>
 <div class="topnote"><b>模型解讀：</b>{esc(summary_sentence)}</div>
 <div class="return-box">
   <div class="return-k">策略推估淨報酬 (EV) / 資產潛力</div>
   <div class="return-v">{ev}</div>
   <div class="return-desc">可信度評等：<b>{grade_str}</b>（{conf_desc}）。已扣除設定成本。</div>
 </div>
 <div class="stats">
  <div class="stat"><div class="k">同期超額 Alpha</div><div class="v">{percent(f.get('alpha_mean'))}</div></div>
  <div class="stat"><div class="k">中間情境 (P50)</div><div class="v">{percent(summary.get('median'))}</div></div>
  <div class="stat"><div class="k">偏佳情境 (P75)</div><div class="v">{percent(summary.get('p75'))}</div></div>
  <div class="stat"><div class="k">最差10%極端損失</div><div class="v">{percent(summary.get('expected_shortfall10_loss'), False)}</div></div>
 </div>
 <div class="decision {'decision-ok' if qualified and review_ok and condition=='CONDITIONS_MET_NOT_FILLED' else ''}">{esc(headline)}</div>
</div>""", unsafe_allow_html=True)
    
    with st.expander("🔍 進出場計畫、收益分布細節與 K 線", expanded=False):
        if plan:
            mode = "等待布局區＋轉強確認" if plan.get("entry_mode") == "zone_confirmed" else "突破確認後進場"
            st.markdown(f"""<div class="levels">
<div class="level"><div class="k">布局區</div><div class="v">{money(plan.get('zone_low'))}–{money(plan.get('zone_high'))}</div></div>
<div class="level"><div class="k">確認價</div><div class="v">{money(plan.get('trigger'))}</div></div>
<div class="level"><div class="k">不追價上限</div><div class="v">{money(plan.get('chase_limit'))}</div></div>
<div class="level"><div class="k">原始結構失效</div><div class="v">{money(plan.get('invalidation'))}</div></div>
</div><div class="subnote">固定路徑：{esc(mode)}。僅次日開盤嘗試一次；日線無法確認盤中實際成交細節。</div>""", unsafe_allow_html=True)
        
        snap_id = snap.get("snapshot_id", "default") if isinstance(snap, dict) else "default"
        chart = chart or (snap.get("charts", {}).get(obj.get("ticker")) if isinstance(snap, dict) else None)
        if chart is None and isinstance(snap, dict):
            try:
                chart = service.chart_on_demand(snap, obj.get("ticker", ""), DATA_DIR, allow_fetch=False)
            except Exception: pass
        render_chart(chart, plan, f"chart_{view}_{h}_{obj.get('ticker')}_{snap_id}")

def render_horizon(snap, h, calendar=None):
    st.subheader(HORIZON_LABELS.get(h, h))
    if not snap or not isinstance(snap, dict):
        st.info("尚無收益快照，請點擊上方『⚡ 更新市場與報酬研究』。")
        return

    picked = service.select_view(snap, h, qualified=True, n=3)
    
    if picked:
        st.caption("以下為通過淨報酬、樣本與風險門檻之正式研究標的：")
        for obj in picked:
            card(obj, h, snap, h, calendar=calendar, is_watchlist=False)
    else:
        st.warning(f"⚠️ **{HORIZON_LABELS.get(h, h)} 本期無通過嚴格硬性門檻之合格標的**")
        st.info("💡 已自動為您調出「最推薦的 3 檔潛力觀察個股」，並列出推估報酬 % 與資料可信度指標：")
        
        watch = service.select_view(snap, h, qualified=False, n=3)
        if watch:
            for obj in watch:
                card(obj, h, snap, "watch_" + h, calendar=calendar, is_watchlist=True)
        else:
            st.caption("目前市場環境下，亦無樣本充足且淨期望值為正的觀察標的。")

def main():
    st.set_page_config(page_title="Alpha Radar · Return First", page_icon="📈", layout="centered", initial_sidebar_state="collapsed")
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown("""<div class="hero"><div class="eyebrow">TAIWAN ALPHA RADAR · V8.3</div>
<h1>先看收益空間，再決定怎麼進場</h1>
<p>短・中・長線收益研究 × 真實價格條件 × 數據可信度解析<br>不以安全分代替收益，亦不使用人為虛構之 100 分 Edge。</p></div>""", unsafe_allow_html=True)
    
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    if st.session_state.get("v8_version") != service.OPERATIONS_VERSION:
        for key in ("v8_snapshot", "v8_doctor", "v8_error"):
            st.session_state.pop(key, None)
        st.session_state["v8_version"] = service.OPERATIONS_VERSION
        try:
            previous = service.load_dashboard(DATA_DIR / "dashboard_snapshot.json")
            if previous:
                st.session_state["v8_snapshot"] = service.compact_dashboard(previous)
        except Exception: pass

    with st.sidebar:
        st.markdown("### 資料與研究設定")
        family_label = st.selectbox("報酬模型的資料範圍", list(FAMILY_LABELS), key="family_v83")
        refs = st.selectbox("歷史參考股票數", [96, 160, 240], key="reference_v83")
        period = st.selectbox("歷史研究長度", ["5y", "8y", "10y", "3y"], key="period_v83")
        
        with st.expander("維護與快取", expanded=False):
            if st.button("清除本機行情快取 (SQLite)", key="clear_prices_v83"):
                DailyPriceStore(DATA_DIR / "daily_prices.sqlite").clear()
                st.success("已清除行情快取；舊快照仍保留。")

    settings = service.RunSettings(
        reference_size=int(refs), candidate_size=300, history_period=period,
        model_family=FAMILY_LABELS[family_label]
    )

    if st.button("⚡ 更新市場與報酬研究", type="primary", use_container_width=True, key="run_scan_v83"):
        progress = st.progress(0, text="準備資料")
        try:
            def update(stage, value):
                progress.progress(min(1., max(0., value)), text="建立日線快照／收益樣本：" + stage)
            snap = service.run_scan(DATA_DIR, settings, progress=update)
            st.session_state["v8_snapshot"] = service.compact_dashboard(snap)
            st.session_state.pop("v8_doctor", None)
            st.session_state.pop("v8_error", None)
        except Exception as exc:
            st.session_state["v8_error"] = f"{type(exc).__name__}: {exc}"
            st.error("本次更新未完成；不以空值覆蓋上一份成功快照。")
        finally:
            progress.empty()

    snap = st.session_state.get("v8_snapshot")
    calendar = calendar_reference(DATA_DIR, now=_taipei_timestamp())

    if snap and isinstance(snap, dict):
        st.markdown(f"""<div class="statusline">日線截至 <b>{esc(snap.get('price_date', ''))}</b> ·
研究基準 {esc(snap.get('market', {}).get('benchmark', ''))} · 收益期限 10／40／120交易日<br>
名冊 {snap.get('coverage', {}).get('requested', 0):,} → 同日有效 {snap.get('coverage', {}).get('feature_valid', 0):,} → 深度評估 {snap.get('candidate_n', 0):,}。</div>""", unsafe_allow_html=True)

    view = st.radio("功能", VIEW_LABELS, horizontal=True, label_visibility="collapsed", key="view_v83")

    if view == VIEW_LABELS[0]:
        st.subheader("⭐ 各週期的合格代表")
        if not snap or not isinstance(snap, dict):
            st.info("尚無收益快照，請點擊上方『⚡ 更新市場與報酬研究』。")
        else:
            any_pick = False
            for h in HORIZONS:
                picks = service.select_view(snap, h, True, 1)
                if picks:
                    any_pick = True
                    card(picks[0], h, snap, "prime", calendar=calendar)
                else:
                    st.info(f"{HORIZON_LABELS.get(h, h)}：目前沒有通過嚴格門檻的合格標的。")
            if not any_pick:
                st.warning("💡 各週期皆無合格標的，請切換至短/中/長線頁籤查看「最推薦 Top 3 潛力觀察個股」。")
    elif view == VIEW_LABELS[4]:
        st.subheader("🔎 個股診斷")
        code = st.text_input("股票代碼", value="2330", key="doctor_code_v83")
        if st.button("立即診斷", type="primary", use_container_width=True):
            if not snap or not isinstance(snap, dict):
                st.warning("請先點擊上方『⚡ 更新市場與報酬研究』建立基準資料庫後，再執行診斷。")
            else:
                dr = service.diagnose(code, snap, DATA_DIR)
                st.session_state["v8_doctor"] = service.compact_doctor_result(dr)
        
        dr = st.session_state.get("v8_doctor")
        if dr and snap and isinstance(dr, dict) and "stock" in dr:
            card(dr["stock"], "mid", snap, "doctor", dr.get("chart"), calendar=calendar)
    else:
        render_horizon(snap, {VIEW_LABELS[1]:"short", VIEW_LABELS[2]:"mid", VIEW_LABELS[3]:"long"}[view], calendar=calendar)

if __name__ == "__main__":
    main()