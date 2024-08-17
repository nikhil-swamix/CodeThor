# import os
from typing import Any, Dict, List, overload, Literal, cast, AnyStr
import os, re
from datetime import datetime
from .utils import jsonify
from .utils.LLMENUMS import AvailModels
import sys

terminal_file = open("terminal.txt", "w")
original_write = sys.stdout.write


def writer(*args):
    original_write(*args)  # Write to the original stdout
    terminal_file.write(''.join(map(str, args)))  # Write to the terminal.txt file
    terminal_file.flush()  # Make sure the write is persisted


sys.stdout.write, sys.stderr.write = writer, writer


def simple_msgs(msgs: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [{"role": r, "content": re.sub(r"\s+", " ", c)} for m in msgs for r, c in m.items()]


class Client:
    """
    ## Providers
    - anthropic
    - openai
    - deepseek
    - deepinfra
    - google
    """

    def __init__(
        self,
        model: AvailModels,
        **kwargs,
    ) -> None:
        ...
        self.provider = model.split("|")[0]
        self.model = model.split("|")[1]
        self.openai_canonical = ['openai', 'deepseek', "deepinfra", "groq", "ollama"]

    def chat(self, messages, system="", outfile=None, max_tokens=4096, temperature=0.5, stream=False, **kwargs) -> Any:
        from openai import OpenAI
        from anthropic import Anthropic

        if any(role in messages[0] for role in ['user', 'assistant', 'system']):  # swamix simple message format
            messages = simple_msgs(messages)

        if system and self.provider in self.openai_canonical:
            messages = [{"role": "system", "content": system}] + messages
            # print(messages)
        kwargs["max_tokens"], kwargs["temperature"], kwargs["messages"] = max_tokens, temperature, messages

        match self.provider:
            case "openai":
                self.client_oai: OpenAI = OpenAI()
                return self.client_oai.chat.completions.create(model=self.model, **kwargs).choices[0].message.content

            case "anthropic":

                return Anthropic().messages.create(model=self.model, system=system, **kwargs).content[0].text

            case "deepseek":
                self.client_deepseek: OpenAI = OpenAI(
                    base_url="https://api.deepseek.com", api_key=os.environ.get("DEEPSEEK_API_KEY")
                )
                if stream:
                    return self._stream_openai_responses(self.client_deepseek, model=self.model, **kwargs)
                return (
                    self.client_deepseek.chat.completions.create(model=self.model, **kwargs).choices[0].message.content
                )
            case "ollama":
                self.client: OpenAI = OpenAI(base_url="http://localhost:11434/v1")
                if stream:
                    return self._stream_openai_responses(self.client, model=self.model, **kwargs)
                return self.client.chat.completions.create(model=self.model, **kwargs).choices[0].message.content

            case "deepinfra":
                self.client_dpi: OpenAI = OpenAI(
                    base_url="https://api.deepinfra.com/v1/openai", api_key=os.environ.get("DEEPINFRA_API_KEY")
                )
                if stream:
                    return self._stream_openai_responses(self.client_dpi, model=self.model, **kwargs)
                return self.client_dpi.chat.completions.create(model=self.model, **kwargs).choices[0].message.content

            case "google":
                from google.generativeai import GenerativeModel

                # TODO: implement google stream

    def _stream_openai_responses(self, client, **kwargs):
        from openai import OpenAI

        response = client.chat.completions.create(
            stream=True, extra_body={"options": {"main_gpu": -1, "low_vram": True}}, **kwargs
        )
        for res in response:
            # print(res)
            yield res.choices[0].delta.content


if __name__ == "__main__":
    from utils import tools, count_tokens
    import json

    # CONTEXT = tools.get_youtube_transcript("gaWxyWwziwE")
    CONTEXT = ""
    SYS = f"""
    you are an openAPI spec generator V3, give optimal response.
    # CONTEXT:\n 
    {CONTEXT}
    """
    # print((CONTEXT))
    # CONTEXT = 'tools.get_youtube_transcript("wiLJ1-cQgFM")'
    resp = Client("deepseek|deepseek-coder").chat(
        system=SYS,
        messages=[
            {
                "user": """
                give a schema for orders for ecommerce
                """
            },
        ],
        stream=True,
        max_tokens=2048,
    )
    # for r in resp:
    #     print(r)

    os.system("code output.md")
    open("output.md", "w")
    for r in resp:
        if r:
            open("output.md", "a+").write(r)
