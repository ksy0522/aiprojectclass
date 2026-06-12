import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_OK = True
except ImportError:
    st.error("plotly 패키지가 설치되지 않았습니다. requirements.txt에 plotly를 추가하세요.")
    st.stop()

# ── 페이지 설정 ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="스마트팜 입지 분석",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 색상 팔레트 (농업·데이터 테마) ──────────────────────────────────────────
COLORS = {
    "primary":   "#2D6A4F",   # 깊은 초록
    "secondary": "#52B788",   # 밝은 초록
    "accent":    "#F4A261",   # 따뜻한 오렌지 (에너지/태양광)
    "light_bg":  "#F0F7F4",   # 연한 민트 배경
    "dark_text": "#1B2D24",   # 진한 텍스트
    "neutral":   "#B7C9BE",   # 중간 회색-초록
    "warning":   "#E76F51",   # 경고 오렌지
    "info":      "#457B9D",   # 정보 파랑
}

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=Space+Grotesk:wght@400;600;700&display=swap');

  html, body, [class*="css"] {{
    font-family: 'Noto Sans KR', sans-serif;
    color: {COLORS['dark_text']};
  }}

  /* 배경 */
  .stApp {{ background: {COLORS['light_bg']}; }}
  section[data-testid="stSidebar"] {{ background: {COLORS['primary']}; }}
  section[data-testid="stSidebar"] * {{ color: white !important; }}
  section[data-testid="stSidebar"] .stSelectbox label,
  section[data-testid="stSidebar"] .stMultiSelect label {{ color: white !important; }}

  /* 헤더 배너 */
  .hero-banner {{
    background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
    border-radius: 16px;
    padding: 36px 40px 28px;
    margin-bottom: 28px;
    color: white;
    position: relative;
    overflow: hidden;
  }}
  .hero-banner::before {{
    content: '🌱';
    position: absolute;
    right: 40px; top: 20px;
    font-size: 80px;
    opacity: 0.15;
  }}
  .hero-tag {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.7);
    margin-bottom: 8px;
  }}
  .hero-title {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 30px;
    font-weight: 700;
    color: white;
    margin: 0 0 8px;
    line-height: 1.2;
  }}
  .hero-subtitle {{
    font-size: 14px;
    color: rgba(255,255,255,0.85);
    margin: 0;
    line-height: 1.6;
  }}

  /* 카드 */
  .card {{
    background: white;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 16px;
    box-shadow: 0 2px 12px rgba(45,106,79,0.08);
    border-left: 4px solid {COLORS['secondary']};
  }}
  .card-title {{
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: {COLORS['primary']};
    margin-bottom: 16px;
  }}

  /* 지표 카드 */
  .metric-row {{ display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }}
  .metric-box {{
    flex: 1; min-width: 130px;
    background: white;
    border-radius: 10px;
    padding: 16px 18px;
    box-shadow: 0 2px 8px rgba(45,106,79,0.08);
    border-top: 3px solid {COLORS['secondary']};
    text-align: center;
  }}
  .metric-label {{ font-size: 11px; color: #888; font-weight: 500; margin-bottom: 6px; }}
  .metric-value {{ font-family: 'Space Grotesk', sans-serif; font-size: 26px; font-weight: 700; color: {COLORS['primary']}; }}
  .metric-unit {{ font-size: 12px; color: #aaa; }}

  /* 점수 배지 */
  .score-badge {{
    display: inline-block;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 48px;
    font-weight: 700;
    color: {COLORS['primary']};
    background: {COLORS['light_bg']};
    border-radius: 50%;
    width: 100px; height: 100px;
    line-height: 100px;
    text-align: center;
    border: 4px solid {COLORS['secondary']};
    margin: 8px auto;
    display: block;
  }}

  /* 차시 탭 배지 */
  .step-badge {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: {COLORS['primary']};
    color: white;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 12px;
  }}

  /* 정보 블록 */
  .info-block {{
    background: rgba(82,183,136,0.08);
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 13px;
    color: {COLORS['primary']};
    border-left: 3px solid {COLORS['secondary']};
    margin: 8px 0;
  }}
  .warning-block {{
    background: rgba(247,148,97,0.1);
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 13px;
    color: {COLORS['warning']};
    border-left: 3px solid {COLORS['warning']};
    margin: 8px 0;
  }}

  /* 교과 태그 */
  .tag-math    {{ background:#E8F4FD; color:#457B9D; border-radius:4px; padding:2px 8px; font-size:11px; font-weight:700; }}
  .tag-bio     {{ background:#E8F7EF; color:#2D6A4F; border-radius:4px; padding:2px 8px; font-size:11px; font-weight:700; }}
  .tag-physics {{ background:#FEF3E8; color:#F4A261; border-radius:4px; padding:2px 8px; font-size:11px; font-weight:700; }}

  /* Streamlit 기본 요소 오버라이드 */
  div[data-testid="stTabs"] button {{
    font-weight: 600;
    font-size: 14px;
  }}
  .stButton > button {{
    background: {COLORS['primary']};
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 10px 24px;
    transition: all 0.2s;
  }}
  .stButton > button:hover {{
    background: {COLORS['secondary']};
    transform: translateY(-1px);
  }}
  hr {{ border-color: {COLORS['neutral']}; opacity: 0.4; }}
</style>
""", unsafe_allow_html=True)


# ── 상수 데이터 ───────────────────────────────────────────────────────────────
REGIONS = {
    "서울": {"lat": 37.57, "lon": 126.98},
    "수원": {"lat": 37.27, "lon": 127.01},
    "강릉": {"lat": 37.75, "lon": 128.88},
    "청주": {"lat": 36.64, "lon": 127.49},
    "대전": {"lat": 36.35, "lon": 127.38},
    "전주": {"lat": 35.82, "lon": 127.15},
    "광주": {"lat": 35.16, "lon": 126.85},
    "대구": {"lat": 35.87, "lon": 128.60},
    "부산": {"lat": 35.10, "lon": 129.03},
    "제주": {"lat": 33.50, "lon": 126.53},
}

CROPS = {
    "상추": {
        "emoji": "🥬",
        "opt_temp": (15, 20),
        "opt_humid": (60, 80),
        "opt_solar": (150, 300),   # W/m²
        "growth_days": 30,
        "heating_coeff": 0.8,
        "cooling_coeff": 0.6,
    },
    "토마토": {
        "emoji": "🍅",
        "opt_temp": (20, 28),
        "opt_humid": (65, 75),
        "opt_solar": (300, 600),
        "growth_days": 90,
        "heating_coeff": 1.2,
        "cooling_coeff": 0.9,
    },
    "딸기": {
        "emoji": "🍓",
        "opt_temp": (17, 23),
        "opt_humid": (70, 80),
        "opt_solar": (200, 400),
        "growth_days": 60,
        "heating_coeff": 1.0,
        "cooling_coeff": 0.7,
    },
    "파프리카": {
        "emoji": "🫑",
        "opt_temp": (22, 28),
        "opt_humid": (65, 75),
        "opt_solar": (350, 650),
        "growth_days": 120,
        "heating_coeff": 1.3,
        "cooling_coeff": 1.0,
    },
}

MONTHS_KR = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]

def solar_wm2_to_mj(w):
    """W/m² → MJ/m²/day 환산 (역수: ÷11.6)"""
    return round(w / 11.6, 1)

def opt_solar_mj_str(crop_info):
    """작물의 최적 일사량을 MJ/m²/day 표시 문자열로 반환"""
    lo, hi = crop_info["opt_solar"]
    return f"{solar_wm2_to_mj(lo)}~{solar_wm2_to_mj(hi)} MJ/m²/day"


# ── API 호출 함수 ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_openmeteo(lat, lon):
    """Open-Meteo API: 월평균 기온·습도 (과거 1년)"""
    end   = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    url = (
        f"https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat}&longitude={lon}"
        f"&hourly=temperature_2m,relativehumidity_2m"
        f"&start_date={start}&end_date={end}"
        f"&timezone=Asia%2FSeoul"
    )
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
        temps   = data["hourly"]["temperature_2m"]
        humids  = data["hourly"]["relativehumidity_2m"]
        times   = pd.to_datetime(data["hourly"]["time"])
        df = pd.DataFrame({"time": times, "temp": temps, "humid": humids})
        df["month"] = df["time"].dt.month
        monthly = df.groupby("month").agg({"temp": "mean", "humid": "mean"}).reset_index()
        return monthly
    except Exception as e:
        return None

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_nasa_power(lat, lon):
    """NASA POWER API: 월별 기후 평균 일사량 (climatology 엔드포인트 사용)
    - climatology: 장기 월 평균값 제공, 지역별로 정확히 다른 값 반환
    - 키 형식: "JAN","FEB",...,"DEC" → 1~12월로 변환
    """
    url = (
        f"https://power.larc.nasa.gov/api/temporal/climatology/point"
        f"?parameters=ALLSKY_SFC_SW_DWN"
        f"&community=AG"
        f"&longitude={lon}&latitude={lat}"
        f"&format=JSON"
    )
    MONTH_MAP = {
        "JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,
        "JUL":7,"AUG":8,"SEP":9,"OCT":10,"NOV":11,"DEC":12
    }
    try:
        r = requests.get(url, timeout=25)
        r.raise_for_status()
        data = r.json()
        values = data["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]
        months, solar = [], []
        for k, v in values.items():
            if k in MONTH_MAP and v not in (-999, -999.0):
                months.append(MONTH_MAP[k])
                solar.append(float(v))
        if len(months) < 12:
            return None
        solar_df = pd.DataFrame({"month": months, "solar": solar})
        return solar_df.sort_values("month").reset_index(drop=True)
    except Exception:
        return None

def get_region_data(region):
    lat, lon = REGIONS[region]["lat"], REGIONS[region]["lon"]
    with st.spinner(f"🌐 {region} 기상 데이터 수집 중..."):
        meteo = fetch_openmeteo(lat, lon)
        nasa  = fetch_nasa_power(lat, lon)
    return meteo, nasa, lat

# 지역별 월 평균 일사량 fallback (기상청·NASA POWER 자료 기반 추정값, MJ/m²/day)
SOLAR_FALLBACK = {
    # 위도 33~34 (제주권): 일사량 가장 많음
    (33.0, 34.5): [3.0,3.8,4.8,5.8,6.2,5.8,5.0,5.5,4.8,4.0,3.1,2.7],
    # 위도 34.5~36 (광주·전주권)
    (34.5, 36.0): [2.8,3.5,4.5,5.5,6.0,5.5,4.7,5.2,4.5,3.7,2.9,2.5],
    # 위도 36~37 (대전·청주권)
    (36.0, 37.0): [2.6,3.3,4.3,5.2,5.8,5.3,4.5,5.0,4.3,3.5,2.7,2.3],
    # 위도 37~38 (서울·수원·강릉권)
    (37.0, 38.5): [2.4,3.1,4.1,5.0,5.6,5.1,4.3,4.8,4.1,3.3,2.5,2.1],
    # 위도 38.5 이상 (북부)
    (38.5, 40.0): [2.2,2.9,3.9,4.8,5.4,4.9,4.1,4.6,3.9,3.1,2.3,1.9],
}

def _get_solar_fallback(lat):
    """위도에 맞는 fallback 일사량 리스트 반환"""
    for (lo, hi), vals in SOLAR_FALLBACK.items():
        if lo <= lat < hi:
            return vals
    # 범위 밖이면 가장 가까운 것 선택
    return SOLAR_FALLBACK[(37.0, 38.5)]

def build_monthly_df(meteo, nasa, lat=37.0):
    """기상·일사량 병합 DataFrame (12개월)"""
    if meteo is None:
        return None
    df = meteo.copy()
    if nasa is not None:
        merged = df.merge(nasa, on="month", how="left")
        # NASA 데이터가 merge 후 일부 NaN이면 fallback으로 채움
        if merged["solar"].isna().any():
            fb = _get_solar_fallback(lat)
            merged["solar"] = merged.apply(
                lambda row: fb[int(row["month"])-1] if pd.isna(row["solar"]) else row["solar"],
                axis=1
            )
        df = merged
    else:
        fb = _get_solar_fallback(lat)
        df["solar"] = [fb[int(m)-1] for m in df["month"]]
    df["month_kr"] = df["month"].apply(lambda m: MONTHS_KR[m-1])
    return df


# ── 점수 계산 함수 ────────────────────────────────────────────────────────────
def score_component(value, opt_min, opt_max, weight=1.0):
    """최적 범위 대비 점수 (0~100)"""
    opt_mid  = (opt_min + opt_max) / 2
    opt_half = (opt_max - opt_min) / 2
    deviation = abs(value - opt_mid) / (opt_half + 1e-9)
    raw = max(0, 100 - deviation * 60)
    return raw * weight

def calc_suitability(df, crop):
    """월별 적합도 + 연간 평균 점수"""
    c = CROPS[crop]
    df = df.copy()
    df["temp_score"]  = df["temp"].apply(
        lambda t: score_component(t, *c["opt_temp"]))
    df["humid_score"] = df["humid"].apply(
        lambda h: score_component(h, *c["opt_humid"]))
    df["solar_score"] = df["solar"].apply(
        lambda s: score_component(s * 11.6, *c["opt_solar"]))  # MJ→W/m² 환산
    df["total_score"] = (
        df["temp_score"]  * 0.40 +
        df["humid_score"] * 0.25 +
        df["solar_score"] * 0.35
    )
    return df

def calc_energy(df, crop, area_m2=1000):
    """예상 냉·난방 비용 (만원/년, 간이 계산)"""
    c = CROPS[crop]
    opt_mid_temp = sum(c["opt_temp"]) / 2

    heating_kwh = 0.0
    cooling_kwh = 0.0
    for _, row in df.iterrows():
        delta = opt_mid_temp - row["temp"]
        if delta > 0:   # 난방 필요
            heating_kwh += delta * area_m2 * c["heating_coeff"] * 30 * 24 / 1000
        else:           # 냉방 필요
            cooling_kwh += (-delta) * area_m2 * c["cooling_coeff"] * 30 * 24 / 1000

    kwh_price = 130  # 원/kWh (산업용 전기 추정)
    heating_cost = heating_kwh * kwh_price / 10000  # 만원
    cooling_cost = cooling_kwh * kwh_price / 10000
    return round(heating_cost), round(cooling_cost)

def calc_led_supplement(df, crop):
    """LED 보광 필요도 (월별 부족 일사량 비율)"""
    c = CROPS[crop]
    opt_solar_wm2 = sum(c["opt_solar"]) / 2
    df = df.copy()
    df["solar_wm2"] = df["solar"] * 11.6
    df["led_need"]  = df["solar_wm2"].apply(
        lambda s: max(0, (opt_solar_wm2 - s) / opt_solar_wm2 * 100))
    return df


# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌱 탐구 설정")
    st.markdown("---")

    st.markdown("**📍 지역 선택**")
    selected_regions = st.multiselect(
        "비교할 지역을 선택하세요 (최대 3곳)",
        list(REGIONS.keys()),
        default=["서울", "제주"],
        max_selections=3,
        label_visibility="collapsed"
    )

    st.markdown("**🌿 작물 선택**")
    selected_crop = st.selectbox(
        "재배 작물",
        list(CROPS.keys()),
        format_func=lambda c: f"{CROPS[c]['emoji']} {c}",
        label_visibility="collapsed"
    )

    st.markdown("**🏗️ 스마트팜 규모**")
    farm_area = st.slider("재배 면적 (m²)", 100, 5000, 1000, 100)

    st.markdown("---")
    st.markdown(f"""
    <div style="font-size:12px; color:rgba(255,255,255,0.7); line-height:1.8;">
    📡 <b>사용 API</b><br>
    · Open-Meteo (기온·습도)<br>
    · NASA POWER (일사량)
    </div>
    """, unsafe_allow_html=True)

    run_btn = st.button("🔍 분석 시작", use_container_width=True)
    if run_btn:
        st.session_state["run_analysis"] = True
        st.session_state["analysis_regions"] = list(selected_regions)
        st.session_state["analysis_crop"] = selected_crop
        st.session_state["analysis_area"] = farm_area
        # 지역/작물 변경 시 캐시 초기화
        st.session_state.pop("region_data_cache", None)


# ── 메인 영역 ─────────────────────────────────────────────────────────────────
# 헤더
st.markdown("""
<div class="hero-banner">
  <div class="hero-tag">수학 · 생명과학 · 물리 융합 프로젝트</div>
  <div class="hero-title">데이터로 찾는 최적의 스마트팜 입지</div>
  <p class="hero-subtitle">
    실제 기상 API 데이터를 활용하여 지역별 환경을 분석하고,<br>
    작물 생장 조건과 에너지 효율을 고려한 최적 입지를 탐구합니다.
  </p>
</div>
""", unsafe_allow_html=True)

# 탭
tab1, tab_lab, tab2, tab3, tab4 = st.tabs([
    "📖 1차시 · 수업 개요",
    "🌿 1.5차시 · 생장 조건 탐구",
    "📊 2차시 · 데이터 분석",
    "⚡ 3차시 · 최적화 설계",
    "🏆 4차시 · 결과 발표",
])


# ════════════════════════════════════════════════════════
# TAB 1 — 수업 개요
# ════════════════════════════════════════════════════════
with tab1:
    col_a, col_b = st.columns([3, 2])

    with col_a:
        st.markdown("""
        <div class="card">
          <div class="card-title">🔍 탐구 문제</div>
          <p style="font-size:17px; font-weight:700; color:#1B2D24; line-height:1.6;">
            "우리나라에서 스마트팜을 가장 효율적으로<br>운영할 수 있는 지역은 어디일까?"
          </p>
          <div class="info-block">
            학생들은 실제 기상 데이터를 활용하여 지역별 환경을 분석하고,
            작물 생장 조건과 에너지 효율을 고려하여 최적의 스마트팜 입지를 선정한다.
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="card">
          <div class="card-title">📚 교과 융합 요소</div>
          <table style="width:100%; font-size:14px; border-collapse:collapse;">
            <tr style="border-bottom:1px solid #eee;">
              <td style="padding:10px 8px;"><span class="tag-physics">물리</span></td>
              <td style="padding:10px 8px; color:#555;">빛 에너지, 열에너지, 에너지 효율</td>
            </tr>
            <tr style="border-bottom:1px solid #eee;">
              <td style="padding:10px 8px;"><span class="tag-bio">생명과학</span></td>
              <td style="padding:10px 8px; color:#555;">광합성, 증산작용, 작물 생장 조건</td>
            </tr>
            <tr>
              <td style="padding:10px 8px;"><span class="tag-math">수학</span></td>
              <td style="padding:10px 8px; color:#555;">데이터 분석, 그래프 해석, 최적화</td>
            </tr>
          </table>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown("""
        <div class="card">
          <div class="card-title">🗓️ 차시별 운영</div>
        """, unsafe_allow_html=True)

        steps = [
            ("1차시", "🌱", "탐구 문제 설정", "스마트팜 원리 이해 · 작물 생장 조건 탐색 · 탐구 질문 설정"),
            ("2차시", "📊", "데이터 수집 및 분석", "API 기상 데이터 수집 · 기온·습도·일사량 비교 · 그래프 분석"),
            ("3차시", "⚡", "스마트팜 최적화 설계", "작물 선택 · 생장 조건 설정 · 에너지 계산 · 적합도 산출"),
            ("4차시", "🏆", "결과 발표", "최적 입지 선정 · 데이터 기반 근거 · 지역별 장단점 비교"),
        ]
        for code, emoji, title, desc in steps:
            st.markdown(f"""
            <div style="display:flex; gap:12px; align-items:flex-start; margin-bottom:14px;">
              <div style="background:#2D6A4F; color:white; border-radius:8px;
                          padding:6px 10px; font-size:11px; font-weight:700;
                          white-space:nowrap; margin-top:2px;">{code}</div>
              <div>
                <div style="font-weight:700; font-size:14px;">{emoji} {title}</div>
                <div style="font-size:12px; color:#777; margin-top:2px;">{desc}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
        <div class="card" style="border-left-color:#F4A261;">
          <div class="card-title">🔌 API 데이터 소스</div>
          <div style="font-size:13px; line-height:2.0;">
            <b>Open-Meteo API</b><br>
            &nbsp;&nbsp;· 기온 &nbsp;· 습도 &nbsp;· 강수량<br>
            <b>NASA POWER API</b><br>
            &nbsp;&nbsp;· 일사량 (월평균 MJ/m²/day)
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card" style="border-left-color:#457B9D; background:linear-gradient(to right, #F0F7F4, white);">
      <div class="card-title">✅ 기대 효과</div>
      <div style="display:flex; flex-wrap:wrap; gap:10px; font-size:13px;">
        <span style="background:#E8F7EF; color:#2D6A4F; border-radius:20px; padding:6px 14px;">실제 데이터 기반 탐구 수행</span>
        <span style="background:#E8F7EF; color:#2D6A4F; border-radius:20px; padding:6px 14px;">수학·생명과학·물리 융합적 이해</span>
        <span style="background:#E8F7EF; color:#2D6A4F; border-radius:20px; padding:6px 14px;">기후변화와 식량 문제 의사결정 경험</span>
        <span style="background:#E8F7EF; color:#2D6A4F; border-radius:20px; padding:6px 14px;">AI·데이터 기반 미래 농업 기술 이해</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-block" style="font-size:14px; font-weight:500;">
      💡 <b>한 줄 요약:</b> 실제 기상 데이터를 활용하여 지역별 스마트팜 운영 효율을 분석하고,
      최적의 스마트팜 입지를 선정하는 융합형 프로젝트 수업입니다.
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════
# 데이터 로드 (탭 2·3·4 공통)
# ════════════════════════════════════════════════════════
region_data = {}

# 분석 실행: 버튼을 눌렀을 때만 API 호출 및 캐시 저장
if st.session_state.get("run_analysis") and "region_data_cache" not in st.session_state:
    load_regions = st.session_state.get("analysis_regions", selected_regions)
    load_crop    = st.session_state.get("analysis_crop", selected_crop)
    cache = {}
    for r in load_regions:
        meteo, nasa, lat_r = get_region_data(r)
        df = build_monthly_df(meteo, nasa, lat=lat_r)
        if df is not None:
            df = calc_suitability(df, load_crop)
            df = calc_led_supplement(df, load_crop)
            cache[r] = df
    st.session_state["region_data_cache"] = cache

region_data = st.session_state.get("region_data_cache", {})
display_crop = st.session_state.get("analysis_crop", selected_crop)
display_area = st.session_state.get("analysis_area", farm_area)



# ════════════════════════════════════════════════════════
# TAB LAB — 생장 조건 탐구 실험실 (1.5차시)
# ════════════════════════════════════════════════════════
with tab_lab:
    st.markdown("""
    <div class="step-badge">🌿 1.5차시 · 생장 조건 탐구 실험실</div>
    <div style="font-size:13px; color:#555; margin-bottom:20px;">
      <span class="tag-bio">생명과학</span>&nbsp;<span class="tag-physics">물리</span>&nbsp;<span class="tag-math">수학</span>&nbsp;
      슬라이더로 환경 변수를 조절하며 식물 생장에 미치는 영향을 직접 탐구합니다.
    </div>
    """, unsafe_allow_html=True)

    # ── 작물 선택 ──
    lab_crop = st.selectbox(
        "탐구할 작물 선택",
        list(CROPS.keys()),
        format_func=lambda c: f"{CROPS[c]['emoji']} {c}",
        key="lab_crop"
    )
    lc = CROPS[lab_crop]

    st.markdown("---")

    # ── 생장 모델 계산 함수 ──
    import math

    def photosynthesis_rate(solar, temp, humid, crop):
        """광합성 속도 모델 (0~100 상대값)"""
        c = CROPS[crop]
        s_min, s_max = c["opt_solar"]
        s_mid = (s_min + s_max) / 2
        s_rate = 100 / (1 + math.exp(-0.008 * (solar - s_mid)))
        if solar > s_max:
            s_rate *= max(0.6, 1 - (solar - s_max) / (s_max * 2))

        t_opt = sum(c["opt_temp"]) / 2
        t_rate = 100 * math.exp(-0.012 * (temp - t_opt) ** 2)

        h_min, h_max = c["opt_humid"]
        h_opt = (h_min + h_max) / 2
        h_rate = 100 * math.exp(-0.003 * (humid - h_opt) ** 2)

        limiting = min(s_rate, t_rate, h_rate)
        combined = (s_rate * 0.45 + t_rate * 0.35 + h_rate * 0.20) * 0.6 + limiting * 0.4
        return round(min(100, max(0, combined)), 1)

    def transpiration_rate(temp, humid, solar):
        """증산속도 모델 (0~100 상대값)"""
        base = (temp / 45) * 50 + ((100 - humid) / 100) * 30 + (solar / 800) * 20
        return round(min(100, max(0, base)), 1)

    def growth_score(photo, transp, temp, humid, crop):
        """종합 생장 점수"""
        c = CROPS[crop]
        transp_penalty = max(0, (transp - 70) * 0.5)
        t_opt = sum(c["opt_temp"]) / 2
        temp_stress = max(0, abs(temp - t_opt) - 5) * 2
        score = photo - transp_penalty - temp_stress
        return round(min(100, max(0, score)), 1)

    # 광보상점/광포화점
    comp_point = lc["opt_solar"][0] * 0.3
    sat_point  = lc["opt_solar"][1]

    # ════════════════════════════════════════════════════
    # 레이아웃: 좌(슬라이더+지표+분석) / 우(그래프)
    # 슬라이더를 조절하면 같은 화면 좌측에서 바로 결과를 확인할 수 있습니다.
    # ════════════════════════════════════════════════════
    col_left, col_right = st.columns([1, 1.3])

    with col_left:
        # ── 슬라이더 3개 (세로 배치, 결과와 같은 컬럼) ──
        st.markdown("##### 🎛️ 환경 변수 조절")

        st.markdown(f"""<div class="card" style="border-left-color:#F4A261; margin-bottom:6px; padding:12px 16px;">
          <div class="card-title" style="margin-bottom:4px;">☀️ 일사량 <span class="tag-physics">물리</span></div>
          <div style="font-size:11px; color:#888;">
            빛 에너지가 광합성에 필요한 ATP·NADPH를 생성합니다.
          </div>
        </div>""", unsafe_allow_html=True)
        lab_solar = st.slider("일사량 (W/m²)", 0, 800, 300, 10, key="lab_solar")
        st.caption(f"≈ {solar_wm2_to_mj(lab_solar)} MJ/m²/day  (2차시 그래프와 동일 단위)")

        st.markdown(f"""<div class="card" style="border-left-color:#E76F51; margin-bottom:6px; padding:12px 16px;">
          <div class="card-title" style="margin-bottom:4px;">🌡️ 온도 <span class="tag-bio">생명과학</span></div>
          <div style="font-size:11px; color:#888;">
            효소 활성에 영향을 주어 광합성·호흡 속도를 결정합니다.
          </div>
        </div>""", unsafe_allow_html=True)
        lab_temp = st.slider("온도 (°C)", 0, 45, 22, 1, key="lab_temp")

        st.markdown(f"""<div class="card" style="border-left-color:#457B9D; margin-bottom:6px; padding:12px 16px;">
          <div class="card-title" style="margin-bottom:4px;">💧 습도 <span class="tag-bio">생명과학</span></div>
          <div style="font-size:11px; color:#888;">
            기공 개폐에 영향을 주어 CO₂ 흡수와 증산작용을 조절합니다.
          </div>
        </div>""", unsafe_allow_html=True)
        lab_humid = st.slider("습도 (%)", 0, 100, 65, 1, key="lab_humid")

        # 현재 값 계산
        photo  = photosynthesis_rate(lab_solar, lab_temp, lab_humid, lab_crop)
        transp = transpiration_rate(lab_temp, lab_humid, lab_solar)
        growth = growth_score(photo, transp, lab_temp, lab_humid, lab_crop)

        st.markdown("---")

        # ── 결과 지표 (슬라이더 바로 아래) ──
        st.markdown("##### 📊 현재 조건의 생장 지표")
        mc1, mc2, mc3 = st.columns(3)
        indicators = [
            ("🌿 광합성 속도", photo, "%", "#52B788"),
            ("💦 증산 속도",   transp, "%", "#457B9D"),
            ("📈 종합 생장 점수", growth, "점", "#2D6A4F"),
        ]
        for col, (label, val, unit, color) in zip([mc1, mc2, mc3], indicators):
            with col:
                bar_w = int(val)
                st.markdown(f"""
                <div class="metric-box" style="border-top-color:{color};">
                  <div class="metric-label">{label}</div>
                  <div class="metric-value" style="color:{color}; font-size:22px;">{val}</div>
                  <div class="metric-unit">{unit}</div>
                  <div style="background:#eee; border-radius:4px; height:6px; margin-top:8px;">
                    <div style="background:{color}; width:{bar_w}%; height:6px; border-radius:4px; transition:width 0.3s;"></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # ── 현재 조건 분석 (피드백) — 슬라이더와 같은 컬럼에서 즉시 확인 ──
        st.markdown("##### 🔍 현재 조건 분석")

        feedbacks = []

        # 일사량 판단
        s_min, s_max = lc["opt_solar"]
        if lab_solar < s_min * 0.3:
            feedbacks.append(("warning", f"⚠️ <b>일사량 부족</b> ({lab_solar} W/m² ≈ {solar_wm2_to_mj(lab_solar)} MJ/m²/day): 광보상점에 미치지 못해 광합성보다 호흡이 우세합니다. LED 보광이 필요합니다."))
        elif lab_solar < s_min:
            feedbacks.append(("warning", f"⚠️ <b>일사량 낮음</b> ({lab_solar} W/m² ≈ {solar_wm2_to_mj(lab_solar)} MJ/m²/day): 광합성은 가능하지만 최적 범위({opt_solar_mj_str(lc)})보다 낮습니다."))
        elif lab_solar <= s_max:
            feedbacks.append(("info", f"✅ <b>일사량 적정</b> ({lab_solar} W/m² ≈ {solar_wm2_to_mj(lab_solar)} MJ/m²/day): {lab_crop}의 최적 광합성 범위 내에 있습니다."))
        else:
            feedbacks.append(("warning", f"⚠️ <b>일사량 과다</b> ({lab_solar} W/m² ≈ {solar_wm2_to_mj(lab_solar)} MJ/m²/day): 광포화점({solar_wm2_to_mj(s_max)} MJ/m²/day)을 초과하여 광억제가 발생할 수 있습니다."))

        # 온도 판단
        t_min, t_max = lc["opt_temp"]
        if lab_temp < t_min - 5:
            feedbacks.append(("warning", f"⚠️ <b>저온 스트레스</b> ({lab_temp}°C): 효소 활성이 크게 저하되어 생장이 거의 멈춥니다."))
        elif lab_temp < t_min:
            feedbacks.append(("warning", f"⚠️ <b>온도 낮음</b> ({lab_temp}°C): 최적 온도({t_min}~{t_max}°C)보다 낮아 광합성 효율이 떨어집니다."))
        elif lab_temp <= t_max:
            feedbacks.append(("info", f"✅ <b>온도 적정</b> ({lab_temp}°C): {lab_crop}의 최적 온도 범위 내입니다."))
        elif lab_temp < t_max + 5:
            feedbacks.append(("warning", f"⚠️ <b>온도 높음</b> ({lab_temp}°C): 최적 범위를 벗어나 호흡 소모가 증가합니다."))
        else:
            feedbacks.append(("warning", f"⚠️ <b>고온 스트레스</b> ({lab_temp}°C): 효소 변성이 일어나 광합성이 급격히 감소합니다."))

        # 습도 판단
        h_min, h_max = lc["opt_humid"]
        if lab_humid < h_min - 10:
            feedbacks.append(("warning", f"⚠️ <b>습도 매우 낮음</b> ({lab_humid}%): 기공이 닫혀 CO₂ 공급이 차단되고 증산 스트레스가 심합니다."))
        elif lab_humid < h_min:
            feedbacks.append(("warning", f"⚠️ <b>습도 낮음</b> ({lab_humid}%): 증산이 과다하여 수분 손실이 클 수 있습니다."))
        elif lab_humid <= h_max:
            feedbacks.append(("info", f"✅ <b>습도 적정</b> ({lab_humid}%): 기공이 열려 CO₂ 흡수와 수분 균형이 좋습니다."))
        else:
            feedbacks.append(("warning", f"⚠️ <b>습도 과다</b> ({lab_humid}%): 곰팡이·병해 위험이 높아지고 증산이 억제됩니다."))

        # 종합 생장 점수 판단
        if growth >= 80:
            feedbacks.append(("info", f"🌟 <b>종합 생장 점수 {growth}점</b>: 매우 좋은 조건입니다! 이 환경을 유지하면 최적 생장을 기대할 수 있습니다."))
        elif growth >= 60:
            feedbacks.append(("info", f"📊 <b>종합 생장 점수 {growth}점</b>: 양호한 조건입니다. 위의 경고 항목을 보완하면 더 높아집니다."))
        else:
            feedbacks.append(("warning", f"📉 <b>종합 생장 점수 {growth}점</b>: 개선이 필요합니다. 경고 항목을 먼저 수정하세요."))

        for ftype, ftext in feedbacks:
            css_class = "info-block" if ftype == "info" else "warning-block"
            st.markdown(f'<div class="{css_class}" style="margin-bottom:6px;">{ftext}</div>', unsafe_allow_html=True)

    with col_right:
        # ── 그래프 4개 (우측에 세로 배치) ──
        st.markdown("##### 📈 환경 변수와 생장의 관계 그래프")
        st.markdown("""
        <div class="info-block" style="margin-bottom:10px;">
          💡 왼쪽 슬라이더를 움직이면 아래 그래프의 <b>주황 점선(현재 조건)</b>이 실시간으로 이동합니다.
        </div>
        """, unsafe_allow_html=True)

        solar_range = list(range(0, 810, 10))
        temp_range  = list(range(0, 46, 1))

        # 광합성 속도 vs 일사량 (광반응 곡선)
        photo_by_solar = [photosynthesis_rate(s, lab_temp, lab_humid, lab_crop) for s in solar_range]
        fig_solar = go.Figure()
        fig_solar.add_trace(go.Scatter(
            x=solar_range, y=photo_by_solar,
            mode="lines", name="광합성 속도",
            line=dict(color="#52B788", width=2.5),
            fill="tozeroy", fillcolor="rgba(82,183,136,0.08)"
        ))
        fig_solar.add_vline(x=lab_solar, line_dash="dash", line_color="#F4A261", line_width=2,
                            annotation_text=f"현재 {lab_solar} W/m² ({solar_wm2_to_mj(lab_solar)} MJ/m²/day)", annotation_font_size=10)
        fig_solar.add_vline(x=comp_point, line_dash="dot", line_color="#aaa", line_width=1,
                            annotation_text="광보상점", annotation_position="bottom right",
                            annotation_font_size=10)
        fig_solar.add_vline(x=sat_point, line_dash="dot", line_color="#888", line_width=1,
                            annotation_text="광포화점", annotation_position="bottom right",
                            annotation_font_size=10)
        fig_solar.update_layout(
            title=dict(text="☀️ 일사량 vs 광합성 속도", font=dict(size=13, color="#1B2D24")),
            xaxis_title="일사량 (W/m² · ÷11.6 = MJ/m²/day)", yaxis_title="광합성 속도 (%)",
            yaxis=dict(range=[0, 110]),
            height=240, paper_bgcolor="white", plot_bgcolor="#FAFAFA",
            margin=dict(l=40, r=20, t=40, b=35),
            showlegend=False,
        )

        # 광합성 속도 vs 온도
        photo_by_temp = [photosynthesis_rate(lab_solar, t, lab_humid, lab_crop) for t in temp_range]
        fig_temp_lab = go.Figure()
        fig_temp_lab.add_trace(go.Scatter(
            x=temp_range, y=photo_by_temp,
            mode="lines", name="광합성 속도",
            line=dict(color="#E76F51", width=2.5),
            fill="tozeroy", fillcolor="rgba(231,111,81,0.07)"
        ))
        fig_temp_lab.add_vrect(
            x0=lc["opt_temp"][0], x1=lc["opt_temp"][1],
            fillcolor="rgba(82,183,136,0.12)", line_width=0,
            annotation_text="최적 온도", annotation_font_size=10,
        )
        fig_temp_lab.add_vline(x=lab_temp, line_dash="dash", line_color="#F4A261", line_width=2,
                               annotation_text=f"현재 {lab_temp}°C", annotation_font_size=11)
        fig_temp_lab.update_layout(
            title=dict(text="🌡️ 온도 vs 광합성 속도", font=dict(size=13, color="#1B2D24")),
            xaxis_title="온도 (°C)", yaxis_title="광합성 속도 (%)",
            yaxis=dict(range=[0, 110]),
            height=240, paper_bgcolor="white", plot_bgcolor="#FAFAFA",
            margin=dict(l=40, r=20, t=40, b=35),
            showlegend=False,
        )

        # 증산속도 vs 온도
        transp_by_temp = [transpiration_rate(t, lab_humid, lab_solar) for t in temp_range]
        fig_transp = go.Figure()
        fig_transp.add_trace(go.Scatter(
            x=temp_range, y=transp_by_temp,
            mode="lines", name="증산 속도",
            line=dict(color="#457B9D", width=2.5),
            fill="tozeroy", fillcolor="rgba(69,123,157,0.07)"
        ))
        fig_transp.add_vline(x=lab_temp, line_dash="dash", line_color="#F4A261", line_width=2,
                             annotation_text=f"현재 {lab_temp}°C", annotation_font_size=11)
        fig_transp.update_layout(
            title=dict(text="💧 온도 vs 증산 속도", font=dict(size=13, color="#1B2D24")),
            xaxis_title="온도 (°C)", yaxis_title="증산 속도 (%)",
            yaxis=dict(range=[0, 110]),
            height=240, paper_bgcolor="white", plot_bgcolor="#FAFAFA",
            margin=dict(l=40, r=20, t=40, b=35),
            showlegend=False,
        )

        # 광합성 vs 증산 (현재 조건 점 표시)
        fig_pt = go.Figure()
        photo_traj  = [photosynthesis_rate(lab_solar, t, lab_humid, lab_crop) for t in temp_range]
        transp_traj = [transpiration_rate(t, lab_humid, lab_solar) for t in temp_range]
        fig_pt.add_trace(go.Scatter(
            x=transp_traj, y=photo_traj,
            mode="lines",
            line=dict(color=COLORS["neutral"], width=1.5),
            name="온도 변화 궤적",
            hovertemplate="온도: %{text}°C<br>증산: %{x:.0f}%<br>광합성: %{y:.0f}%",
            text=[str(t) for t in temp_range],
        ))
        fig_pt.add_trace(go.Scatter(
            x=[transp], y=[photo],
            mode="markers",
            marker=dict(size=14, color=COLORS["accent"], symbol="star",
                        line=dict(color="white", width=2)),
            name="현재 조건",
        ))
        fig_pt.add_shape(type="rect", x0=0, x1=40, y0=60, y1=110,
                         fillcolor="rgba(82,183,136,0.08)", line_width=0)
        fig_pt.add_annotation(x=20, y=105, text="✅ 이상 구역", showarrow=False,
                              font=dict(size=10, color="#2D6A4F"))
        fig_pt.update_layout(
            title=dict(text="🔬 광합성 vs 증산 관계 (온도 변화)", font=dict(size=13, color="#1B2D24")),
            xaxis_title="증산 속도 (%)", yaxis_title="광합성 속도 (%)",
            xaxis=dict(range=[0, 100]), yaxis=dict(range=[0, 110]),
            height=240, paper_bgcolor="white", plot_bgcolor="#FAFAFA",
            margin=dict(l=40, r=20, t=40, b=35),
            legend=dict(orientation="h", y=1.18, font=dict(size=10)),
        )

        st.plotly_chart(fig_solar, use_container_width=True)
        st.plotly_chart(fig_temp_lab, use_container_width=True)
        st.plotly_chart(fig_transp, use_container_width=True)
        st.plotly_chart(fig_pt, use_container_width=True)

    # ── 탐구 질문 (전체 너비) ──
    st.markdown("---")
    st.markdown("""
    <div class="card" style="border-left-color:#F4A261;">
      <div class="card-title">💬 탐구 질문</div>
      <div style="font-size:14px; line-height:2.4; color:#333;">
        1. 일사량을 계속 높이면 광합성 속도도 계속 증가할까? 왜 그렇지 않을까? <span class="tag-bio">생명과학</span><br>
        2. 같은 온도에서도 습도에 따라 생장 점수가 달라지는 이유는? <span class="tag-bio">생명과학</span><br>
        3. 광합성 속도와 증산 속도 그래프에서 최적 온도가 다른 이유는 무엇일까? <span class="tag-physics">물리</span><br>
        4. 세 변수 중 어느 것이 현재 작물 생장을 가장 크게 제한하고 있는가? <span class="tag-math">수학</span>
      </div>
    </div>    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════
# TAB 2 — 데이터 수집 및 분석
# ════════════════════════════════════════════════════════
with tab2:
    st.markdown("""
    <div class="step-badge">📊 2차시 · 데이터 수집 및 분석</div>
    <div style="font-size:13px; color:#555; margin-bottom:20px;">
      <span class="tag-math">수학</span>&nbsp;
      <span class="tag-physics">물리</span>&nbsp;
      Open-Meteo · NASA POWER API로 실제 기상 데이터를 수집하고 비교합니다.
    </div>
    """, unsafe_allow_html=True)

    if not region_data:
        st.info("👈 사이드바에서 지역을 선택하고 **분석 시작**을 누르세요.")
    else:
        # 요약 지표
        cols = st.columns(len(region_data))
        for i, (region, df) in enumerate(region_data.items()):
            with cols[i]:
                avg_temp  = df["temp"].mean()
                avg_humid = df["humid"].mean()
                avg_solar = df["solar"].mean()
                st.markdown(f"""
                <div class="card" style="text-align:center;">
                  <div style="font-size:20px; font-weight:700; color:#2D6A4F; margin-bottom:8px;">📍 {region}</div>
                  <div class="metric-row" style="justify-content:center; flex-direction:column; gap:8px;">
                    <div><span style="font-size:22px; font-weight:700; color:#E76F51;">{avg_temp:.1f}°C</span>
                         <span style="font-size:11px; color:#999;"> 연평균 기온</span></div>
                    <div><span style="font-size:22px; font-weight:700; color:#457B9D;">{avg_humid:.0f}%</span>
                         <span style="font-size:11px; color:#999;"> 평균 습도</span></div>
                    <div><span style="font-size:22px; font-weight:700; color:#F4A261;">{avg_solar:.1f}</span>
                         <span style="font-size:11px; color:#999;"> MJ/m²/day</span></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # 기온 비교 그래프
        fig_temp = go.Figure()
        crop_info = CROPS[display_crop]
        fig_temp.add_hrect(
            y0=crop_info["opt_temp"][0], y1=crop_info["opt_temp"][1],
            fillcolor="rgba(82,183,136,0.12)", line_width=0,
            annotation_text=f"{display_crop} 최적 기온 범위",
            annotation_position="top left",
            annotation_font_size=11,
        )
        region_colors = ["#2D6A4F", "#F4A261", "#457B9D"]
        for i, (region, df) in enumerate(region_data.items()):
            fig_temp.add_trace(go.Scatter(
                x=df["month_kr"], y=df["temp"],
                mode="lines+markers", name=region,
                line=dict(color=region_colors[i], width=2.5),
                marker=dict(size=7)
            ))
        fig_temp.update_layout(
            title=dict(text="🌡️ 월별 평균 기온 비교", font=dict(size=15, color="#1B2D24")),
            xaxis_title="월", yaxis_title="기온 (°C)",
            height=320, paper_bgcolor="white", plot_bgcolor="#FAFAFA",
            legend=dict(orientation="h", y=1.15),
            margin=dict(l=40, r=20, t=50, b=40),
        )

        # 습도 비교 그래프
        fig_humid = go.Figure()
        fig_humid.add_hrect(
            y0=crop_info["opt_humid"][0], y1=crop_info["opt_humid"][1],
            fillcolor="rgba(69,123,157,0.10)", line_width=0,
        )
        for i, (region, df) in enumerate(region_data.items()):
            fig_humid.add_trace(go.Bar(
                x=df["month_kr"], y=df["humid"],
                name=region, marker_color=region_colors[i], opacity=0.75,
            ))
        fig_humid.update_layout(
            title=dict(text="💧 월별 평균 습도 비교", font=dict(size=15, color="#1B2D24")),
            xaxis_title="월", yaxis_title="습도 (%)",
            height=320, paper_bgcolor="white", plot_bgcolor="#FAFAFA",
            barmode="group", legend=dict(orientation="h", y=1.15),
            margin=dict(l=40, r=20, t=50, b=40),
        )

        # 일사량 비교 그래프
        fig_solar = go.Figure()
        for i, (region, df) in enumerate(region_data.items()):
            fig_solar.add_trace(go.Scatter(
                x=df["month_kr"], y=df["solar"],
                mode="lines+markers+text", name=region,
                line=dict(color=region_colors[i], width=2.5),
                marker=dict(size=7),
                fill="tozeroy", fillcolor=f"rgba({','.join(str(int(c*255)) for c in px.colors.hex_to_rgb(region_colors[i]))},0.06)"
                    if False else None,
            ))
        fig_solar.update_layout(
            title=dict(text="☀️ 월별 평균 일사량 비교 (NASA POWER)", font=dict(size=15, color="#1B2D24")),
            xaxis_title="월", yaxis_title="일사량 (MJ/m²/day)",
            height=320, paper_bgcolor="white", plot_bgcolor="#FAFAFA",
            legend=dict(orientation="h", y=1.15),
            margin=dict(l=40, r=20, t=50, b=40),
        )

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(fig_temp, use_container_width=True)
            st.plotly_chart(fig_solar, use_container_width=True)
        with c2:
            st.plotly_chart(fig_humid, use_container_width=True)
            # 작물 생장 조건 참고표
            st.markdown(f"""
            <div class="card">
              <div class="card-title">🌿 {display_crop} 최적 생장 조건 <span class="tag-bio">생명과학</span></div>
              <table style="width:100%; font-size:13px; border-collapse:collapse;">
                <tr style="border-bottom:1px solid #eee;">
                  <td style="padding:8px; color:#777;">최적 기온</td>
                  <td style="padding:8px; font-weight:700;">{crop_info['opt_temp'][0]}~{crop_info['opt_temp'][1]} °C</td>
                </tr>
                <tr style="border-bottom:1px solid #eee;">
                  <td style="padding:8px; color:#777;">최적 습도</td>
                  <td style="padding:8px; font-weight:700;">{crop_info['opt_humid'][0]}~{crop_info['opt_humid'][1]} %</td>
                </tr>
                <tr style="border-bottom:1px solid #eee;">
                  <td style="padding:8px; color:#777;">최적 일사량</td>
                  <td style="padding:8px; font-weight:700;">{opt_solar_mj_str(crop_info)}</td>
                </tr>
                <tr>
                  <td style="padding:8px; color:#777;">생장 기간</td>
                  <td style="padding:8px; font-weight:700;">{crop_info['growth_days']}일</td>
                </tr>
              </table>
            </div>
            """, unsafe_allow_html=True)




# ════════════════════════════════════════════════════════
# TAB 3 — 최적화 설계 (자기주도 탐구형 v2)
# ════════════════════════════════════════════════════════
with tab3:
    st.markdown("""
    <div class="step-badge">⚡ 3차시 · 스마트팜 최적화 설계</div>
    <div style="font-size:13px; color:#555; margin-bottom:4px;">
      <span class="tag-math">수학</span>&nbsp;<span class="tag-physics">물리</span>&nbsp;<span class="tag-bio">생명과학</span>&nbsp;
      가중치 설정 → 가설 수립 → 데이터 탐색 → 결과 확인
    </div>
    """, unsafe_allow_html=True)

    if not region_data:
        st.info("👈 사이드바에서 지역을 선택하고 **분석 시작**을 누르세요.")
    else:
        region_list = list(region_data.keys())
        region_colors = ["#2D6A4F", "#F4A261", "#457B9D"]
        crop_info = CROPS[display_crop]

        # ══════════════════════════════════════════════════════
        # STEP 1: 가중치 설정 (가장 먼저)
        # ══════════════════════════════════════════════════════
        with st.expander("⚖️ STEP 1 · 가중치 설정", expanded=True):
            st.markdown(f"""
            <div class="card" style="border-left-color:#F4A261;">
              <div class="card-title">⚖️ 어떤 환경 요소가 가장 중요할까요?</div>
              <div style="font-size:13px; color:#555; line-height:2.0;">
                스마트팜 입지를 결정할 때 아래 세 요소 중 무엇이 가장 중요한지 모둠에서 토론하세요.<br>
                <b>세 가중치의 합이 100이 되도록</b> 슬라이더를 조절하세요.
              </div>
              <table style="width:100%; font-size:12px; margin-top:12px; border-collapse:collapse;">
                <tr style="background:#f8f8f8;">
                  <th style="padding:8px; text-align:left;">요소</th>
                  <th style="padding:8px; text-align:left;">식물 생장과의 관계</th>
                  <th style="padding:8px; text-align:left;">{display_crop} 최적 범위</th>
                </tr>
                <tr style="border-bottom:1px solid #eee;">
                  <td style="padding:8px;"><span class="tag-physics">물리</span> 🌡️ 기온</td>
                  <td style="padding:8px; color:#555;">효소 활성 조절 → 광합성·호흡 속도 결정<br>벗어나면 난방/냉방 비용 발생</td>
                  <td style="padding:8px; font-weight:700;">{crop_info['opt_temp'][0]}~{crop_info['opt_temp'][1]}°C</td>
                </tr>
                <tr style="border-bottom:1px solid #eee;">
                  <td style="padding:8px;"><span class="tag-physics">물리</span> ☀️ 일사량</td>
                  <td style="padding:8px; color:#555;">빛 에너지 → 광합성 ATP·NADPH 생성<br>부족하면 LED 보광 비용 발생</td>
                  <td style="padding:8px; font-weight:700;">{opt_solar_mj_str(crop_info)}</td>
                </tr>
                <tr>
                  <td style="padding:8px;"><span class="tag-bio">생명과학</span> 💧 습도</td>
                  <td style="padding:8px; color:#555;">기공 개폐 → CO₂ 흡수·증산작용 조절<br>과다 시 병해, 부족 시 수분 스트레스</td>
                  <td style="padding:8px; font-weight:700;">{crop_info['opt_humid'][0]}~{crop_info['opt_humid'][1]}%</td>
                </tr>
              </table>
            </div>
            """, unsafe_allow_html=True)

            wc1, wc2, wc3 = st.columns(3)
            with wc1:
                st.markdown("<div style='text-align:center; font-weight:700; color:#E76F51; margin-bottom:4px;'>🌡️ 기온 가중치</div>", unsafe_allow_html=True)
                w_temp = st.slider("기온", 0, 100, 40, 5, key="w_temp", label_visibility="collapsed")
            with wc2:
                st.markdown("<div style='text-align:center; font-weight:700; color:#F4A261; margin-bottom:4px;'>☀️ 일사량 가중치</div>", unsafe_allow_html=True)
                w_solar = st.slider("일사량", 0, 100, 35, 5, key="w_solar", label_visibility="collapsed")
            with wc3:
                st.markdown("<div style='text-align:center; font-weight:700; color:#457B9D; margin-bottom:4px;'>💧 습도 가중치</div>", unsafe_allow_html=True)
                w_humid = st.slider("습도", 0, 100, 25, 5, key="w_humid", label_visibility="collapsed")

            total_w = w_temp + w_solar + w_humid

            # 가중치 합계 시각적 게이지
            bar_color = "#52B788" if total_w == 100 else ("#E76F51" if total_w > 100 else "#F4A261")
            fill_pct = min(100, total_w)
            st.markdown(f"""
            <div style="margin: 12px 0 4px;">
              <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
                <span style="font-weight:700;">합계: <span style="color:{bar_color}; font-size:16px;">{total_w}</span> / 100</span>
                <span style="color:#999;">{'✅ 완료!' if total_w==100 else ('▼ %d 줄이세요' % (total_w-100) if total_w>100 else '▲ %d 더 추가하세요' % (100-total_w))}</span>
              </div>
              <div style="background:#eee; border-radius:6px; height:10px;">
                <div style="background:{bar_color}; width:{fill_pct}%; height:10px; border-radius:6px; transition:width 0.3s;"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            if total_w == 100:
                st.session_state["weights"] = (w_temp/100, w_solar/100, w_humid/100)
                st.session_state["weights_set"] = True

                # 가중치 1위 요소 강조
                top_factor = max([("기온", w_temp), ("일사량", w_solar), ("습도", w_humid)], key=lambda x: x[1])
                st.markdown(f"""
                <div class="info-block" style="margin-top:10px;">
                  ✅ 설정 완료! 우리 모둠이 가장 중요하게 본 요소:
                  <b style="font-size:16px;">{top_factor[0]} ({top_factor[1]}%)</b><br>
                  이 선택을 바탕으로 아래 STEP 2에서 가설을 작성하세요.
                </div>
                """, unsafe_allow_html=True)

                w_reason = st.text_area(
                    "📝 이 가중치를 선택한 이유 (모둠 토론 후 기록)",
                    placeholder=f"예) {top_factor[0]}을 가장 중요하게 본 이유는...",
                    height=72, key="w_reason"
                )
            else:
                st.session_state["weights_set"] = False
                st.markdown("""
                <div class="warning-block">
                  ⚠️ 합계가 100이 되어야 다음 단계로 진행할 수 있습니다.
                </div>""", unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════
        # STEP 2: 가설 수립 (가중치 기반으로 유도)
        # ══════════════════════════════════════════════════════
        weights_set = st.session_state.get("weights_set", False)

        with st.expander(
            "📝 STEP 2 · 가설 수립" + (" ✅" if weights_set else " 🔒 STEP 1 완료 후 진행"),
            expanded=False
        ):
            if not weights_set:
                st.markdown('<div class="warning-block">🔒 STEP 1에서 가중치 합계를 100으로 맞춰주세요.</div>', unsafe_allow_html=True)
            else:
                wt, ws, wh = st.session_state.get("weights", (0.4, 0.35, 0.25))
                top_w = max([("기온", wt), ("일사량", ws), ("습도", wh)], key=lambda x: x[1])
                top_name = top_w[0]
                top_emoji = {"기온": "🌡️", "일사량": "☀️", "습도": "💧"}[top_name]
                top_opt = {
                    "기온":   f"{crop_info['opt_temp'][0]}~{crop_info['opt_temp'][1]}°C",
                    "일사량": opt_solar_mj_str(crop_info),
                    "습도":   f"{crop_info['opt_humid'][0]}~{crop_info['opt_humid'][1]}%",
                }[top_name]

                st.markdown(f"""
                <div class="card" style="border-left-color:#52B788;">
                  <div class="card-title">📝 내 가중치를 바탕으로 가설을 세워보세요</div>
                  <div style="font-size:13px; color:#555; line-height:2.0;">
                    우리 모둠은 <b>{top_emoji} {top_name}({int(top_w[1]*100)}%)</b>을 가장 중요하게 설정했어요.<br>
                    그렇다면 <b>{top_name}</b>이 {display_crop}의 최적 조건({top_opt})에 가장 잘 맞는 지역이 유리하겠죠?<br>
                    아래 힌트를 보고 가설을 완성해보세요.
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # 가설 작성을 위한 힌트 — 해당 변인의 지역별 연평균값만 보여줌
                st.markdown(f"##### {top_emoji} {top_name} 힌트 — 지역별 연평균값")
                hint_cols = st.columns(len(region_list))
                for i, (region, df) in enumerate(region_data.items()):
                    with hint_cols[i]:
                        if top_name == "기온":
                            val = f"{df['temp'].mean():.1f}°C"
                            opt_mid = sum(crop_info['opt_temp']) / 2
                            gap = abs(df['temp'].mean() - opt_mid)
                            comment = "✅ 최적에 가까움" if gap < 3 else ("⚠️ 다소 차이" if gap < 6 else "❌ 많이 벗어남")
                        elif top_name == "일사량":
                            val = f"{df['solar'].mean():.1f} MJ/m²"
                            opt_mid = sum(crop_info['opt_solar']) / 2 / 11.6
                            gap = abs(df['solar'].mean() - opt_mid)
                            comment = "✅ 최적에 가까움" if gap < 2 else ("⚠️ 다소 차이" if gap < 4 else "❌ 많이 벗어남")
                        else:
                            val = f"{df['humid'].mean():.0f}%"
                            opt_mid = sum(crop_info['opt_humid']) / 2
                            gap = abs(df['humid'].mean() - opt_mid)
                            comment = "✅ 최적에 가까움" if gap < 5 else ("⚠️ 다소 차이" if gap < 10 else "❌ 많이 벗어남")

                        c_color = "#52B788" if "✅" in comment else ("#F4A261" if "⚠️" in comment else "#E76F51")
                        st.markdown(f"""
                        <div class="card" style="text-align:center; border-left-color:{c_color};">
                          <div style="font-weight:700; font-size:15px; color:#2D6A4F;">📍 {region}</div>
                          <div style="font-size:22px; font-weight:700; margin:8px 0;">{val}</div>
                          <div style="font-size:12px; color:{c_color}; font-weight:600;">{comment}</div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("---")

                # 가설 문장 완성 — 빈칸 채우기 형식
                st.markdown("##### ✏️ 가설 문장을 완성해보세요")
                st.markdown(f"""
                <div style="background:#F0F7F4; border-radius:10px; padding:16px 20px; font-size:14px; line-height:2.2; border:1px dashed #52B788;">
                  우리 모둠은 <b>{top_emoji} {top_name}</b>이 스마트팜 입지에서 가장 중요한 요소라고 판단했다.<br>
                  따라서 {top_name}이 {display_crop}의 최적 범위({top_opt})에 가장 가까운 지역이
                  스마트팜 운영에 가장 적합할 것이다.
                </div>
                """, unsafe_allow_html=True)

                hypo_region = st.selectbox(
                    f"❓ 위 힌트를 보고, {top_name} 조건이 가장 좋은 지역은?",
                    ["(선택하세요)"] + region_list,
                    key="hypo_best"
                )
                hypo_reason = st.text_area(
                    "📌 그렇게 생각한 이유 (위 힌트 수치를 활용해서 작성하세요)",
                    placeholder=f"예) {region_list[0]}은 연평균 {top_name}이 최적 범위와 가장 가깝기 때문에...",
                    height=90, key="hypo_reason"
                )
                hypo_worst = st.selectbox(
                    "❓ 반대로 가장 불리할 것 같은 지역은?",
                    ["(선택하세요)"] + region_list,
                    key="hypo_worst"
                )

                hypo_done = hypo_region != "(선택하세요)" and hypo_reason.strip() != ""
                if hypo_done:
                    st.session_state["hypo_done"] = True
                    st.markdown(f"""
                    <div class="info-block">
                      ✅ 가설 작성 완료!<br>
                      가설: <b>{hypo_region}</b>이 {top_name} 조건이 가장 유리하여 최적 입지일 것이다.<br>
                      STEP 3에서 다른 변인 데이터도 확인하고 검증해보세요.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.session_state["hypo_done"] = False
                    st.markdown('<div class="warning-block">⚠️ 지역 선택과 이유를 모두 작성해야 STEP 3로 넘어갈 수 있습니다.</div>', unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════
        # STEP 3: 데이터 탐색 (가설 검증용)
        # ══════════════════════════════════════════════════════
        hypo_done = st.session_state.get("hypo_done", False)

        with st.expander(
            "🔬 STEP 3 · 데이터 탐색 & 가설 검증" + (" ✅" if hypo_done else " 🔒 STEP 2 완료 후 진행"),
            expanded=False
        ):
            if not hypo_done:
                st.markdown('<div class="warning-block">🔒 STEP 2에서 가설을 먼저 작성해주세요.</div>', unsafe_allow_html=True)
            else:
                hypo_region = st.session_state.get("hypo_best", "")
                wt, ws, wh = st.session_state.get("weights", (0.4, 0.35, 0.25))

                st.markdown(f"""
                <div class="info-block" style="margin-bottom:16px;">
                  🔎 우리 가설: <b>"{hypo_region}"</b>이 최적 입지일 것이다.<br>
                  지금부터 나머지 변인 데이터도 탐색하며 가설을 검증해보세요.
                </div>
                """, unsafe_allow_html=True)

                explore_item = st.radio(
                    "📊 탐색할 데이터 선택",
                    ["🌡️ 기온", "☀️ 일사량", "💧 습도", "💰 에너지 비용"],
                    horizontal=True, key="explore_item"
                )

                if explore_item == "🌡️ 기온":
                    fig_e = go.Figure()
                    fig_e.add_hrect(y0=crop_info["opt_temp"][0], y1=crop_info["opt_temp"][1],
                                    fillcolor="rgba(82,183,136,0.15)", line_width=0,
                                    annotation_text=f"최적 기온 ({crop_info['opt_temp'][0]}~{crop_info['opt_temp'][1]}°C)",
                                    annotation_font_size=11)
                    for i, (region, df) in enumerate(region_data.items()):
                        fig_e.add_trace(go.Scatter(x=df["month_kr"], y=df["temp"],
                            mode="lines+markers", name=region,
                            line=dict(color=region_colors[i], width=2.5), marker=dict(size=8)))
                    fig_e.update_layout(title="월별 기온 — 초록 구간이 최적 범위",
                        xaxis_title="월", yaxis_title="기온 (°C)", height=300,
                        paper_bgcolor="white", plot_bgcolor="#FAFAFA",
                        legend=dict(orientation="h", y=1.15), margin=dict(l=40,r=20,t=50,b=40))
                    st.plotly_chart(fig_e, use_container_width=True)
                    st.markdown("""<div class="info-block">
                      🔍 <b>탐구 포인트:</b> 최적 범위를 벗어난 달이 많은 지역은 난방·냉방 비용이 증가합니다.
                      내 가설의 지역은 몇 달이나 최적 범위 안에 있나요?
                    </div>""", unsafe_allow_html=True)

                elif explore_item == "☀️ 일사량":
                    fig_e = go.Figure()
                    for i, (region, df) in enumerate(region_data.items()):
                        fig_e.add_trace(go.Bar(x=df["month_kr"], y=df["solar"],
                            name=region, marker_color=region_colors[i], opacity=0.8))
                    fig_e.update_layout(title="월별 일사량 (MJ/m²/day)",
                        xaxis_title="월", yaxis_title="일사량", height=300, barmode="group",
                        paper_bgcolor="white", plot_bgcolor="#FAFAFA",
                        legend=dict(orientation="h", y=1.15), margin=dict(l=40,r=20,t=50,b=40))
                    st.plotly_chart(fig_e, use_container_width=True)
                    led_cols = st.columns(len(region_data))
                    for i, (region, df) in enumerate(region_data.items()):
                        with led_cols[i]:
                            need_months = df[df["led_need"] > 30]["month_kr"].tolist()
                            st.markdown(f"""<div class="card" style="text-align:center;">
                              <div style="font-weight:700; color:#2D6A4F;">📍 {region}</div>
                              <div style="font-size:11px; color:#777; margin:4px 0;">LED 보광 필요 월</div>
                              <div style="font-size:13px; font-weight:700; color:#F4A261;">
                                {', '.join(need_months) if need_months else '없음 ✅'}
                              </div>
                            </div>""", unsafe_allow_html=True)
                    st.markdown("""<div class="info-block">
                      🔍 <b>탐구 포인트:</b> LED 보광이 필요한 달이 많을수록 전기 비용이 올라갑니다.
                      일사량과 에너지 비용은 어떤 관계가 있을까요?
                    </div>""", unsafe_allow_html=True)

                elif explore_item == "💧 습도":
                    fig_e = go.Figure()
                    fig_e.add_hrect(y0=crop_info["opt_humid"][0], y1=crop_info["opt_humid"][1],
                                    fillcolor="rgba(69,123,157,0.12)", line_width=0,
                                    annotation_text=f"최적 습도 ({crop_info['opt_humid'][0]}~{crop_info['opt_humid'][1]}%)",
                                    annotation_font_size=11)
                    for i, (region, df) in enumerate(region_data.items()):
                        fig_e.add_trace(go.Scatter(x=df["month_kr"], y=df["humid"],
                            mode="lines+markers", name=region,
                            line=dict(color=region_colors[i], width=2.5), marker=dict(size=8)))
                    fig_e.update_layout(title="월별 습도 — 파란 구간이 최적 범위",
                        xaxis_title="월", yaxis_title="습도 (%)", height=300,
                        paper_bgcolor="white", plot_bgcolor="#FAFAFA",
                        legend=dict(orientation="h", y=1.15), margin=dict(l=40,r=20,t=50,b=40))
                    st.plotly_chart(fig_e, use_container_width=True)
                    st.markdown("""<div class="info-block">
                      🔍 <b>탐구 포인트:</b> 습도가 너무 높으면 병해 위험, 너무 낮으면 증산 스트레스가 생깁니다.
                      어느 지역의 습도가 가장 안정적으로 최적 범위 안에 있나요?
                    </div>""", unsafe_allow_html=True)

                else:  # 에너지 비용
                    fig_e = go.Figure()
                    for i, (region, df) in enumerate(region_data.items()):
                        h, c = calc_energy(df, display_crop, display_area)
                        fig_e.add_trace(go.Bar(
                            name=region,
                            x=["난방 비용", "냉방 비용", "총 비용"],
                            y=[h, c, h+c],
                            marker_color=region_colors[i],
                            text=[f"{v:,}만원" for v in [h, c, h+c]],
                            textposition="outside",
                        ))
                    fig_e.update_layout(title=f"예상 에너지 비용 ({display_area:,}m² 기준, 만원/년)",
                        barmode="group", height=300,
                        paper_bgcolor="white", plot_bgcolor="#FAFAFA",
                        legend=dict(orientation="h", y=1.15), margin=dict(l=40,r=20,t=50,b=40))
                    st.plotly_chart(fig_e, use_container_width=True)
                    st.markdown("""<div class="info-block">
                      🔍 <b>탐구 포인트:</b> 난방 비용이 높다는 것은 겨울 기온이 낮다는 의미입니다.
                      기온 가중치를 높게 설정한 모둠은 이 비용을 중요한 판단 근거로 삼을 수 있어요.
                    </div>""", unsafe_allow_html=True)

                st.markdown("---")

                # 내 가중치로 계산된 점수표 (순위 숨김)
                st.markdown("##### 📋 내 가중치로 계산한 항목별 점수")
                scored_step3 = []
                for region, df in region_data.items():
                    scored_step3.append({
                        "region": region,
                        "기온 점수": round(df["temp_score"].mean(), 1),
                        "일사량 점수": round(df["solar_score"].mean(), 1),
                        "습도 점수": round(df["humid_score"].mean(), 1),
                        "종합 점수": round(
                            df["temp_score"].mean()*wt +
                            df["solar_score"].mean()*ws +
                            df["humid_score"].mean()*wh, 1),
                    })

                hdr = st.columns([2,2,2,2,2])
                for col, h in zip(hdr, ["지역","기온 점수","일사량 점수","습도 점수","종합 점수(내 가중치)"]):
                    col.markdown(f"<b style='font-size:12px; color:#2D6A4F;'>{h}</b>", unsafe_allow_html=True)
                st.markdown("<hr style='margin:4px 0 8px;'>", unsafe_allow_html=True)
                for s in scored_step3:
                    row = st.columns([2,2,2,2,2])
                    row[0].markdown(f"**📍 {s['region']}**")
                    row[1].markdown(f"{s['기온 점수']}점")
                    row[2].markdown(f"{s['일사량 점수']}점")
                    row[3].markdown(f"{s['습도 점수']}점")
                    row[4].markdown(f"**{s['종합 점수']}점**")

                st.markdown("---")
                st.markdown("##### ✏️ 가설 검증 기록")
                fc1, fc2 = st.columns(2)
                with fc1:
                    st.text_area("📊 데이터를 탐색하며 발견한 점",
                        placeholder="예) 제주는 기온은 좋지만 여름 습도가 매우 높아 습도 점수가 낮았다.",
                        height=90, key="finding")
                with fc2:
                    st.text_area("🔄 가설과 비교 — 예상과 다른 점이 있었나요?",
                        placeholder="예) 기온만 보면 제주가 유리했지만, 종합 점수는 예상과 달랐다.",
                        height=90, key="hypo_check")
                st.markdown('<div class="info-block">✅ 기록 완료 후 <b>4차시 결과 발표</b> 탭으로 넘어가세요!</div>', unsafe_allow_html=True)


# TAB 4 — 결과 발표 (자기주도 탐구형)
# ════════════════════════════════════════════════════════
with tab4:
    st.markdown("""
    <div class="step-badge">🏆 4차시 · 결과 발표</div>
    <div style="font-size:13px; color:#555; margin-bottom:20px;">
      모둠 결론 정리 → 최적 입지 선정 근거 작성 → 발표 준비 → 다른 모둠과 비교
    </div>
    """, unsafe_allow_html=True)

    if not region_data:
        st.info("👈 사이드바에서 지역을 선택하고 **분석 시작**을 누르세요.")
    else:
        # ── 모둠 결론 작성 ──────────────────────────────────────────
        st.markdown("""
        <div class="card" style="border-left-color:#2D6A4F;">
          <div class="card-title">✏️ STEP 1 · 모둠 최종 결론 작성</div>
          <div style="font-size:13px; color:#555;">
            3차시에서 탐색한 데이터를 바탕으로 모둠의 최종 결론을 작성하세요.
            점수만이 아니라 <b>데이터 근거</b>를 함께 제시해야 합니다.
          </div>
        </div>
        """, unsafe_allow_html=True)

        region_list = list(region_data.keys())
        fc1, fc2 = st.columns(2)
        with fc1:
            final_pick = st.selectbox(
                "🏆 우리 모둠이 선정한 최적 입지",
                ["(선택하세요)"] + region_list, key="final_pick"
            )
            final_reason_data = st.text_area(
                "📊 데이터 근거 (수치를 포함하여 작성)",
                placeholder="예) 제주는 연평균 기온이 16.2°C로 상추 최적 온도(15~20°C)와 일치하며, 난방 비용이 세 지역 중 가장 낮은 320만원이었다.",
                height=110, key="final_reason_data"
            )
        with fc2:
            final_weak = st.text_area(
                "⚠️ 선정 지역의 한계점 및 보완 방안",
                placeholder="예) 여름 습도가 80%를 넘어 병해 위험이 있다. 환기 시스템을 강화하면 보완 가능하다.",
                height=110, key="final_weak"
            )
            final_weight_reason = st.text_area(
                "⚖️ 우리 모둠의 가중치 설정 근거",
                placeholder="예) 기온을 40%로 설정한 이유는 난방·냉방 비용이 장기 수익성에 가장 큰 영향을 미치기 때문이다.",
                height=110, key="final_weight_reason"
            )

        st.markdown("---")

        # ── 발표 자료 미리보기 ──────────────────────────────────────
        st.markdown("""
        <div class="card" style="border-left-color:#52B788;">
          <div class="card-title">📊 STEP 2 · 발표 데이터 확인</div>
          <div style="font-size:13px; color:#555;">
            아래 그래프를 발표 근거로 활용하세요. 발표 시 구체적인 수치를 언급하세요.
          </div>
        </div>
        """, unsafe_allow_html=True)

        # 내 가중치 또는 기본값으로 점수 계산
        wt, ws, wh = st.session_state.get("weights", (0.40, 0.35, 0.25))
        region_colors = ["#2D6A4F", "#F4A261", "#457B9D"]

        scored = []
        for region, df in region_data.items():
            my_score = (
                df["temp_score"].mean()  * wt +
                df["solar_score"].mean() * ws +
                df["humid_score"].mean() * wh
            )
            heating, cooling = calc_energy(df, display_crop, display_area)
            scored.append({
                "region": region, "df": df,
                "my_score": round(my_score, 1),
                "temp_s":  round(df["temp_score"].mean(), 1),
                "solar_s": round(df["solar_score"].mean(), 1),
                "humid_s": round(df["humid_score"].mean(), 1),
                "heating": heating, "cooling": cooling,
            })

        # 가중치 표시
        st.markdown(f"""
        <div class="info-block">
          📐 <b>적용된 가중치:</b> 기온 {int(wt*100)}% · 일사량 {int(ws*100)}% · 습도 {int(wh*100)}%
          {"(3차시에서 직접 설정한 값)" if st.session_state.get("weights_set") else "(기본값 — 3차시에서 가중치를 설정하면 반영됩니다)"}
        </div>
        """, unsafe_allow_html=True)

        # 항목별 비교 레이더
        fig_radar = go.Figure()
        for i, s in enumerate(scored):
            fig_radar.add_trace(go.Scatterpolar(
                r=[s["temp_s"], s["solar_s"], s["humid_s"], s["my_score"]],
                theta=["기온 적합도", "일사량 적합도", "습도 적합도", "종합 점수"],
                fill="toself", name=s["region"],
                line=dict(color=region_colors[i]), opacity=0.7,
            ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            title=dict(text="항목별 강약점 비교", font=dict(size=14)),
            height=320, paper_bgcolor="white",
            legend=dict(orientation="h", y=-0.12),
            margin=dict(l=20, r=20, t=50, b=40),
        )

        # 월별 종합 점수 꺾은선 (계절별 흐름 파악)
        fig_monthly = go.Figure()
        for i, s in enumerate(scored):
            fig_monthly.add_trace(go.Scatter(
                x=s["df"]["month_kr"], y=s["df"]["total_score"],
                mode="lines+markers", name=s["region"],
                line=dict(color=region_colors[i], width=2.5),
                marker=dict(size=8),
            ))
        fig_monthly.add_hline(y=70, line_dash="dot", line_color="#aaa",
                              annotation_text="기준선 70점", annotation_font_size=11)
        fig_monthly.update_layout(
            title=dict(text="월별 생장 적합도 점수 추이", font=dict(size=14)),
            xaxis_title="월", yaxis_title="적합도 점수",
            yaxis=dict(range=[0, 110]),
            height=280, paper_bgcolor="white", plot_bgcolor="#FAFAFA",
            legend=dict(orientation="h", y=1.15),
            margin=dict(l=40, r=20, t=50, b=40),
        )

        pc1, pc2 = st.columns([2, 3])
        with pc1:
            st.plotly_chart(fig_radar, use_container_width=True)
        with pc2:
            st.plotly_chart(fig_monthly, use_container_width=True)

        # 지역별 핵심 수치 카드 (순위 없이)
        st.markdown("##### 📋 지역별 핵심 수치")
        ccols = st.columns(len(scored))
        for i, (col, s) in enumerate(zip(ccols, scored)):
            with col:
                df_r = s["df"]
                best_month  = df_r.loc[df_r["total_score"].idxmax(), "month_kr"]
                worst_month = df_r.loc[df_r["total_score"].idxmin(), "month_kr"]
                avg_led = df_r["led_need"].mean()
                st.markdown(f"""
                <div class="card">
                  <div style="font-size:16px; font-weight:700; color:#2D6A4F; margin-bottom:10px;">
                    📍 {s['region']}
                  </div>
                  <div style="font-size:13px; line-height:2.1;">
                    <b>종합 점수:</b> {s['my_score']}점<br>
                    <b>기온 점수:</b> {s['temp_s']}점<br>
                    <b>일사량 점수:</b> {s['solar_s']}점<br>
                    <b>습도 점수:</b> {s['humid_s']}점<br>
                    <b>🌟 최적 월:</b> {best_month}<br>
                    <b>📉 취약 월:</b> {worst_month}<br>
                    <b>💡 보광 필요:</b> 연평균 {avg_led:.0f}%<br>
                    <b>💰 에너지 비용:</b> {s['heating']+s['cooling']:,}만원/년
                  </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # ── 모둠 간 토론 ────────────────────────────────────────────
        st.markdown("""
        <div class="card" style="border-left-color:#F4A261;">
          <div class="card-title">💬 STEP 3 · 발표 후 토론 질문</div>
          <div style="font-size:14px; line-height:2.4; color:#333;">
            1. 같은 데이터를 봤는데 모둠마다 결론이 다르다면, 그 이유는 무엇일까?
               <span class="tag-math">수학</span><br>
            2. 가중치를 다르게 설정한 모둠과 비교할 때 어느 쪽 판단이 더 합리적인가?
               <span class="tag-math">수학</span><br>
            3. 기후변화로 10년 후 기온이 1~2°C 상승한다면, 지금의 선택이 달라질까?
               <span class="tag-bio">생명과학</span><br>
            4. 에너지 비용을 줄이기 위해 물리적으로 어떤 방법을 사용할 수 있을까?
               <span class="tag-physics">물리</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── 최종 결론 공개 ───────────────────────────────────────────
        reveal_col1, reveal_col2 = st.columns(2)
        with reveal_col1:
            if st.button("🔍 내 가중치 기준 순위 공개", key="reveal_btn"):
                st.session_state["reveal_my"] = True
        with reveal_col2:
            if st.button("🌍 절대적 적합도 기준 정답 공개", key="reveal_abs_btn"):
                st.session_state["reveal_abs"] = True

        # ── 내 가중치 기준 순위 ──
        if st.session_state.get("reveal_my"):
            scored_sorted = sorted(scored, key=lambda x: x["my_score"], reverse=True)
            best_my = scored_sorted[0]
            wt, ws, wh = st.session_state.get("weights", (0.4, 0.35, 0.25))

            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#2D6A4F,#52B788);
                        border-radius:14px; padding:22px 28px; margin:12px 0;
                        color:white; text-align:center;">
              <div style="font-size:11px; letter-spacing:2px; opacity:0.8; margin-bottom:4px;">
                📐 내 가중치 기준 (기온 {int(wt*100)}% · 일사량 {int(ws*100)}% · 습도 {int(wh*100)}%)
              </div>
              <div style="font-size:28px; font-weight:900;">📍 {best_my['region']}</div>
              <div style="font-size:38px; font-weight:700;">{best_my['my_score']}점</div>
              <div style="font-size:12px; opacity:0.85; margin-top:4px;">
                기온 {best_my['temp_s']}점 · 일사량 {best_my['solar_s']}점 · 습도 {best_my['humid_s']}점
              </div>
            </div>
            """, unsafe_allow_html=True)

            fig_my = go.Figure(go.Bar(
                x=[s["my_score"] for s in scored_sorted],
                y=[s["region"] for s in scored_sorted],
                orientation="h",
                marker=dict(color=[s["my_score"] for s in scored_sorted],
                            colorscale=[[0,"#F4A261"],[0.5,"#52B788"],[1,"#2D6A4F"]]),
                text=[f"{s['my_score']}점" for s in scored_sorted],
                textposition="outside",
            ))
            fig_my.update_layout(
                title=f"내 가중치 기준 순위",
                xaxis=dict(range=[0,110]), height=max(160, len(scored)*75),
                paper_bgcolor="white", plot_bgcolor="#FAFAFA",
                margin=dict(l=20, r=60, t=40, b=20),
            )
            st.plotly_chart(fig_my, use_container_width=True)

            if final_pick != "(선택하세요)":
                my_pick_score = next((s["my_score"] for s in scored if s["region"] == final_pick), None)
                if final_pick == scored_sorted[0]["region"]:
                    st.markdown(f"""<div class="info-block">
                      🎯 우리 모둠의 선택 <b>{final_pick}</b>이 내 가중치 기준으로도 1위입니다!
                      가설과 분석이 일치했어요.
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="warning-block">
                      🤔 우리 모둠은 <b>{final_pick} ({my_pick_score}점)</b>을 선택했지만,
                      내 가중치 기준 1위는 <b>{scored_sorted[0]['region']} ({scored_sorted[0]['my_score']}점)</b>입니다.
                      가중치 설정이 달랐다면 결론도 달라졌을까요?
                    </div>""", unsafe_allow_html=True)

        # ── 절대적 적합도 기준 정답 ──
        if st.session_state.get("reveal_abs"):
            # 절대 적합도: calc_suitability의 고정 가중치(기온40·일사량35·습도25) + 에너지 비용 반영
            abs_scored = []
            for region, df in region_data.items():
                h, c = calc_energy(df, display_crop, display_area)
                abs_grow  = df["total_score"].mean()          # 고정 가중치 기반 생장 점수
                abs_led   = 100 - df["led_need"].mean()       # LED 보광 불필요 점수
                max_cost  = max(sum(calc_energy(d, display_crop, display_area)) for d in region_data.values())
                abs_cost  = max(0, 100 - ((h+c) / (max_cost+1)) * 60)
                abs_total = round(abs_grow * 0.50 + abs_led * 0.30 + abs_cost * 0.20, 1)
                abs_scored.append({
                    "region": region,
                    "생장 점수": round(abs_grow, 1),
                    "보광 효율": round(abs_led, 1),
                    "비용 효율": round(abs_cost, 1),
                    "절대 적합도": abs_total,
                    "heating": h, "cooling": c,
                })
            abs_scored.sort(key=lambda x: x["절대 적합도"], reverse=True)
            abs_best = abs_scored[0]

            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1B2D24,#2D6A4F);
                        border-radius:14px; padding:22px 28px; margin:12px 0;
                        color:white; text-align:center;">
              <div style="font-size:11px; letter-spacing:2px; opacity:0.7; margin-bottom:4px;">
                🌍 절대적 스마트팜 적합도 (생장 50% · 보광효율 30% · 비용효율 20%)
              </div>
              <div style="font-size:28px; font-weight:900;">📍 {abs_best['region']}</div>
              <div style="font-size:38px; font-weight:700;">{abs_best['절대 적합도']}점</div>
              <div style="font-size:12px; opacity:0.85; margin-top:4px;">
                생장 적합도 {abs_best['생장 점수']}점 · 보광 효율 {abs_best['보광 효율']}점 · 비용 효율 {abs_best['비용 효율']}점
              </div>
            </div>
            """, unsafe_allow_html=True)

            # 절대 적합도 기준 상세 비교 차트
            fig_abs = make_subplots(rows=1, cols=2,
                subplot_titles=["절대 적합도 종합 순위", "항목별 점수 비교"],
                horizontal_spacing=0.12)

            region_colors_local = ["#2D6A4F", "#F4A261", "#457B9D"]
            fig_abs.add_trace(go.Bar(
                x=[s["절대 적합도"] for s in abs_scored],
                y=[s["region"] for s in abs_scored],
                orientation="h",
                marker=dict(color=[s["절대 적합도"] for s in abs_scored],
                            colorscale=[[0,"#F4A261"],[0.5,"#52B788"],[1,"#1B2D24"]]),
                text=[f"{s['절대 적합도']}점" for s in abs_scored],
                textposition="outside",
                showlegend=False,
            ), row=1, col=1)

            cats = ["생장 점수", "보광 효율", "비용 효율"]
            for i, s in enumerate(abs_scored):
                fig_abs.add_trace(go.Bar(
                    name=s["region"],
                    x=cats,
                    y=[s["생장 점수"], s["보광 효율"], s["비용 효율"]],
                    marker_color=region_colors_local[i % 3],
                    text=[f"{v:.0f}" for v in [s["생장 점수"], s["보광 효율"], s["비용 효율"]]],
                    textposition="outside",
                ), row=1, col=2)

            fig_abs.update_layout(
                height=300, paper_bgcolor="white", plot_bgcolor="#FAFAFA",
                barmode="group", legend=dict(orientation="h", y=1.15),
                margin=dict(l=20, r=40, t=45, b=20),
            )
            fig_abs.update_xaxes(range=[0, 115], row=1, col=1)
            fig_abs.update_xaxes(range=[0, 115], row=1, col=2)  # 수정: col=2
            st.plotly_chart(fig_abs, use_container_width=True)

            # 내 선택 vs 절대 정답 비교
            if final_pick != "(선택하세요)":
                abs_pick_score = next((s["절대 적합도"] for s in abs_scored if s["region"] == final_pick), None)
                if final_pick == abs_best["region"]:
                    st.markdown(f"""<div class="info-block">
                      🏆 우리 모둠의 선택 <b>{final_pick}</b>이 절대적 적합도 기준으로도 최적 입지입니다!
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="warning-block">
                      🤔 절대적 기준 최적 입지는 <b>{abs_best['region']} ({abs_best['절대 적합도']}점)</b>이지만,
                      우리 모둠은 <b>{final_pick} ({abs_pick_score}점)</b>을 선택했습니다.
                    </div>""", unsafe_allow_html=True)

            # 내 가중치 vs 절대 순위 비교 인사이트
            if st.session_state.get("reveal_my") and st.session_state.get("reveal_abs"):
                my_sorted  = sorted(scored, key=lambda x: x["my_score"], reverse=True)
                abs_rank   = {s["region"]: i+1 for i, s in enumerate(abs_scored)}
                my_rank    = {s["region"]: i+1 for i, s in enumerate(my_sorted)}

                st.markdown("---")
                st.markdown("""
                <div class="card" style="border-left-color:#F4A261;">
                  <div class="card-title">🔬 심화 분석 · 내 가중치 vs 절대 기준 비교</div>
                """, unsafe_allow_html=True)
                diff_found = False
                for region in region_data.keys():
                    m_r = my_rank.get(region, "-")
                    a_r = abs_rank.get(region, "-")
                    if m_r != a_r:
                        diff_found = True
                        st.markdown(f"""
                        <div style="font-size:13px; padding:6px 0; border-bottom:1px solid #eee;">
                          📍 <b>{region}</b>: 내 가중치 순위 <b>{m_r}위</b> →
                          절대 기준 순위 <b>{a_r}위</b>
                          <span style="color:#888; font-size:12px;"> — 순위가 달라졌어요!</span>
                        </div>""", unsafe_allow_html=True)
                if not diff_found:
                    st.markdown("""<div class="info-block">
                      두 기준의 순위가 일치합니다! 내 가중치가 객관적 판단과 유사했어요.
                    </div>""", unsafe_allow_html=True)
                st.markdown("""
                  <div style="font-size:13px; color:#555; margin-top:10px; line-height:1.8;">
                    💡 순위 차이가 생긴 이유는 무엇일까요?<br>
                    내 가중치에서 상대적으로 낮게 설정한 요소가 실제로는 더 중요했던 것은 아닐까요?
                  </div>
                </div>""", unsafe_allow_html=True)
