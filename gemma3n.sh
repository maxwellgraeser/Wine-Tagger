#!/bin/zsh
exec llama-server \
    --hf-repo bartowski/google_gemma-3n-E4B-it-GGUF \
    --hf-file google_gemma-3n-E4B-it-Q4_K_M.gguf \
    "$@"
