from llama_cpp import Llama
import os
from utils import make_filetag
import time

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# filetags = "\n".join([make_filetag(x, wrapper="tag") for x in os.listdir() if os.path.isfile(x)])
# print(filetags)

# model_id = r"D:\Models\llama-262k\Llama-3-8B-Instruct-262k.Q4_1.gguf"
# model_id = r"D:\Models\Bartowski\Meta-Llama-3-8B-Instruct-Q8_0.gguf"
model_id = r"D:\Models\llama3\Meta-Llama-3-8B-Instruct-Q6_K.gguf"
# model_id = r"D:\Models\Bartowski\Meta-Llama-3-8B-Instruct-Q8_0.gguf"
TASKDATA = open('./TASK-REFACTOR.txt').read()
llm = Llama(
    model_path=model_id,
    n_gpu_layers=-1,
    # seed=1338,
    n_ctx=1024 * 2,
    # kv_overrides={"tokenizer.ggml.pre": "llama3"},
    # chat_template="llama3",
    chat_format="llama-3",
    use_mmap=False,
    flash_attn=True,
    # split_mode=1,
    tensor_split=[8, 13],
    # main_gpu=1,
    # verbose=False,
)

t = time.time()
output = llm.create_chat_completion(
    messages=[
        {
            "role": "system",
            "content": f"""only required output""",
        },
        {
            "role": "user",
            "content": f""" QUERY: write a 100 word article for nikhil and its meaning""",
        },
    ],
    # mirostat_mode=2,
    # mirostat_tau=8,
    # mirostat_eta=0.1,
    # max_tokens=512,
    response_format={
        "type": "json_object",
    },
    temperature=0.2,
)
# print(output)

print(output["choices"][0]["message"]["content"])
print(time.time() - t)
