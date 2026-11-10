# SERVING-INVENTORY

- gx10 SSH reachable: yes (BatchMode true).
- GPU: NVIDIA GB10 (Blackwell), driver 580.159.03, CUDA 13.0, kernel 6.17 aarch64. VRAM total not reported by nvidia-smi (unified memory); system RAM 121 GiB.
- SGLang 0.0.0.dev1+g4ccff141d in container gx10-occamy-nvfp4, image sha256:72457f09..., port 8012->30000. Exact flags recorded (radix cache on, HiCache OFF, lmcache off).
- Weights: /home/zer0null/.cache/huggingface/.../fa865dc5..., index sha 6a072db..., tokenizer sha e9c0c634...; arch Qwen3_5MoeForConditionalGeneration hybrid linear+full attention 40 layers MoE NVFP4, ctx 131072.
- vLLM 0.22.1rc1 installed on host; occamy compatibility unknown (hybrid mamba + modelopt_fp4). CacheBlend 0.5.2 source in uv cache; occamy compat unknown. FreeToken consumer engine; occamy not listed; semantic-anchor cache unverified.
- Deliverables: pins/SERVING-INVENTORY.md, pins/serving-inventory.json, notes/ENGINE-DOCS.md. Restore command captured.