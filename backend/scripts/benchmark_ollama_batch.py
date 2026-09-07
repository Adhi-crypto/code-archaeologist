import time
import json
import requests
import subprocess

def get_vram_usage():
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,nounits,noheader"],
            capture_output=True, text=True, check=True
        )
        used, total = res.stdout.strip().split(",")
        return float(used.strip()), float(total.strip())
    except Exception:
        return 0.0, 0.0

def get_ram_usage():
    try:
        with open("/proc/meminfo") as f:
            lines = f.readlines()
        info = {}
        for l in lines:
            parts = l.split(":")
            if len(parts) == 2:
                info[parts[0].strip()] = int(parts[1].split()[0])
        total_kb = info.get("MemTotal", 0)
        avail_kb = info.get("MemAvailable", 0)
        used_gb = (total_kb - avail_kb) / (1024**2)
        total_gb = total_kb / (1024**2)
        return used_gb, total_gb
    except Exception:
        return 0.0, 0.0

PROMPT = (
    "Analyze the following architectural components and suggest optimization strategies:\n"
    "- Module A: Ingestion pipeline handling Git diff extraction via subprocess.\n"
    "- Module B: ChromaDB vector store indexing snapshot embeddings with dense 384-dimensional vectors.\n"
    "- Module C: Temporal RAG retriever performing positional queries and keyword re-ranking.\n"
    "- Module D: Causal reasoning engine predicting bug origins across commits.\n"
    "Provide a structured 2-paragraph summary with high-impact recommendations."
)

SYSTEM = "You are a senior software architect specializing in high-performance distributed systems."

def run_test(num_batch, num_ctx=4096, num_predict=256):
    print(f"\n--- Testing num_batch={num_batch} (num_ctx={num_ctx}, num_predict={num_predict}) ---")
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "qwen2.5-coder:7b",
        "prompt": PROMPT,
        "system": SYSTEM,
        "stream": True,
        "keep_alive": "60m",
        "options": {
            "temperature": 0.2,
            "num_predict": num_predict,
            "num_ctx": num_ctx,
            "num_batch": num_batch,
        }
    }

    vram_before, vram_total = get_vram_usage()
    ram_before, ram_total = get_ram_usage()

    t_start = time.perf_counter()
    resp = requests.post(url, json=payload, stream=True)
    t_first_token = None
    tokens = []
    final_data = {}

    for line in resp.iter_lines():
        if not line:
            continue
        chunk = json.loads(line.decode("utf-8"))
        if t_first_token is None and chunk.get("response"):
            t_first_token = time.perf_counter()
        tokens.append(chunk.get("response", ""))
        if chunk.get("done", False):
            final_data = chunk
            break

    t_end = time.perf_counter()
    vram_after, _ = get_vram_usage()
    ram_after, _ = get_ram_usage()

    ttft_ms = round((t_first_token - t_start) * 1000, 2) if t_first_token else 0
    total_time_s = round(t_end - t_start, 3)
    num_tokens = len(tokens)
    
    # Extract Ollama internal stats if present (nanoseconds to seconds/tok/s)
    prompt_eval_count = final_data.get("prompt_eval_count", 0)
    prompt_eval_duration_ns = final_data.get("prompt_eval_duration", 0)
    eval_count = final_data.get("eval_count", 0)
    eval_duration_ns = final_data.get("eval_duration", 0)

    prompt_tok_s = round(prompt_eval_count / (prompt_eval_duration_ns / 1e9), 2) if prompt_eval_duration_ns else 0
    gen_tok_s = round(eval_count / (eval_duration_ns / 1e9), 2) if eval_duration_ns else 0

    print(f"TTFT: {ttft_ms} ms")
    print(f"Total Time: {total_time_s} s")
    print(f"Generated Tokens: {eval_count} tokens")
    print(f"Prompt Eval Speed: {prompt_tok_s} tok/s ({prompt_eval_count} tokens in {round(prompt_eval_duration_ns/1e6, 1)} ms)")
    print(f"Generation Speed: {gen_tok_s} tok/s ({eval_count} tokens in {round(eval_duration_ns/1e6, 1)} ms)")
    print(f"VRAM: {vram_after:.1f} MB / {vram_total:.1f} MB (delta: {vram_after - vram_before:+.1f} MB)")
    print(f"RAM: {ram_after:.2f} GB / {ram_total:.2f} GB (delta: {ram_after - ram_before:+.2f} GB)")

    return {
        "num_batch": num_batch,
        "ttft_ms": ttft_ms,
        "total_time_s": total_time_s,
        "gen_tokens": eval_count,
        "prompt_tok_s": prompt_tok_s,
        "gen_tok_s": gen_tok_s,
        "vram_mb": vram_after,
        "ram_gb": round(ram_after, 2),
    }

if __name__ == "__main__":
    # Warmup run
    print("Warming up model...")
    run_test(num_batch=512, num_predict=10)

    results = []
    for b in [128, 256, 512]:
        res = run_test(num_batch=b, num_predict=150)
        results.append(res)

    print("\n================ BENCHMARK SUMMARY ================")
    print(f"{'num_batch':<10} | {'TTFT (ms)':<10} | {'Total Time (s)':<15} | {'Gen tok/s':<10} | {'VRAM (MB)':<10}")
    print("-" * 65)
    for r in results:
        print(f"{r['num_batch']:<10} | {r['ttft_ms']:<10} | {r['total_time_s']:<15} | {r['gen_tok_s']:<10} | {r['vram_mb']:<10}")
