import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from groq import Groq


app = FastAPI()
app.mount("/", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return {"message": "Hello changes"}


@app.post("/chat/{llm_name}")
async def chat(llm_name):

    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "anshul is a poet, is it true?",
            },
            {
                "role": "user",
                "content": "what did i ask?",
            },
        ],
        model="llama3-8b-8192",
    )
    return chat_completion
    # print(chat_completion.choices[0].message.content)


if __name__ == "__main__":
    uvicorn.run('main:app', host="127.0.0.1", port=1900, reload=True)
