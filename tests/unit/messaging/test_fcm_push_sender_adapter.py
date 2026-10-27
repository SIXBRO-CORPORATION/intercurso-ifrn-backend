import pytest

from domain.exceptions.business_exception import BusinessException
from messaging.adapters import fcm_push_sender_adapter as module
from messaging.configuration.config import messaging_settings


@pytest.mark.unit
class TestFCMCredentialBuilding:
    """Cobre só a lógica pura de resolução de credencial (sem inicializar
    o app do Firebase de verdade, o que exigiria rede/credenciais reais).
    """

    def test_raises_when_no_credential_is_configured(self, monkeypatch):
        monkeypatch.setattr(messaging_settings, "firebase_credentials_path", "")
        monkeypatch.setattr(messaging_settings, "firebase_credentials_json", "")

        with pytest.raises(BusinessException):
            module._build_credential()

    def test_raises_when_credentials_json_is_not_valid_json(self, monkeypatch):
        monkeypatch.setattr(messaging_settings, "firebase_credentials_path", "")
        monkeypatch.setattr(
            messaging_settings, "firebase_credentials_json", "{not-json"
        )

        with pytest.raises(BusinessException):
            module._build_credential()

    def test_prefers_path_over_json_when_both_are_set(self, monkeypatch):
        monkeypatch.setattr(
            messaging_settings, "firebase_credentials_path", "/tmp/does-not-exist.json"
        )
        monkeypatch.setattr(messaging_settings, "firebase_credentials_json", "{}")

        # Caminho é tentado primeiro; como o arquivo não existe, o erro
        # vem do SDK do Firebase (IOError), não do parse de JSON —
        # confirma que _build_credential não cai no branch do JSON.
        with pytest.raises(Exception) as exc_info:
            module._build_credential()
        assert not isinstance(exc_info.value, BusinessException)
