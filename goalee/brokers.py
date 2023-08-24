from pydantic import BaseModel


class Broker(BaseModel):
    host: str = "localhost"
    port: int = 0
    username: str = ""
    password: str = ""


class AMQPBroker(Broker):
    vhost: str = "/"
    topicExchange: str = "amq.topic"


class RedisBroker(Broker):
    db: int = 0


class MQTTBroker(Broker):
    pass
