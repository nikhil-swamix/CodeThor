import os, re
import requests


def get_openai_models():
    """
    {
    "object": "list",
    "data": [
        {
            "id": "dall-e-3",
            "object": "model",
            "created": 1698785189,
            "owned_by": "system"
        },
        {
            "id": "gpt-4-1106-preview",
            "object": "model",
            "created": 1698957206,
            "owned_by": "system"
        },
        {
            "id": "dall-e-2",
            "object": "model",
            "created": 1698798177,
            "owned_by": "system"
        },
        {
            "id": "tts-1-hd-1106",
            "object": "model",
            "created": 1699053533,
            "owned_by": "system"
        },
        {
    """
    url = "https://api.openai.com/v1/models"
    headers = {'Authorization': 'Bearer {}'.format(os.environ['OPENAI_API_KEY'])}
    resp = requests.get(url, headers=headers).json()
    models = sorted(resp['data'], key=lambda d: d['created'], reverse=True)
    models = [d['id'] for d in models if "gpt" in d['id']]
    models = sorted(models, key=lambda s: len(s.split('-')))  # sort by length of alphanumeric only string
    return [f"openai|{m}" for m in models]


def get_anthropic_models():
    return [
        f'anthropic|{m}'
        for m in [
            "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]
    ]


def get_deepseek_models():
    return ["deepseek|deepseek-chat", "deepseek|deepseek-coder"]


def get_deepinfra_models():
    url = "https://api.deepinfra.com/deploy/list?status=running"
    models = requests.get(url, headers={"Authorization": f"Bearer {os.environ['DEEPINFRA_API_KEY']}"}).json()
    return [f'deepinfra|{x["model_name"]}' for x in models]


def get_ollama_models():
    url = "http://localhost:11434/api/tags"

    return [f"ollama|{x['name']}" for x in requests.get(url).json()['models']]


def burn(literals=[], f="LLMENUMS.py"):
    joins = ",\n".join([f'\t"{x}"' for x in literals])
    template = f"""from typing import Literal
AvailModels = Literal[
{joins}
    "google|gemini-1.5-flash",
    "google|gemini-1.5-pro",
]
"""
    open(f, "w").write(template)


if __name__ == "__main__":
    print()
    burn(
        [
            *get_openai_models(),
            *get_anthropic_models(),
            *get_deepseek_models(),
            *get_deepinfra_models(),
            *get_ollama_models(),
        ],
        f="LLMENUMS.py",
    )
    # print()
