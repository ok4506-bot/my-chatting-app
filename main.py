import streamlit as st
from openai import OpenAI

# -----------------------------------------------------------------------
# 1) 기본 화면 설정
# -----------------------------------------------------------------------
st.set_page_config(page_title="AI 데이터 분석 선생님", page_icon="📊")
st.title("📊 AI 데이터 분석 선생님")

# -----------------------------------------------------------------------
# 2) Solar API 클라이언트 만들기
#    - API 키는 절대 코드에 직접 쓰지 않고, 스트림릿의 "비밀 금고(secrets)"에서 가져와요.
#    - 스트림릿 클라우드에 배포할 때 Settings > Secrets 에
#      SOLAR_API_KEY = "여기에_실제_키" 형태로 등록해두면 됩니다.
# -----------------------------------------------------------------------
try:
    SOLAR_API_KEY = st.secrets["SOLAR_API_KEY"]
except Exception:
    st.error(
        "🔑 API 키를 찾을 수 없어요.\n\n"
        "스트림릿 클라우드의 'Secrets' 설정에 SOLAR_API_KEY 값을 등록해주세요."
    )
    st.stop()

client = OpenAI(
    api_key=SOLAR_API_KEY,
    base_url="https://api.upstage.ai/v1",  # Solar API 접속 주소
)

# 모델 이름은 문제에서 지정한 그대로 사용합니다. (바꾸지 마세요!)
MODEL_NAME = "solar-open2"

# AI에게 부여할 성격(시스템 프롬프트)
SYSTEM_PROMPT = "너는 따뜻하고 친절한 데이터 분석 선생님이야. 반드시 순수 한국어로만 답해"

# -----------------------------------------------------------------------
# 3) 대화 기록을 세션(session_state)에 저장하기
#    - 세션에 저장해두면 사용자가 메시지를 여러 번 보내도
#      이전 대화 내용을 기억한 채로 이어서 답할 수 있어요.
# -----------------------------------------------------------------------
if "messages" not in st.session_state:
    # 화면에 보여줄 대화 기록 (시스템 프롬프트는 화면에는 안 보여줍니다)
    st.session_state.messages = []

# -----------------------------------------------------------------------
# 4) 지금까지의 대화 내용을 화면에 말풍선으로 그리기
# -----------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------------------------------------------------
# 5) 사용자가 새 메시지를 입력하면 실행되는 부분
# -----------------------------------------------------------------------
user_input = st.chat_input("궁금한 데이터 분석 질문을 입력해보세요!")

if user_input:
    # 5-1) 사용자 메시지를 세션에 저장하고 화면에 표시
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 5-2) API에 보낼 메시지 목록 만들기
    #      (맨 앞에 시스템 프롬프트를 넣어서 AI 성격을 지정해줍니다)
    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    api_messages.extend(st.session_state.messages)

    # 5-3) AI의 답변을 스트리밍(실시간 타이핑처럼)으로 받아서 보여주기
    with st.chat_message("assistant"):
        placeholder = st.empty()  # 글자가 계속 갱신될 자리
        full_answer = ""  # 지금까지 받은 답변을 계속 이어붙일 변수

        try:
            # reasoning_effort="none" 은 추론(생각) 기능을 꺼서
            # 답변을 더 빠르게 받기 위한 옵션입니다.
            # (temperature가 아니라 reasoning_effort 라는 이름의 값을 사용합니다)
            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=api_messages,
                stream=True,
                extra_body={"reasoning_effort": "none"},
            )

            for chunk in stream:
                # 조각(chunk) 하나하나에 들어있는 글자를 이어붙여요.
                delta = chunk.choices[0].delta.content
                if delta:
                    full_answer += delta
                    # 실시간으로 화면 갱신 (커서 느낌을 위해 "▌" 표시)
                    placeholder.markdown(full_answer + "▌")

            # 스트리밍이 끝나면 커서 표시 없이 최종 답변만 보여주기
            placeholder.markdown(full_answer)

        except Exception as e:
            # 에러 화면(붉은 에러 메시지)을 그대로 보여주지 않고
            # 사용자에게 친절한 한국어 안내 메시지를 보여줍니다.
            full_answer = (
                "😥 지금은 답변을 가져오지 못했어요.\n\n"
                "인터넷 연결이나 API 키 설정을 확인한 뒤 잠시 후 다시 시도해주세요."
            )
            placeholder.markdown(full_answer)
            # 필요하다면 개발자가 원인을 확인할 수 있도록 콘솔에만 남겨둡니다.
            print(f"[에러 발생] {e}")

    # 5-4) AI의 답변도 세션에 저장 (다음 질문에서 이 내용을 기억하게 됨)
    st.session_state.messages.append({"role": "assistant", "content": full_answer})
