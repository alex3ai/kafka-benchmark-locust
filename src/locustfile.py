import time
import json
import random
import os
from locust import User, task, events, constant_pacing
from confluent_kafka import Producer

# --- CONFIGURAÇÃO ---
# Pega valores das Variáveis de Ambiente (Segurança e Flexibilidade)
BOOTSTRAP_SERVER = os.getenv("KAFKA_BOOTSTRAP")
SASL_USER = os.getenv("SASL_USER", "locust-user")
SASL_PASSWORD = os.getenv("SASL_PASSWORD")
TOPIC = "benchmark-logs"

# Configuração Tuning do Kafka Producer
# Baseado em: https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md
CONF = {
    'bootstrap.servers': BOOTSTRAP_SERVER,
    'security.protocol': 'SASL_PLAINTEXT',
    'sasl.mechanism': 'SCRAM-SHA-512',
    'sasl.username': SASL_USER,
    'sasl.password': SASL_PASSWORD,
    'client.id': 'locust-benchmark',
    
    # OTIMIZAÇÃO DE THROUGHPUT (Vazão)
    'linger.ms': 10,           # Aguarda até 10ms para encher um lote (batch)
    'batch.size': 65536,       # Tamanho máximo do lote: 64KB
    'compression.type': 'lz4', # Compactação rápida (economiza rede)
    'acks': '1',               # 1 = Líder confirma (Rápido). 'all' = Lento/Seguro.
    'queue.buffering.max.messages': 100000, # Fila local grande para não travar
}

class KafkaClient:
    """Cliente Kafka Wrapper para reportar métricas ao Locust"""
    def __init__(self):
        self.producer = Producer(CONF)

    def on_delivery(self, err, msg, start_time):
        """Callback executado quando o Kafka confirma o recebimento"""
        duration = (time.time() - start_time) * 1000  # Em milissegundos
        if err:
            events.request.fire(request_type="KAFKA", name="produce_error", response_time=duration, exception=err)
            # print(f"Erro Kafka: {err}") # Descomente para debug (pode poluir o terminal)
        else:
            # Sucesso! Reporta ao Locust
            events.request.fire(request_type="KAFKA", name="produce_ok", response_time=duration, response_length=len(msg.value()))

    def send(self, msg):
        start_time = time.time()
        try:
            # Envio Assíncrono: O código não para aqui!
            self.producer.produce(
                TOPIC, 
                json.dumps(msg).encode('utf-8'), 
                callback=lambda err, m: self.on_delivery(err, m, start_time)
            )
            # Poll(0) serve para disparar os callbacks pendentes sem bloquear
            self.producer.poll(0)
        except BufferError:
            # Se a fila local encher (produzindo mais rápido que a rede aguenta)
            events.request.fire(request_type="KAFKA", name="local_buffer_full", response_time=0, exception=Exception("Buffer Full"))
            self.producer.poll(0.1) # Dá um respiro para a fila esvaziar
        except Exception as e:
            events.request.fire(request_type="KAFKA", name="exception", response_time=0, exception=e)

    def flush(self):
        """Força o envio de mensagens pendentes ao parar"""
        self.producer.flush(timeout=5)

class KafkaUser(User):
    """Simula um dispositivo/usuário gerando logs"""
    abstract = True
    client = None

    def on_start(self):
        # Singleton: Usa o mesmo cliente Kafka para economizar conexões
        if not KafkaUser.client:
            KafkaUser.client = KafkaClient()

    def on_stop(self):
        # Ao encerrar o teste, garante que tudo foi enviado
        if KafkaUser.client:
            KafkaUser.client.flush()

    # Mantém uma cadência constante (Pacing)
    # Tenta executar a tarefa a cada 0.01 segundos (simulando alta frequência)
    wait_time = constant_pacing(0.01) 

    @task
    def send_log(self):
        # Gera um log simulado de ~1KB
        payload = {
            "sensor_id": random.randint(1, 5000),
            "temperature": random.uniform(20.0, 100.0),
            "status": "OK",
            "timestamp": time.time(),
            "heavy_payload": "x" * 1024 # Payload dummy para gerar tráfego
        }
        KafkaUser.client.send(payload)