from openai import OpenAI
import ollama

# import PROFILES


# sample_msgs = simple_msgs(PROFILES.SYSTEM_PROMPTS["minimal-coder"])
# print(sample_msgs)
TASKDATA = open('./TASK-REFACTOR.txt').read()
model = "llama3-gradient:8b-instruct-1048k-q6_K"
# model = "llama3:instruct"
r = ollama.chat(
    model=model,
    messages=[
        {
            "role": "system",
            "content": f"""
            _______________
            {TASKDATA}
            _______________
            INSTRUCTIONS:
            you are a function calling agent. 
            you will give only arguments of function in JSON. 
            i will provide you some context. 
            from this context you need to generate function arguments. 
            strictly follow my instructions in bottom. 
            and avoid any extra outputs, only function arguments.

            { {...} }
            """,
        },
        {
            "role": "user",
            "content": f"""

            TASK : using edit file

            """,
        },
    ],
    stream=True,
    # format="json",
    options={
        "num_predict": 1000,
        # "use_mmap": False,
        # "repeat_last_n": -1,
        "num_ctx": 1024 * 16,
        # "mirostat": 2,
        # "mirostat_eta": 0.2,
        # "mirostat_tau": 2,
        # "temperature": 0.5,
        # "repeat_penalty": 1.25,
    },
)
for w in r:
    print(w['message']['content'], end="")
