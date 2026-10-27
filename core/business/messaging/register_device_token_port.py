from core.command import Command
from domain.messaging.device_token import DeviceToken


class RegisterDeviceTokenPort(Command[DeviceToken]):
    pass
