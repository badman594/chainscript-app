import os
from lark import Lark, Transformer
from openai import OpenAI
import streamlit as st

# Настройка страницы
st.set_page_config(page_title="ChainScript IDE", page_icon="🚀", layout="wide")
st.title("🚀 ChainScript Web IDE v1.1")
st.caption("Базовая стабильная версия с поддержкой русского синтаксиса")

# 1. ИСПРАВЛЕННАЯ ГРАММАТИКА: теперь русские команды обрабатываются корректно
chainscript_grammar = """
    start: statement+
    ?statement: agent_call | show_call
    
    agent_call: "AI" IDENTIFIER ":" STRING "->" "Сохранить" "в" IDENTIFIER
    show_call: "Показать" IDENTIFIER
    
    IDENTIFIER: /[a-zA-Zа-яА-Я0-9_]+/
    STRING: /"[^"]*"/
    
    %import common.WS
    %ignore WS
"""

# Инициализация OpenAI
api_key = st.sidebar.text_input("Вставьте ваш OpenAI API Key", type="password", value=os.environ.get("OPENAI_API_KEY", ""))
client = OpenAI(api_key=api_key) if api_key else None

if "logs" not in st.session_state: st.session_state.logs = []
if "variables" not in st.session_state: st.session_state.variables = {}

class ChainScriptInterpreter(Transformer):
    def agent_call(self, args):
        # Извлекаем аргументы: имя агента, текст промта и имя переменной
        agent_name = str(args[0])
        prompt_raw = str(args[1]).strip('"')
        var_name = str(args[2])
        
        # Подстановка контекста (замена {переменных} на их значения)
        for var, val in st.session_state.variables.items():
            prompt_raw = prompt_raw.replace(f"{{{var}}}", str(val))
            
        st.session_state.logs.append(f"🤖 [ChainScript] Агент {agent_name} обрабатывает запрос...")
        
        if not client:
            st.session_state.logs.append("❌ Ошибка: Не указан API-ключ в боковой панели!")
            return

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt_raw}]
            )
            result = response.choices.message.content
            st.session_state.variables[var_name] = result
            st.session_state.logs.append(f"✅ Результат успешно сохранен в '{var_name}'")
        except Exception as e:
            st.session_state.logs.append(f"❌ Ошибка API: {e}")

    def show_call(self, args):
        var_name = str(args[0])
        val = st.session_state.variables.get(var_name, "Переменная не найдена.")
        st.session_state.logs.append(f"\n📋 [ВЫВОД {var_name}]:\n{val}\n" + "-"*40)

def run_code(source_code):
    st.session_state.logs = []
    st.session_state.variables = {}
    
    parser = Lark(chainscript_grammar, parser='lalr')
    try:
        tree = parser.parse(source_code)
        ChainScriptInterpreter().transform(tree)
    except Exception as e:
        st.session_state.logs.append(f"❌ Ошибка синтаксиса ChainScript: {e}")

# Интерфейс приложения (Две колонки)
col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 Редактор кода")
    
    # Текст по умолчанию для проверки
    default_code = """AI Agent1: "Назови один главный тренд в технологиях 2026 года в одно предложение" -> Сохранить в trend
AI Agent2: "Придумай кликбейтный заголовок для статьи про {trend}" -> Сохранить в post
Показать post"""
    
    code_input = st.text_area("Напишите ваш код здесь:", value=default_code, height=300)
    
    if st.button("▶️ Запустить код", type="primary"):
        with st.spinner("ChainScript выполняет цепочку запросов..."):
            run_code(code_input)

with col2:
    st.subheader("🖥️ Консоль вывода")
    if st.session_state.logs:
        for log in st.session_state.logs:
            if "❌" in log: st.error(log)
            elif "✅" in log: st.success(log)
            elif "📋" in log: st.info(log)
            else: st.text(log)
    else:
        st.info("Здесь появится результат работы ИИ-агентов после запуска.")

