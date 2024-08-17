# uvicorn main:app --reload
$env:OLLAMA_HOST = "127.0.0.1:11433" ;  $env:CUDA_VISIBLE_DEVICES="0" ;  (ollama serve)