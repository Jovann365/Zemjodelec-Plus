from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1/",
    api_key="ollama",
)

def ask_sinong(messages=None, think=False):
    response = client.chat.completions.create(
        model="sinong-8b",
        messages=messages,
        temperature=0.6 if think else 0.7,
        top_p=0.95 if think else 0.8,
        max_tokens=4000 if think else 1500,
    )

    answer = response.choices[0].message.content
    answer = answer.replace("<think>", "").replace("</think>", "").strip()
    return answer

