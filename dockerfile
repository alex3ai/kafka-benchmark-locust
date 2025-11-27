# Dockerfile

# 1. Começamos com a imagem oficial do Locust
FROM locustio/locust

# 2. INSTALAÇÃO DAS DEPENDÊNCIAS DE SISTEMA (A CORREÇÃO)
#    - build-essential: Instala o compilador C/C++ (gcc, make, etc.)
#    - python3-dev: Instala os headers de desenvolvimento do Python
#    - librdkafka-dev: Instala a biblioteca C do Kafka que o pip precisa para compilar
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    librdkafka-dev

# 3. Copiamos nosso arquivo de dependências para dentro da imagem
COPY src/requirements.txt /requirements.txt

# 4. Agora sim, executamos o pip para instalar as bibliotecas
#    Ele encontrará as ferramentas de compilação e terá sucesso.
RUN pip install --no-cache-dir -r /requirements.txt