from abc import ABC, abstractmethod
from typing import List, TypedDict

class Host(TypedDict):
    mac: str
    name: str

class Router(ABC):
    def __init__(self, host, port, user, password):
        self.host = host
        self.port = port
        self.user = user
        self.password = password

    @abstractmethod
    def get_active_hosts(self) -> List[Host]:
        pass
