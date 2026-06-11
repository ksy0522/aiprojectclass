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


# ── API 호출 함수 ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_openmeteo(lat, lon):
    """Open-Meteo API: 월평균 기온·습도 (과거 1년)"""
    end   = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    url = (
        f"https://api.open-meteo.com/v1/forecast"
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

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_nasa_power(lat, lon):
    """NASA POWER API: 월평균 일사량"""
    end   = datetime.now()
    start = end - timedelta(days=365)
    url = (
        f"https://power.larc.nasa.gov/api/temporal/monthly/point"
        f"?parameters=ALLSKY_SFC_SW_DWN"
        f"&community=AG"
        f"&longitude={lon}&latitude={lat}"
        f"&start={start.strftime('%Y%m')}&end={end.strftime('%Y%m')}"
        f"&format=JSON"
    )
    try:
        r = requests.get(url, timeout=20)
        data = r.json()
        values = data["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]
        months, solar = [], []
        for k, v in values.items():
            try:
                month = int(k[-2:])
                if 1 <= month <= 12 and v != -999:
                    months.append(month)
                    solar.append(v)
            except:
                pass
        if not months:
            return None
        solar_df = pd.DataFrame({"month": months, "solar": solar})
        solar_monthly = solar_df.groupby("month")["solar"].mean().reset_index()
        return solar_monthly
    except Exception as e:
        return None

def get_region_data(region):
    lat, lon = REGIONS[region]["lat"], REGIONS[region]["lon"]
    with st.spinner(f"🌐 {region} 기상 데이터 수집 중..."):
        meteo = fetch_openmeteo(lat, lon)
        nasa  = fetch_nasa_power(lat, lon)
    return meteo, nasa

def build_monthly_df(meteo, nasa):
    """기상·일사량 병합 DataFrame (12개월)"""
    if meteo is None:
        return None
    df = meteo.copy()
    if nasa is not None:
        df = df.merge(nasa, on="month", how="left")
    else:
        # fallback: 위도 기반 추정치
        df["solar"] = [2.5,3.2,4.1,5.0,5.8,5.5,4.8,5.2,4.5,3.8,2.8,2.3][:len(df)]
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
tab1, tab2, tab3, tab4 = st.tabs([
    "📖 1차시 · 수업 개요",
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

if not selected_regions:
    for tab in [tab2, tab3, tab4]:
        with tab:
            st.info("👈 사이드바에서 지역을 선택하고 **분석 시작** 버튼을 누르세요.")
else:
    # 자동 로드 또는 버튼 클릭 시 로드
    if run_btn or "region_data_cache" not in st.session_state:
        st.session_state["region_data_cache"] = {}
        for r in selected_regions:
            meteo, nasa = get_region_data(r)
            df = build_monthly_df(meteo, nasa)
            if df is not None:
                df = calc_suitability(df, selected_crop)
                df = calc_led_supplement(df, selected_crop)
                st.session_state["region_data_cache"][r] = df

    region_data = st.session_state.get("region_data_cache", {})


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
        crop_info = CROPS[selected_crop]
        fig_temp.add_hrect(
            y0=crop_info["opt_temp"][0], y1=crop_info["opt_temp"][1],
            fillcolor="rgba(82,183,136,0.12)", line_width=0,
            annotation_text=f"{selected_crop} 최적 기온 범위",
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
              <div class="card-title">🌿 {selected_crop} 최적 생장 조건 <span class="tag-bio">생명과학</span></div>
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
                  <td style="padding:8px; font-weight:700;">{crop_info['opt_solar'][0]}~{crop_info['opt_solar'][1]} W/m²</td>
                </tr>
                <tr>
                  <td style="padding:8px; color:#777;">생장 기간</td>
                  <td style="padding:8px; font-weight:700;">{crop_info['growth_days']}일</td>
                </tr>
              </table>
            </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════
# TAB 3 — 최적화 설계
# ════════════════════════════════════════════════════════
with tab3:
    st.markdown("""
    <div class="step-badge">⚡ 3차시 · 스마트팜 최적화 설계</div>
    <div style="font-size:13px; color:#555; margin-bottom:20px;">
      <span class="tag-math">수학</span>&nbsp;<span class="tag-physics">물리</span>&nbsp;
      생장 적합도 산출 · 에너지 비용 계산 · LED 보광 필요도 분석
    </div>
    """, unsafe_allow_html=True)

    if not region_data:
        st.info("👈 사이드바에서 지역을 선택하고 **분석 시작**을 누르세요.")
    else:
        for region, df in region_data.items():
            heating, cooling = calc_energy(df, selected_crop, farm_area)
            annual_score = df["total_score"].mean()

            st.markdown(f"""
            <div style="font-size:16px; font-weight:700; color:#2D6A4F;
                        border-bottom:2px solid #52B788; padding-bottom:8px; margin:20px 0 16px;">
              📍 {region}
            </div>
            """, unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            metrics = [
                ("작물 생장 적합도", f"{annual_score:.0f}", "점 / 100"),
                ("예상 난방 비용", f"{heating:,}", "만원 / 년"),
                ("예상 냉방 비용", f"{cooling:,}", "만원 / 년"),
                ("연간 에너지 비용", f"{heating+cooling:,}", "만원 / 년"),
            ]
            for col, (label, val, unit) in zip([c1,c2,c3,c4], metrics):
                with col:
                    st.markdown(f"""
                    <div class="metric-box">
                      <div class="metric-label">{label}</div>
                      <div class="metric-value">{val}</div>
                      <div class="metric-unit">{unit}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # 월별 적합도 + LED 보광 서브플롯
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=["월별 생장 적합도 점수", "월별 LED 보광 필요도 (%)"],
                horizontal_spacing=0.12
            )
            fig.add_trace(go.Bar(
                x=df["month_kr"], y=df["total_score"],
                name="적합도",
                marker=dict(
                    color=df["total_score"],
                    colorscale=[[0,"#E76F51"],[0.5,"#F4A261"],[1,"#52B788"]],
                    showscale=False,
                ),
                showlegend=False,
            ), row=1, col=1)
            fig.add_hline(y=70, line_dash="dot", line_color="#2D6A4F",
                          annotation_text="목표 기준선 (70점)", row=1, col=1)

            fig.add_trace(go.Bar(
                x=df["month_kr"], y=df["led_need"],
                name="LED 보광 필요도",
                marker=dict(
                    color=df["led_need"],
                    colorscale=[[0,"#52B788"],[0.5,"#F4A261"],[1,"#E76F51"]],
                    showscale=False,
                ),
                showlegend=False,
            ), row=1, col=2)

            fig.update_layout(
                height=300, paper_bgcolor="white", plot_bgcolor="#FAFAFA",
                margin=dict(l=30, r=20, t=40, b=30),
                font=dict(size=12),
            )
            fig.update_yaxes(range=[0,100], row=1, col=1)
            fig.update_yaxes(range=[0,100], row=1, col=2)
            st.plotly_chart(fig, use_container_width=True)

            # 항목별 월 평균 레이더 지표
            col_l, col_r = st.columns([2, 1])
            with col_l:
                months_sample = [1, 4, 7, 10]
                month_names = [MONTHS_KR[m-1] for m in months_sample]
                fig_radar = go.Figure()
                categories = ["기온 적합도", "습도 적합도", "일사량 적합도", "종합 점수"]
                for m, mname in zip(months_sample, month_names):
                    row = df[df["month"] == m]
                    if not row.empty:
                        r = row.iloc[0]
                        fig_radar.add_trace(go.Scatterpolar(
                            r=[r["temp_score"], r["humid_score"], r["solar_score"], r["total_score"]],
                            theta=categories,
                            fill="toself", name=mname, opacity=0.6,
                        ))
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    title=dict(text="분기별 레이더 차트 (1·4·7·10월)", font=dict(size=13)),
                    height=300, paper_bgcolor="white",
                    legend=dict(orientation="h", y=-0.1),
                    margin=dict(l=20, r=20, t=40, b=20),
                )
                st.plotly_chart(fig_radar, use_container_width=True)

            with col_r:
                low_months = df[df["total_score"] < 60]["month_kr"].tolist()
                high_months = df[df["total_score"] >= 80]["month_kr"].tolist()
                st.markdown(f"""
                <div class="card">
                  <div class="card-title">📋 분석 요약</div>
                  <div style="font-size:13px; line-height:2.0;">
                    <b>✅ 최적 달:</b><br>
                    {'·'.join(high_months) if high_months else '해당 없음'}<br>
                    <b>⚠️ 보완 필요 달:</b><br>
                    {'·'.join(low_months) if low_months else '없음'}<br>
                    <b>🏗️ 분석 면적:</b> {farm_area:,} m²<br>
                    <b>🌿 선택 작물:</b> {CROPS[selected_crop]['emoji']} {selected_crop}
                  </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")


# ════════════════════════════════════════════════════════
# TAB 4 — 결과 발표
# ════════════════════════════════════════════════════════
with tab4:
    st.markdown("""
    <div class="step-badge">🏆 4차시 · 결과 발표</div>
    <div style="font-size:13px; color:#555; margin-bottom:20px;">
      지역별 스마트팜 적합도 종합 비교 · 최적 입지 선정 · 데이터 기반 근거 제시
    </div>
    """, unsafe_allow_html=True)

    if not region_data:
        st.info("👈 사이드바에서 지역을 선택하고 **분석 시작**을 누르세요.")
    else:
        # 종합 점수 산출
        summary = []
        for region, df in region_data.items():
            heating, cooling = calc_energy(df, selected_crop, farm_area)
            score_grow  = df["total_score"].mean()
            score_led   = 100 - df["led_need"].mean()
            total_cost  = heating + cooling
            max_cost    = max(
                sum(calc_energy(d, selected_crop, farm_area))
                for d in region_data.values()
            )
            score_cost  = max(0, 100 - (total_cost / (max_cost + 1)) * 60)
            final_score = score_grow * 0.5 + score_led * 0.3 + score_cost * 0.2
            summary.append({
                "region": region,
                "생장 적합도": round(score_grow, 1),
                "보광 효율": round(score_led, 1),
                "비용 효율": round(score_cost, 1),
                "종합 점수": round(final_score, 1),
                "난방(만원)": heating,
                "냉방(만원)": cooling,
            })

        summary.sort(key=lambda x: x["종합 점수"], reverse=True)
        best = summary[0]

        # 1위 배너
        st.markdown(f"""
        <div style="background:linear-gradient(135deg, #2D6A4F 0%, #52B788 100%);
                    border-radius:16px; padding:28px 32px; margin-bottom:24px; color:white; text-align:center;">
          <div style="font-size:12px; letter-spacing:2px; opacity:0.8; margin-bottom:6px;">
            🏆 최적 입지 선정 결과
          </div>
          <div style="font-size:36px; font-weight:900; margin-bottom:4px;">
            📍 {best['region']}
          </div>
          <div style="font-size:48px; font-weight:700; font-family:'Space Grotesk', sans-serif;">
            {best['종합 점수']}점
          </div>
          <div style="font-size:13px; opacity:0.85; margin-top:8px;">
            생장 적합도 {best['생장 적합도']}점 · 보광 효율 {best['보광 효율']}점 · 비용 효율 {best['비용 효율']}점
          </div>
        </div>
        """, unsafe_allow_html=True)

        # 지역별 점수 비교 바 차트
        fig_final = go.Figure()
        categories_score = ["생장 적합도", "보광 효율", "비용 효율"]
        region_colors = ["#2D6A4F", "#F4A261", "#457B9D"]
        for i, s in enumerate(summary):
            fig_final.add_trace(go.Bar(
                name=s["region"],
                x=categories_score,
                y=[s["생장 적합도"], s["보광 효율"], s["비용 효율"]],
                marker_color=region_colors[i],
                text=[f"{v:.0f}" for v in [s["생장 적합도"], s["보광 효율"], s["비용 효율"]]],
                textposition="outside",
            ))
        fig_final.update_layout(
            title=dict(text="항목별 점수 비교", font=dict(size=15)),
            barmode="group", yaxis=dict(range=[0, 115]),
            height=340, paper_bgcolor="white", plot_bgcolor="#FAFAFA",
            legend=dict(orientation="h", y=1.15),
            margin=dict(l=30, r=20, t=50, b=30),
        )

        # 종합 점수 도넛
        fig_donut = go.Figure()
        for s in summary:
            fig_donut.add_trace(go.Pie(
                labels=["종합 점수", ""],
                values=[s["종합 점수"], 100 - s["종합 점수"]],
                hole=0.65,
                name=s["region"],
                marker_colors=["#2D6A4F", "#F0F7F4"],
                textinfo="none",
                showlegend=False,
            ))
        # 대신 가로 막대로 간단하게
        fig_rank = go.Figure(go.Bar(
            x=[s["종합 점수"] for s in summary],
            y=[s["region"] for s in summary],
            orientation="h",
            marker=dict(
                color=[s["종합 점수"] for s in summary],
                colorscale=[[0,"#F4A261"],[0.5,"#52B788"],[1,"#2D6A4F"]],
            ),
            text=[f"{s['종합 점수']}점" for s in summary],
            textposition="outside",
        ))
        fig_rank.update_layout(
            title=dict(text="종합 점수 순위", font=dict(size=15)),
            xaxis=dict(range=[0, 115]),
            height=200, paper_bgcolor="white", plot_bgcolor="#FAFAFA",
            margin=dict(l=20, r=60, t=40, b=20),
        )

        c1, c2 = st.columns([3, 2])
        with c1:
            st.plotly_chart(fig_final, use_container_width=True)
        with c2:
            st.plotly_chart(fig_rank, use_container_width=True)

        # 지역별 장단점 카드
        st.markdown("#### 📋 지역별 장단점 비교")
        cols = st.columns(len(summary))
        for i, (col, s) in enumerate(zip(cols, summary)):
            with col:
                rank_emoji = ["🥇","🥈","🥉"][i]
                df_r = region_data[s["region"]]
                best_month = df_r.loc[df_r["total_score"].idxmax(), "month_kr"]
                worst_month = df_r.loc[df_r["total_score"].idxmin(), "month_kr"]
                avg_led = df_r["led_need"].mean()

                strength = "일사량 풍부" if df_r["solar"].mean() > 13 else \
                           "온화한 기온" if abs(df_r["temp"].mean() - sum(CROPS[selected_crop]["opt_temp"])/2) < 3 else \
                           "안정적인 습도"
                weakness = "겨울 난방 필요" if s["난방(만원)"] > s["냉방(만원)"] else "여름 냉방 필요"

                st.markdown(f"""
                <div class="card">
                  <div style="font-size:18px; font-weight:700; margin-bottom:12px;">
                    {rank_emoji} {s['region']}
                  </div>
                  <div style="font-size:28px; font-weight:700; color:#2D6A4F; text-align:center; margin:8px 0;">
                    {s['종합 점수']}점
                  </div>
                  <hr>
                  <div style="font-size:12px; line-height:2.0;">
                    <b>✅ 강점:</b> {strength}<br>
                    <b>⚠️ 약점:</b> {weakness}<br>
                    <b>🌟 최적 월:</b> {best_month}<br>
                    <b>📉 취약 월:</b> {worst_month}<br>
                    <b>💡 LED 보광:</b> 연평균 {avg_led:.0f}% 필요<br>
                    <b>💰 에너지 비용:</b> {s['난방(만원)']+s['냉방(만원)']:,}만원/년
                  </div>
                </div>
                """, unsafe_allow_html=True)

        # 탐구 마무리 질문
        st.markdown("""
        <div class="card" style="border-left-color:#F4A261; margin-top:8px;">
          <div class="card-title">💬 탐구 마무리 토론 질문</div>
          <div style="font-size:14px; line-height:2.2;">
            1. 종합 점수 1위 지역이 모든 작물에 대해서도 1위일까? 다른 작물로 바꾸면 결과가 달라지는가?<br>
            2. 에너지 비용과 생장 효율 중 어느 것을 더 중요하게 고려해야 할까?<br>
            3. 기후변화로 10년 후 데이터가 달라진다면, 입지 선택도 바뀔 수 있을까?<br>
            4. 실제 스마트팜 창업 시, 데이터 분석 외에 어떤 요소를 추가로 고려해야 할까?
          </div>
        </div>
        """, unsafe_allow_html=True)
