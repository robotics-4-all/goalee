from pydantic import BaseModel


class Broker(BaseModel):
    pass

class MQTTBroker(Broker):
    host: str = "localhost"
    port: int = 1883
    username: str = ""
    password: str = ""


class AMQPBroker(Broker):
    vhost: str = "/"
    topicExchange: str = "amq.topic"
    host: str = "localhost"
    port: int = 5672
    username: str = "guest"
    password: str = "guest"


class RedisBroker(Broker):
    db: int = 0
    host: str = "localhost"
    port: int = 6379
    username: str = ""
    password: str = ""
