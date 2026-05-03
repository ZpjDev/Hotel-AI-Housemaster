from abc import ABC, abstractmethod
from typing import Dict


class PhoneProviderBase(ABC):
    """电话 Provider 抽象基类"""

    @abstractmethod
    async def handle_inbound_call(self, payload: Dict) -> Dict:
        pass

    @abstractmethod
    async def transcribe_call(self, audio_url: str) -> str:
        pass

    @abstractmethod
    async def answer_question(self, call_text: str, hotel_id: int) -> str:
        pass

    @abstractmethod
    async def transfer_to_human(self, reason: str) -> Dict:
        pass

    @abstractmethod
    async def test_connection(self) -> Dict:
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass
