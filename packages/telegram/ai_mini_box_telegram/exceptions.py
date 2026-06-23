class TelegramAPIError(Exception):
    def __init__(self, description: str, status_code: int = 0):
        self.description = description
        self.status_code = status_code
        super().__init__(f"Telegram API error ({status_code}): {description}")
