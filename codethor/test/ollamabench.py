import time
import openai
import ollama

# Define the prompt
prompt = "create a django application one file for news cms"


# Function to send request to OpenAI and measure time
def benchmark_openai_request():
    start_time = time.time()
    response = openai.OpenAI(api_key="asas", base_url="http://127.0.0.1:11434/v1").chat.completions.create(
        model="wizardlm2:7b-q6_K", messages=[{"role": "user", "content": prompt}], stream=False, max_tokens=4096
    )
    print(response)
    end_time = time.time()
    return end_time - start_time


# Run the benchmark 10 times and calculate average time
times = []
for _ in range(1):
    times.append(benchmark_openai_request())

average_time = sum(times) / len(times)

print(f"Average time to complete request: {average_time:.2f} seconds")
