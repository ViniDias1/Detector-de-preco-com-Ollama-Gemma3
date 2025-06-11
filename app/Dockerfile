FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    python3-tk \
    python3-pil.imagetk \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
