#!/bin/zsh
exec llama-server \
    --hf-repo bartowski/Qwen2.5-7B-Instruct-GGUF \
    --hf-file Qwen2.5-7B-Instruct-Q6_K.gguf \
    "$@"
