import os
import re
import smtplib
import ssl
import mimetypes
import getpass
from typing import List
from email.message import EmailMessage


def infer_name_from_email(email: str) -> str:
    """Prova a ricavare il nome dal local-part dell'email.
    Esempi: 'm.rossi@uni.it' -> 'Rossi' (o 'Rossi' se iniziale), 'mario.rossi@..' -> 'Mario'.
    In mancanza, ritorna 'Professore'.
    """
    local = email.split("@")[0]
    tokens = re.split(r"[._\-+]", local)
    tokens = [t for t in tokens if t and not t.isdigit()]
    if not tokens:
        return "Professore"
    name = tokens[0]
    # Se è un'iniziale (es. "m"), prova a usare il token successivo
    if len(name) == 1 and len(tokens) >= 2:
        name = tokens[1]
    name = re.sub(r"\d+", "", name)
    return name.capitalize() if name else "Professore"


BODY_TEMPLATE = """Gentile Professor {nome},

Sono Luca Francese, associato dell’Area Risorse Umane di JETOR Consulting, la Junior Enterprise dell’Università degli Studi di Roma Tor Vergata.

Qualora non ne fosse a conoscenza, JETOR Consulting è un’organizzazione no-profit gestita da studenti di Tor Vergata che offre un’ampia gamma di servizi di management consulting alle PMI. L’associazione nasce e opera con la finalità di ridurre il divario esistente tra il mondo accademico e quello lavorativo. Grazie a JETOR, gli studenti stessi hanno la possibilità di relazionarsi in prima persona con le imprese ed erogare servizi, arricchendo costantemente il proprio bagaglio formativo in un contesto giovane e challenging.

Con la presente, tengo a informarLa che apriremo a breve le candidature (20 febbraio) per il recruitment che avrà luogo a marzo 2023. Per presentarci e per far conoscere la nostra realtà agli studenti del Suo corso, vorrei chiederLe la possibilità di tenere una breve presentazione dell'associazione, utilizzando cinque minuti (ad inizio/fine) di lezione.

Certi della sua collaborazione, La ringrazio per la Sua disponibilità e rimango a Sua completa disposizione per ulteriori delucidazioni. Le lascio inoltre, in allegato, una breve brochure informativa.

Cordiali saluti,

Francese Luca
"""


SUBJECT = "Richiesta breve presentazione in aula - JETOR Consulting"
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("EMAIL_USER") or os.getenv("SENDER_EMAIL") or "la-tua-email@example.com"

# Aggiungi qui eventuali allegati (percorsi a file esistenti)
ATTACHMENTS: List[str] = [
    # "brochure.pdf",
]


def build_message(sender: str, recipient: str, subject: str, body_text: str, attachments: List[str]) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body_text, subtype="plain", charset="utf-8")

    for path in attachments:
        if not os.path.isfile(path):
            print(f"Avviso: allegato non trovato: {path}")
            continue
        ctype, encoding = mimetypes.guess_type(path)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        with open(path, "rb") as f:
            data = f.read()
        msg.add_attachment(
            data,
            maintype=maintype,
            subtype=subtype,
            filename=os.path.basename(path),
        )
    return msg


def send_bulk(messages: List[EmailMessage], server: str, port: int, username: str, password: str) -> None:
    context = ssl.create_default_context()
    with smtplib.SMTP(server, port) as smtp:
        smtp.ehlo()
        smtp.starttls(context=context)
        smtp.ehlo()
        smtp.login(username, password)
        for msg in messages:
            smtp.send_message(msg)
    print(f"Inviate {len(messages)} email.")


def main():
    sender = "marcofrancese08@gmail.com"
    if not sender or "example.com" in sender:
        raise SystemExit("Configura la tua email mittente in EMAIL_USER o SENDER_EMAIL.")

    password = os.getenv("EMAIL_PASS") or getpass.getpass(f"Password per {sender}: ")

    # Inserisci qui la lista dei destinatari
    recipients = [
        # "nome.cognome@universita.it",
    ]

    if not recipients:
        raise SystemExit("Aggiungi almeno un destinatario nella lista 'recipients'.")

    messages: List[EmailMessage] = []
    for rcpt in recipients:
        nome = infer_name_from_email(rcpt)
        body = BODY_TEMPLATE.format(nome=nome)
        msg = build_message(sender, rcpt, SUBJECT, body, ATTACHMENTS)
        messages.append(msg)

    send_bulk(messages, SMTP_SERVER, SMTP_PORT, sender, password)


if __name__ == "__main__":
    main()

