
---
# 💰 Detector de Preços com Ollama + Gemma3

Este projeto é uma aplicação de TCC que permite identificar e extrair automaticamente os preços de produtos em imagens usando modelos de linguagem via **Ollama**.

A interface gráfica foi construída com `Tkinter`, e toda a aplicação (incluindo o servidor Ollama) roda 100% via **Docker**, garantindo portabilidade e reprodutibilidade para qualquer usuário.

---

## 📦 Tecnologias Utilizadas

- [Python 3.10+](https://www.python.org/)
- [Tkinter](https://docs.python.org/3/library/tkinter.html) (GUI)
- [Ollama](https://ollama.com/) (gerenciador de modelos LLM locais)
- Modelo `gemma3:4b` da Ollama
- Docker e Docker Compose

---

## 🖼️ O que a aplicação faz?

1. Você seleciona uma imagem da pasta local `app/imagens`.
2. A aplicação converte a imagem para base64 e envia ao modelo `gemma3:4b` via API.
3. O modelo retorna os preços encontrados na imagem (ex: `R$ 9,99`, `R$ 12,50`).
4. Os resultados são exibidos diretamente na interface.

---

## 🚀 Como rodar o projeto

### 1. Pré-requisitos

- Docker instalado: [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)
- Docker Compose
- (Windows) WSL2 ativado e funcional

> **Importante:** O projeto baixa o modelo **apenas na primeira execução**. Isso pode demorar alguns minutos (~1GB).

---

### 2. Clone o repositório

```bash
git clone https://github.com/seu-usuario/seu-repo.git
cd seu-repo
---

### 3. Execute o projeto com Docker Compose

```bash
docker compose up --build
```

A primeira vez pode demorar pois o modelo `gemma3:4b` será baixado.

---

## 🗂️ Estrutura do Projeto

```
.
├── docker-compose.yml
├── app/
│   ├── main.py               # Interface gráfica com Tkinter
│   ├── imagens/              # Pasta onde você coloca suas imagens
│   └── Dockerfile            # Dockerfile da aplicação Python
├── ollama/
│   ├── entrypoint.sh         # Script para iniciar servidor Ollama e baixar o modelo
│   └── Dockerfile            # Dockerfile do Ollama + Gemma3
├── docker-compose.yml        # Docker Compose
└── README.md
```

---

## 🛠️ Como funciona por dentro?

* O serviço **`ollama`** é iniciado com um `entrypoint.sh` que:

  * Inicia o servidor
  * Baixa o modelo `gemma3:4b` (caso ainda não tenha)
  * Mantém o servidor ativo
* O serviço **`app`** (interface) conecta-se à porta `11434` e envia imagens convertidas em base64 para o modelo
* Tudo é feito localmente: **sem nuvem**, sem API externa

---

## 🖼️ Como adicionar imagens?

1. Coloque arquivos `.png`, `.jpg` ou `.jpeg` na pasta `app/imagens`
2. Ao abrir a interface, clique em **Selecionar Imagem**
3. A janela abrirá direto nesta pasta
4. A imagem é exibida e os preços são extraídos automaticamente

---

## 🧪 Testado em

* ✅ Ubuntu 22.04 (WSL2 e nativo)
* ✅ Windows 11 com WSL2 + Docker Desktop
* ✅ Docker 24+

---

## 💡 Dicas úteis

* Após a primeira execução com `--build`, você pode rodar mais rápido com:

```bash
docker compose up
```

* Para garantir que tudo está limpo antes de um rebuild:

```bash
docker compose down --volumes
docker compose up --build
```

---

## 🧼 Como parar?

```bash
CTRL+C
docker compose down
```

---


