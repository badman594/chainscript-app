import os
from lark import Lark, Transformer
from openai import OpenAI
import streamlit as st

# 1. Настройка страницы
st.set_page_config(page_title="ChainScript IDE", page_icon="🚀", layout="wide")
st.title("🚀 ChainScript Web IDE v1.0")
st.caption("Первый специализированный язык для создания цепочек ИИ-агентов")

# 2. Грамматика ChainScript
chainscript_grammar = """
    start: statement+
    ?statement: agent_call | show_call
    
    agent_call: "CALL " IDENTIFIER ":" STRING "->" "SAVE " IDENTIFIER
    show_call: "PRINT " IDENTIFIER
    
    IDENTIFIER: /[a-zA-Zа-яА-Я0-9_]+/
    STRING: /"[^"\\]*(\\.[^"\\]*)*"/
    
    %import common.WS
    %ignore WS
"""

# Инициализация OpenAI (берем из ввода пользователя или переменных среды)
api_key = st.sidebar.text_input("Вставьте ваш OpenAI API Key", type="password", value=os.environ.get("OPENAI_API_KEY", ""))
client = OpenAI(api_key=api_key) if api_key else None

# Глобальное хранилище данных для текущей сессии
if "logs" not in st.session_state:
    st.session_state.logs = []
if "variables" not in st.session_state:
    st.session_state.variables = {}

class ChainScriptWebInterpreter(Transformer):
    def agent_call(self, args):
        agent_name, prompt_raw, var_name = args
        prompt = prompt_raw.strip('"')
        
        # Подстановка контекста
        for var, val in st.session_state.variables.items():
            prompt = prompt.replace(f"{{{var}}}", str(val))
            
        st.session_state.logs.append(f"🤖 [ChainScript] Агент {agent_name} обрабатывает запрос...")
        
        if not client:
            st.session_state.logs.append("❌ Ошибка: Не указан API-ключ в боковой панели!")
            return

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.choices.message.content
            st.session_state.variables[str(var_name)] = result
            st.session_state.logs.append(f"✅ Данные успешно записаны в переменную '{var_name}'")
        except Exception as e:
            st.session_state.logs.append(f"❌ Ошибка API: {e}")

    def show_call(self, args):
        var_name = str(args)
        val = st.session_state.variables.get(var_name, "Переменная не найдена.")
        st.session_state.logs.append(f"\n📋 [ВЫВОД {var_name}]:\n{val}\n" + "-"*40)

# Функция запуска компилятора
def run_code(source_code):
    st.session_state.logs = []
    st.session_state.variables = {}
    
    parser = Lark(chainscript_grammar, parser='lalr')
    try:
        tree = parser.parse(source_code)
        ChainScriptWebInterpreter().transform(tree)
    except Exception as e:
        st.session_state.logs.append(f"❌ Ошибка синтаксиса ChainScript: {e}")

# 3. Интерфейс: Две колонки
col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 Редактор кода")
    
    # Шаблон кода по умолчанию
    default_code = """CALL Finder: "Назови один главный тренд в технологиях 2026 года в одно предложение" -> SAVE trend
CALL Marketer: "Придумай 3 идеи для постов в Telegram про {trend}" -> SAVE posts
PRINT posts"""
    
    code_input = st.text_area("Напишите ваш код здесь:", value=default_code, height=300)
    
    if st.button("▶️ Запустить код", type="primary"):
        with st.spinner("ChainScript компилируется и выполняет запросы..."):
            run_code(code_input)

with col2:
    st.subheader("🖥️ Консоль вывода")
    if st.session_state.logs:
        for log in st.session_state.logs:
            if "❌" in log:
                st.error(log)
            elif "✅" in log:
                st.success(log)
            elif "📋" in log:
                st.info(log)
            else:
                st.text(log)
    else:
        st.info("Здесь появится результат работы ИИ-агентов после запуска.")
