"""Porta do serviço de "tickets" de curta duração para autenticar conexões SSE.

Ver seção 4, cuidado de segurança #1 da solução técnica: como o `EventSource`
do navegador não permite enviar headers customizados, o token de acesso
principal (Bearer JWT de longa duração, usado no resto da API) NUNCA deve
trafegar na query string do `GET` de SSE �?" isso vaza em logs de acesso,
proxies e histórico do navegador.

Em vez disso, o cliente primeiro chama um endpoint REST autenticado (com o
Bearer token normal, no header, como qualquer outro endpoint) para trocar sua
sessão por um "ticket": um token de curtíssima duração e escopo único
(um `match_id`/`season_id` específico), feito só para abrir UMA conexão SSE.
Esse ticket é o único segredo que vai na query string do `GET` de SSE.
"""

from abc import ABC, abstractmethod
from uuid import UUID


class InvalidLiveTicketError(Exception):
    """Ticket ausente, expirado, malformado, ou com escopo que não confere com o canal."""


class LiveTicketPort(ABC):
    @abstractmethod
    def issue_ticket(self, user_id: UUID, channel: str) -> str:
        """Emite um ticket de uso único, válido só para `channel`, de curta duração."""

    @abstractmethod
    def verify_ticket(self, ticket: str, channel: str) -> UUID:
        """Valida o ticket para o `channel` informado e retorna o `user_id` dono dele.

        Levanta `InvalidLiveTicketError` se o ticket for inválido, expirado,
        ou tiver sido emitido para um canal diferente do informado.
        """
