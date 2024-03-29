import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")


start_chat_log = '''Human: Hello, how are you?
AI: I am doing great. How can I help you today?
'''

completion = openai.Completion()

def ask(question, chat_log=None):
    if chat_log is None:
        chat_log = start_chat_log
    prompt = f'{chat_log}Human: {question}\nAI:'
    #print(f"This is prompt --- {prompt} --- ")
    response = completion.create(
    prompt=prompt, engine="davinci", stop=['\nHuman'], temperature=0.9,
    top_p=1, frequency_penalty=0.6, presence_penalty=0.7, best_of=1,
    max_tokens=150)
    answer = response.choices[0].text.strip()
    return answer

def append_interaction_to_chat_log(question, answer, chat_log=None):
    if chat_log is None:
        chat_log = start_chat_log
    return f'{chat_log}Human: {question}\nAI: {answer}\n'

