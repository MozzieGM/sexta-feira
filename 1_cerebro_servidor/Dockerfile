# ============================================================
# SEXTA-FEIRA — Dockerfile do Cérebro Central
# ============================================================
# Imagem leve baseada em Python 3.11 para máxima compatibilidade.
# Funciona em x86_64 (Windows/Linux) e ARM (Raspberry Pi).
# ============================================================

FROM python:3.11-slim

# Metadados do container
LABEL maintainer="Mozzie — Projeto Sexta-Feira"
LABEL description="Cérebro da Sexta-Feira: API de IA com FastAPI"

# Variáveis de ambiente padrão
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Diretório de trabalho dentro do container
WORKDIR /app

# Instala dependências do sistema necessárias para edge-tts e networking
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python primeiro (cache de camadas Docker)
COPY app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o código-fonte da aplicação
COPY app/ /app/

# Expõe a porta da API
EXPOSE 8000

# Comando de inicialização — Uvicorn com hot-reload em dev
CMD ["uvicorn", "main_server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
