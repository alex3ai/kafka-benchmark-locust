# 1. Começamos com a imagem oficial do Locust
FROM locustio/locust:latest

# 2. MUDANÇA CRÍTICA: Trocamos para o usuário ROOT para ter permissão de instalar pacotes
USER root

# 3. Instalamos as dependências de compilação (gcc, python-dev, librdkafka)
#    Isso resolve o erro "command 'gcc' failed" e o erro "Permission denied"
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

# 4. Voltamos para o usuário padrão do Locust (Boas práticas de segurança)
USER locust

# 5. Copiamos o arquivo e instalamos as bibliotecas Python
COPY src/requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt