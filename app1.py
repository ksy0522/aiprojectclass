import math
from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(page_title="스마트팜 입지 최적화", page_icon="🌱", layout="wide")

# -----------------------------
# 기본 데이터
# -----------------------------
LOCATIONS = {
    "서울": {"lat": 37.5665, "lon": 126.9780},
    "춘천": {"lat": 37.8813, "lon": 127.7298},
    "대전": {"lat": 36.3504, "lon": 127.3845},
    "부산": {"lat": 35.1796, "lon": 129.0756},
    "제주": {"lat": 33.4996, "lon": 126.5312},
    "광주": {"lat": 35.1595, "lon": 126.8526},
    "강릉": {"lat": 37.7519, "lon": 128.8761},
}

# 값은 수업용 단순화 모델입니다.
CROPS = {
    "상추": {"temp": (15, 23), "humidity": (60, 80), "light_daily_kwh": (2.5, 5.0)},
    "토마토": {"temp": (20, 28), "humidity": (55, 75), "light_daily_kwh": (4.0, 7.0)},
    "딸기": {"temp": (15, 25), "humidity": (60, 80), "light_daily_kwh": (3.0, 6.0)},
    "바질": {"temp": (20, 30), "humidity": (50, 70), "light_daily_kwh": (3.5, 6.0)},
}

# -----------------------------
# API 함수
# -----------------------------
@st.cache_data(ttl=60 * 60)
def get_weather(lat: float, lon: float) -> pd.DataFrame:
    """Open-Meteo API에서 7일 예보 데이터를 불러옵니다."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,shortwave_radiation,precipitation",
        "forecast_days": 7,
        "timezone": "Asia/Seoul",
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()["hourly"]
    df = pd.DataFrame(data)
    df["time"] = pd.to_datetime(df["time"])
    return df

# -----------------------------
# 점수 함수
# -----------------------------
def range_score(value: float, low: float, high: float, tolerance: float) -> float:
    """적정 범위 안이면 100점, 벗어나면 거리만큼 감점합니다."""
    if low <= value <= high:
        return 100.0
    if value < low:
        diff = low - value
    else:
        diff = value - high
    return max(0.0, 100.0 * (1 - diff / tolerance))


def light_score(daily_light_kwh: float, low: float, high: float) -> float:
    if low <= daily_light_kwh <= high:
        return 100.0
    if daily_light_kwh < low:
        return max(0.0, 100.0 * daily_light_kwh / low)
    # 빛이 너무 강하면 차광 필요. 과잉도 감점.
    return max(0.0, 100.0 * (1 - (daily_light_kwh - high) / high))


def calculate_scores(df: pd.DataFrame, crop_name: str, weights: dict) -> dict:
    crop = CROPS[crop_name]
    temp_low, temp_high = crop["temp"]
    hum_low, hum_high = crop["humidity"]
    light_low, light_high = crop["light_daily_kwh"]

    avg_temp = df["temperature_2m"].mean()
    avg_hum = df["relative_humidity_2m"].mean()

    # shortwave_radiation 단위 W/m², 1시간 간격이므로 Wh/m²로 합산 후 kWh/m²/day 변환
    daily_light = (
        df.set_index("time")["shortwave_radiation"]
        .resample("D")
        .sum()
        / 1000
    )
    avg_daily_light = daily_light.mean()

    temp_score = range_score(avg_temp, temp_low, temp_high, tolerance=15)
    hum_score = range_score(avg_hum, hum_low, hum_high, tolerance=40)
    sun_score = light_score(avg_daily_light, light_low, light_high)

    total = (
        weights["temp"] * temp_score
        + weights["humidity"] * hum_score
        + weights["light"] * sun_score
    ) / sum(weights.values())

    # 수업용 간단 에너지 지표
    target_temp = (temp_low + temp_high) / 2
    heating_need = max(0, target_temp - avg_temp)
    cooling_need = max(0, avg_temp - target_temp)
    led_need = max(0, light_low - avg_daily_light)

    return {
        "평균기온(℃)": avg_temp,
        "평균습도(%)": avg_hum,
        "평균 일사량(kWh/m²/day)": avg_daily_light,
        "온도점수": temp_score,
        "습도점수": hum_score,
        "빛점수": sun_score,
        "스마트팜 적합도": total,
        "난방 필요도": heating_need,
        "냉방 필요도": cooling_need,
        "LED 보광 필요도": led_need,
    }

# -----------------------------
# UI
# -----------------------------
st.title("🌱 데이터로 찾는 최적의 스마트팜 입지")
st.caption("Open-Meteo API 기상 데이터를 활용해 지역별 스마트팜 운영 적합도를 비교하는 교육용 웹앱")

with st.sidebar:
    st.header("⚙️ 탐구 조건 설정")
    selected_crop = st.selectbox("작물 선택", list(CROPS.keys()))
    selected_locations = st.multiselect(
        "비교할 지역 선택", list(LOCATIONS.keys()), default=["서울", "춘천", "부산", "제주"]
    )

    st.subheader("가중치 조절")
    w_temp = st.slider("온도 중요도", 1, 10, 4)
    w_hum = st.slider("습도 중요도", 1, 10, 3)
    w_light = st.slider("빛 중요도", 1, 10, 3)

    st.divider()
    st.write("작물별 적정 조건")
    crop = CROPS[selected_crop]
    st.write(f"온도: {crop['temp'][0]}~{crop['temp'][1]}℃")
    st.write(f"습도: {crop['humidity'][0]}~{crop['humidity'][1]}%")
    st.write(f"일사량: {crop['light_daily_kwh'][0]}~{crop['light_daily_kwh'][1]} kWh/m²/day")

if not selected_locations:
    st.warning("왼쪽에서 비교할 지역을 1개 이상 선택하세요.")
    st.stop()

weights = {"temp": w_temp, "humidity": w_hum, "light": w_light}

rows = []
weather_by_location = {}
errors = []

for name in selected_locations:
    try:
        loc = LOCATIONS[name]
        df = get_weather(loc["lat"], loc["lon"])
        weather_by_location[name] = df
        score = calculate_scores(df, selected_crop, weights)
        rows.append({"지역": name, **score})
    except Exception as e:
        errors.append(f"{name}: {e}")

if errors:
    st.error("일부 지역의 API 데이터를 불러오지 못했습니다.\n" + "\n".join(errors))

result = pd.DataFrame(rows)
if result.empty:
    st.stop()

best = result.sort_values("스마트팜 적합도", ascending=False).iloc[0]

col1, col2, col3 = st.columns(3)
col1.metric("가장 적합한 지역", best["지역"])
col2.metric("최고 적합도", f"{best['스마트팜 적합도']:.1f}점")
col3.metric("선택 작물", selected_crop)

st.subheader("1. 지역별 스마트팜 적합도 비교")
fig = px.bar(
    result.sort_values("스마트팜 적합도", ascending=False),
    x="지역",
    y="스마트팜 적합도",
    text="스마트팜 적합도",
    range_y=[0, 100],
    title="지역별 스마트팜 적합도 점수",
)
fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
st.plotly_chart(fig, use_container_width=True)

st.subheader("2. 세부 점수 비교")
score_cols = ["지역", "온도점수", "습도점수", "빛점수", "스마트팜 적합도"]
st.dataframe(result[score_cols].round(1), use_container_width=True, hide_index=True)

fig2 = px.bar(
    result,
    x="지역",
    y=["온도점수", "습도점수", "빛점수"],
    barmode="group",
    title="온도·습도·빛 점수 비교",
)
st.plotly_chart(fig2, use_container_width=True)

st.subheader("3. 에너지 제어 필요도")
st.write("값이 클수록 온실 환경을 맞추기 위해 추가 제어가 더 필요하다는 뜻입니다.")
energy_cols = ["지역", "난방 필요도", "냉방 필요도", "LED 보광 필요도"]
st.dataframe(result[energy_cols].round(2), use_container_width=True, hide_index=True)

fig3 = px.bar(
    result,
    x="지역",
    y=["난방 필요도", "냉방 필요도", "LED 보광 필요도"],
    barmode="group",
    title="지역별 난방·냉방·LED 보광 필요도",
)
st.plotly_chart(fig3, use_container_width=True)

st.subheader("4. 시간별 기상 데이터 확인")
loc_for_detail = st.selectbox("상세히 볼 지역", selected_locations)
df_detail = weather_by_location[loc_for_detail].copy()

metric = st.selectbox(
    "확인할 변수",
    ["temperature_2m", "relative_humidity_2m", "shortwave_radiation", "precipitation"],
    format_func=lambda x: {
        "temperature_2m": "기온(℃)",
        "relative_humidity_2m": "상대습도(%)",
        "shortwave_radiation": "일사량(W/m²)",
        "precipitation": "강수량(mm)",
    }[x],
)
fig4 = px.line(df_detail, x="time", y=metric, title=f"{loc_for_detail}의 시간별 데이터")
st.plotly_chart(fig4, use_container_width=True)

st.subheader("5. 학생 탐구 질문")
st.markdown(
    """
- 같은 작물이라도 지역에 따라 적합도 점수가 달라지는 이유는 무엇일까?
- 온도, 습도, 빛 중 어떤 요인이 결과에 가장 큰 영향을 주었을까?
- 가중치를 바꾸면 최적 지역이 달라지는가?
- 에너지를 적게 쓰면서 작물을 잘 키우기 위한 전략은 무엇일까?
"""
)

with st.expander("계산 모델 보기"):
    st.latex(r"적합도 = \frac{w_T T_{score} + w_H H_{score} + w_L L_{score}}{w_T+w_H+w_L}")
    st.write("이 모델은 수업용 단순화 모델입니다. 실제 스마트팜 운영에는 CO₂ 농도, 토양/양액, 병충해, 품종, 설비 효율 등이 추가로 고려됩니다.")

st.caption("데이터 출처: Open-Meteo Weather Forecast API")
