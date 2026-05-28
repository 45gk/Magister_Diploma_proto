from langchain_gigachat.chat_models import GigaChat
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph import tool



memory = MemorySaver()
model = GigaChat(
    credentials="ключ_авторизации",
    scope="GIGACHAT_API_PERS",
    model="GigaChat-Pro",
    verify_ssl_certs=False,
)

@tool("custom_tool")
def custom_tool(agent, input):
    
    # Реализуйте логику вашего инструмента здесь
    return f"Результат работы инструмента для входных данных: {input}"


agent = create_react_agent(model=model, memory=memory)
tools = [custom_tool]

response = agent.invoke({"messages": [("user", "Какая самая дорогая публичная компания в мире?")]})
print(response["messages"][-1].content)

def main():
    while True:
        user_input = input("Введите запрос: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Завершение работы агента.")
            break
        
        response = agent.run(user_input, tools=tools)
        print(f"Ответ агента: {response}")

