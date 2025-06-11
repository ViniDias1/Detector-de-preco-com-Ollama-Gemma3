#!/bin/sh

# Inicia o servidor Ollama em background
ollama serve &

# Aguarda o servidor iniciar
sleep 5

# Baixa o modelo
ollama pull gemma3:4b

# Mantém o servidor rodando em foreground
fg %1