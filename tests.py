from codethor import uaiclient

print(
    uaiclient.Client('ollama|codeqwen').chat(
        [{"user": 'tell me about advance software developemnt with python and advance syntax  examples only 200 words'}]
    )
)
