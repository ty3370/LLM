import streamlit as st
from openai import OpenAI
import os
import json
from dotenv import load_dotenv
import mysql.connector
from datetime import datetime

load_dotenv()  # .env 파일 로드

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MODEL = 'gpt-4o'

# OpenAI API 키 설정
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# 초기 프롬프트 설정
initial_prompt = (
    "너는 중학생의 탐구를 돕는 챗봇이야."
    "먼저 '반가워요. 액체를 이루는 입자에 관한 탐구에서 궁금한 점을 질문해주세요.' 하고 시작해."
    "이 탐구는 중학교 1학년 학생들이 하는 탐구이므로, 중학교 1학년 수준에 맞게 설명해야 돼."
    "탐구의 주제는 '조금도 움직이지 않는 아주 잔잔한 액체에서 입자의 움직임은 어떨까?'야."
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
    "마크다운 언어는 적용되지 않으므로 사용하지 마.(예: **굵게**)"
)

# 챗봇 응답 함수
def get_chatgpt_response(prompt):
    st.session_state["messages"].append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=MODEL,
        messages=st.session_state["messages"],
    )
    
    answer = response.choices[0].message.content
    print(answer)
    
    st.session_state["messages"].append({"role": "assistant", "content": answer})    

    return answer

# MySQL에 대화 내용 저장 함수
def save_to_db():
    number = st.session_state.get('user_number', '').strip()
    name = st.session_state.get('user_name', '').strip()

    if name == '' or number == '':
        st.error("사용자 학번과 이름을 입력해야 합니다.")
        return
    
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        passwd=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_DATABASE")
    )
    cursor = db.cursor()
    now = datetime.now()

    sql = """
    INSERT INTO qna (number, name, chat, time)
    VALUES (%s, %s, %s, %s)
    """
    chat = json.dumps(st.session_state["messages"])  # 대화 내용을 JSON 문자열로 변환
    val = (number, name, chat, now)
    cursor.execute(sql, val)
    db.commit()
    cursor.close()
    db.close()
    st.success("대화 내용이 저장되었습니다.")

# Streamlit 애플리케이션
st.title("보라중학교 과학탐구 도우미 챗봇")
st.write("2024학년도 2학기 보라중학교 과학탐구 수업을 돕기 위한 챗봇입니다. 학번과 이름을 입력한 뒤 [정보 입력] 버튼을 클릭하고 사용하시면 됩니다. 채팅이 끝나면 제일 아래에 [사용 완료] 버튼을 눌러주세요.")

# 사용자 정보 입력 폼
with st.form(key='user_info_form'):
    user_number = st.text_input("학번", key="user_number")
    user_name = st.text_input("이름", key="user_name")
    user_info_submit = st.form_submit_button(label='정보 입력')

# 대화 기록 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": initial_prompt}]

# Submit 버튼을 눌렀을 때 초기 대화를 시작
if user_info_submit:
    get_chatgpt_response("")

# 대화 기록 출력
if "messages" in st.session_state:
    for message in st.session_state["messages"]:
        if message["role"] == "user":
            st.markdown(f'<div style="color:blue; margin-bottom: 10px;">과학탐구 도우미: {message["content"].replace("\\n", "<br>")}</div>', unsafe_allow_html=True)
        elif message["role"] == "assistant":
            st.markdown(f'<div style="color:blue; margin-bottom: 10px;">과학탐구 도우미: {message["content"].replace("\n", "<br>")}</div>', unsafe_allow_html=True)

# 폼을 사용하여 입력 필드와 버튼 그룹화
if "user_name" in st.session_state and "user_number" in st.session_state:
    with st.form(key='my_form', clear_on_submit=True):
        user_input = st.text_area("You: ", key="user_input")
        submit_button = st.form_submit_button(label='전송')

        if submit_button and user_input:
            # 사용자 입력 저장 및 챗봇 응답 생성
            get_chatgpt_response(user_input)
            st.rerun()  # 상태 업데이트 후 즉시 리렌더링

# "사용 완료" 버튼
if "user_name" in st.session_state and "user_number" in st.session_state:
    if st.button("사용 완료"):
        save_to_db()

# 새로운 메시지가 추가되면 스크롤을 맨 아래로 이동
st.write('<script>window.scrollTo(0, document.body.scrollHeight);</script>', unsafe_allow_html=True)
