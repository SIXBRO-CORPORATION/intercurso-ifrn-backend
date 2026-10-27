import json
import logging
from typing import Dict, List, Optional

import firebase_admin
from firebase_admin import credentials, exceptions, messaging

from core.messaging.push_sender_port import PushSenderPort
from domain.exceptions.business_exception import BusinessException
from domain.messaging.push_send_result import PushSendResult
from messaging.configuration.config import messaging_settings

logger = logging.getLogger(__name__)

_FIREBASE_APP_NAME = "messaging"


def _build_credential() -> credentials.Certificate:
    if messaging_settings.firebase_credentials_path:
        return credentials.Certificate(messaging_settings.firebase_credentials_path)

    if messaging_settings.firebase_credentials_json:
        try:
            cert_info = json.loads(messaging_settings.firebase_credentials_json)
        except json.JSONDecodeError as e:
            raise BusinessException(
                f"FIREBASE_CREDENTIALS_JSON não é um JSON válido: {str(e)}"
            )
        return credentials.Certificate(cert_info)

    raise BusinessException(
        "Credencial do Firebase não configurada: defina FIREBASE_CREDENTIALS_PATH "
        "ou FIREBASE_CREDENTIALS_JSON"
    )


def _get_firebase_app() -> firebase_admin.App:
    try:
        return firebase_admin.get_app(_FIREBASE_APP_NAME)
    except ValueError:
        return firebase_admin.initialize_app(
            _build_credential(), name=_FIREBASE_APP_NAME
        )


class FCMPushSenderAdapter(PushSenderPort):

    def __init__(self):
        self._app = _get_firebase_app()

    async def send(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
    ) -> PushSendResult:
        if not tokens:
            return PushSendResult()

        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            tokens=tokens,
        )

        try:
            response = await messaging.send_each_for_multicast_async(
                message, app=self._app
            )
        except exceptions.FirebaseError as e:
            logger.error("Falha ao enviar push via FCM: %s", e)
            raise BusinessException(f"Erro ao enviar push notification: {str(e)}")

        invalid_tokens = [
            tokens[i]
            for i, resp in enumerate(response.responses)
            if not resp.success and isinstance(resp.exception, messaging.UnregisteredError)
        ]

        return PushSendResult(
            success_count=response.success_count,
            failure_count=response.failure_count,
            invalid_tokens=invalid_tokens,
        )

    async def send_to_topic(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
    ) -> None:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            topic=topic,
        )

        try:
            await messaging.send_async(message, app=self._app)
        except exceptions.FirebaseError as e:
            logger.error("Falha ao enviar push de broadcast (tópico %s): %s", topic, e)
