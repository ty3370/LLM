import pymysql
import streamlit as st
from openai import OpenAI
import os
import json
from dotenv import load_dotenv
from datetime import datetime

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MODEL = 'gpt-4o'

# OpenAI API 설정
client = OpenAI(api_key=OPENAI_API_KEY)

# 초기 프롬프트
initial_prompt = (
    "너는 중학생의 탐구를 돕는 챗봇이야. 이름은 '과학탐구 도우미'야."
    "이 탐구는 중학교 1학년 학생들이 하는 탐구이므로, 중학교 1학년 수준에 맞게 설명해야 돼."
    "탐구의 주제는 '조금도 움직이지 않는 아주 잔잔한 액체에서 입자의 움직임은 어떨까?'야."
    "따라서 탐구에서 변화시키는 변인은 '액체가 잔잔한 정도'야. 즉 실험은 잔잔한 액체와 그렇지 않은 액체를 비교하는 형태여야 해."
    "학생이 잔잔한 액체에서 입자가 움직이는지를 물어볼 경우, (즉 탐구의 결론을 물어볼 경우) 직접 탐구를 수행해서 알아보라고 대답해."
    "학생이 실험 아이디어를 제시하면, 실험 과정을 명료화, 구체화할 수 있도록 대화를 통해 지원해줘."
    "다만 '돋보기나 현미경으로 액체 입자를 관찰한다'라는 실험 아이디어를 제시하면 이것이 과학적으로 불가능하다고 설명해줘."
    "만약 학생이 어떤 실험을 해야 할지 전혀 모르겠다고 하면, 중학교에서 할 만한 수준이면서 과학적으로 타당한 실험을 제시해. 예를 들어 '확산'을 이용하는 것과 '증발'을 이용하는 거야. 잔잔한 액체에서 확산이나 증발이 일어나면 입자들이 움직임을 알 수 있어."
    "이 때 실험 과정 전체를 직접 알려주지는 마. 학생이 가진 아이디어를 물어보고, 대화를 통해 학생이 직접 실험 과정을 작성하도록 유도해."
    "학생이 가설에 대해 질문한다면, 그 가설이 두 변인의 관계로 서술되어 있는지, 잠정적 결론 형태로 서술되어 있는지 확인해."
    "학생이 실험 과정에 대해 질문한다면, 실험에서 변화시켜야 하는 변인과 일정하게 유지해야 하는 변인이 서술되어 있는지 확인해. 이 주제에서 변화시켜야 하는 변인은 액체가 잔잔한 정도야."
    "학생이 실험의 결론에 대해 질문한다면, 결론이 과학적 오류 없이 가설과 실험 결과를 종합한 것인지 확인해. 학생의 가설을 모른다면 학생에게 질문해."
    "과학 개념을 설명할 때는 14세 정도의 학생 수준으로 간결하게 설명해."
    "가능하면 대화가 계속 이어지며 학생이 깊이 있는 이해를 할 수 있도록 응답해줘."
)

# MySQL 저장 함수
def save_to_db():
    number = st.session_state.get('user_number', '').strip()
    name = st.session_state.get('user_name', '').strip()

    if not number or not name:  # 학번과 이름 확인
        st.error("사용자 학번과 이름을 입력해야 합니다.")
        return False  # 저장 실패

    try:
        db = pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_DATABASE"),
            charset="utf8mb4",  # UTF-8 지원
            autocommit=True  # 자동 커밋 활성화
        )
        cursor = db.cursor()
        now = datetime.now()

        sql = """
        INSERT INTO qna (number, name, chat, time)
        VALUES (%s, %s, %s, %s)
        """
        chat = json.dumps(st.session_state["messages"], ensure_ascii=False)  # 대화 내용을 JSON 문자열로 변환
        val = (number, name, chat, now)

        # SQL 실행
        cursor.execute(sql, val)
        cursor.close()
        db.close()
        st.success("대화 내용 처리 중입니다.")
        return True  # 저장 성공
    except pymysql.MySQLError as db_err:
        st.error(f"DB 처리 중 오류가 발생했습니다: {db_err}")
        return False  # 저장 실패
    except Exception as e:
        st.error(f"알 수 없는 오류가 발생했습니다: {e}")
        return False  # 저장 실패

# GPT 응답 생성 함수
def get_chatgpt_response(prompt):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": initial_prompt}] + st.session_state["messages"] + [{"role": "user", "content": prompt}],
    )
    answer = response.choices[0].message.content

    # 사용자와 챗봇 대화만 기록
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.session_state["messages"].append({"role": "assistant", "content": answer})
    return answer

# 페이지 1: 학번 및 이름 입력
def page_1():
    st.title("보라중학교 과학탐구 도우미 챗봇")
    st.write("학번과 이름을 입력한 뒤 '다음' 버튼을 눌러주세요.")

    if "user_number" not in st.session_state:
        st.session_state["user_number"] = ""
    if "user_name" not in st.session_state:
        st.session_state["user_name"] = ""

    st.session_state["user_number"] = st.text_input("학번", value=st.session_state["user_number"])
    st.session_state["user_name"] = st.text_input("이름", value=st.session_state["user_name"])

    if st.button("다음"):
        if st.session_state["user_number"].strip() == "" or st.session_state["user_name"].strip() == "":
            st.error("학번과 이름을 모두 입력해주세요.")
        else:
            st.session_state["step"] = 2
            st.rerun()

# 페이지 2: GPT와 대화
def page_2():
    st.title("탐구 설계 대화")
    st.write("과학탐구 도우미와 대화를 나누며 탐구를 설계하세요.")

    # 학번과 이름 확인
    if not st.session_state.get("user_number") or not st.session_state.get("user_name"):
        st.error("학번과 이름이 누락되었습니다. 다시 입력해주세요.")
        st.session_state["step"] = 1
        st.rerun()

    # 대화 기록 초기화
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    if "user_input_temp" not in st.session_state:
        st.session_state["user_input_temp"] = ""

    # 대화 UI
    user_input = st.text_area(
        "You: ",
        value=st.session_state["user_input_temp"],
        key="user_input",
        on_change=lambda: st.session_state.update({"user_input_temp": st.session_state["user_input"]}),
    )

    if st.button("전송") and user_input.strip():
        answer = get_chatgpt_response(user_input)
        st.session_state["recent_message"] = {"user": user_input, "assistant": answer}  # 최근 대화 저장
        st.session_state["user_input_temp"] = ""
        st.rerun()

    # 최근 대화 출력
    if "recent_message" in st.session_state:
        st.subheader("[최근 대화]")
        st.write(f"**You:** {st.session_state['recent_message']['user']}")
        st.write(f"**과학탐구 도우미:** {st.session_state['recent_message']['assistant']}")

    # 누적 대화 목록 출력
    if "messages" in st.session_state:
        st.subheader("[누적 대화 목록]")
        for message in st.session_state["messages"]:
            if message["role"] == "user":
                st.write(f"**You:** {message['content']}")
            elif message["role"] == "assistant":
                st.write(f"**과학탐구 도우미:** {message['content']}")

    # 다음 버튼: 저장 성공 여부에 따라 페이지 전환
    if st.button("다음"):
        if save_to_db():  # 저장 성공 시만 페이지 전환
            st.session_state["step"] = 3
            st.rerun()

# 페이지 3: 실험 과정 출력
def page_3():
    st.title("실험 과정")
    st.write("실험 과정을 정리 중입니다. 잠시만 기다려주세요.")

    if "experiment_plan" not in st.session_state:
        chat_history = "\n".join(
            f"{msg['role']}: {msg['content']}" for msg in st.session_state["messages"]
        )
        prompt = f"다음은 학생과 과학탐구 도우미의 대화 기록입니다:\n{chat_history}\n\n"
        prompt += "위 대화를 바탕으로 학생의 탐구 아이디어에 맞는 실험 과정을 작성해주세요."
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": prompt}],
        )
        st.session_state["experiment_plan"] = response.choices[0].message.content
    
    st.write(st.session_state["experiment_plan"])

# 메인 로직
if "step" not in st.session_state:
    st.session_state["step"] = 1

if st.session_state["step"] == 1:
    page_1()
elif st.session_state["step"] == 2:
    page_2()
elif st.session_state["step"] == 3:
    page_3()