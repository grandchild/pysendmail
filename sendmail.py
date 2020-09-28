#!/usr/bin/env python3
# CC0 - free software.
# To the extent possible under law, all copyright and related or neighboring rights to
# this work are waived.
"""
A simple Mail class (and CLI), wrapping Python's :py:mod:`smtplib`.

The only login/transport security mode supported is STARTTLS.

Run `sendmail.py -h` to see CLI help.

Python usage:

First, create a MailSender object to be able to send mail:

>>> sender = MailSender(
...     user="me@example.com",
...     password="s3cr3t",
...     server="smtp.example.com",
...     from_="Me <me@example.com>"
... )

Create and send and an email like so:

>>> mail = Mail(
...     sender,
...     'recipient@example.com',
...     'subject',
...     'hello,\\nthis is email.\\nthanks!'
... )
>>> mail.send()
True

You can attach files like this:

>>> with open('attachment.png', 'rb') as f:
...     data = f.read()
... Mail(
...     sender,
...     'recipient@example.com',
...     'subject',
...     'hello,\\nthis is email with image.\\nthanks!',
...     {'different_name.png': data}
... ).send()
True

You can send blind copies (BCC) to a list of email addresses:

>>> Mail(
...     sender,
...     'recipient@example.com',
...     'subject',
...     'hello,\\nthis is email.\\nthanks!',
...     bcc=['alice@example.com', 'bob@example.com']
... ).send()
True

The :py:meth:`Mail.send` function returns `False` if something went wrong, and errors
will be printed to stdout.
"""
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders
import smtplib
import time
from typing import Optional


class MailSender:
    """
    Represent an email sender, with email server.

    Args:
        user (str): The login name to the email server, usually the from email address.
        password (str): The server login password for the user.
        server (str): The SMTP server hostname.
        from_ (Optional[str]): The display name of the sender. Used for the FROM email
            header field. If not given, *user* will be used.
        reply_to (Optional[str]): Replies should go to this email address instead of the
            sender email.
    """

    def __init__(self, user, password, server, from_=None, reply_to=None):
        self.user = user
        self.password = password
        self.server = server
        self.from_ = from_
        self.reply_to = reply_to


class Mail:
    """
    Create an email.

    Args:
        to (Union[str, List[str]]): A single email address or a list of addresses
            to send to.
        subject (str): Email subject line
        text (str): The email text
        attachments (Mapping[string, bytes]): A filename and the content encoded as
            a bytes-sequence.
        bcc (Union[str, List[str]]): A single email address or a list of addresses
            to BCC the email to.
        reply_to (str): An email address for the "Reply-To" header (Email clients
            will automatically reply to this instead of the sender address).
        custom_to_header (str): A custom "To" header string for addressee display.
    """

    def __init__(
        self,
        sender,
        to,
        subject="",
        text="",
        attachments=None,
        bcc=None,
        reply_to=None,
        custom_to_header=None,
        root_msg_mime_subtype="mixed",
    ):
        self.sender = sender
        if attachments is None:
            attachments = {}
        if to is None:
            raise ValueError("Mail: No recipient given")
        self.msg = MIMEMultipart(root_msg_mime_subtype)
        self.msg.attach(MIMEText(text))
        if attachments:
            for name, filedata in attachments.items():
                attachment_part = MIMEBase("application", "octet-stream")
                attachment_part.set_payload(filedata)
                encoders.encode_base64(attachment_part)
                attachment_part.add_header(
                    "Content-Disposition", 'attachment; filename="{}"'.format(name)
                )
                self.msg.attach(attachment_part)

        if isinstance(to, str):
            self.to = [to]
        else:  # assume list
            self.to = to
        if bcc is None:
            self.bcc = []
        elif isinstance(bcc, str):
            self.bcc = [bcc]
        else:  # assume list
            self.bcc = bcc
        self.msg["Subject"] = subject
        self.msg["To"] = (
            ",".join(self.to) if custom_to_header is None else custom_to_header
        )
        self.msg["From"] = self.sender.from_ or self.sender.user
        self.msg["Reply-To"] = (
            reply_to
            if reply_to
            else self.sender.reply_to
            if self.sender.reply_to
            else self.sender.from_
        )
        # Fri, 25 Sep 2020 15:41:09 +0200 (CEST)
        self.msg["Date"] = (
            datetime.now(timezone.utc)
            .astimezone()
            .strftime("%a, %d %b %Y %H:%M:%S %z (%Z)")
        )

    def send(self, retries=3):
        """
        Send the email.

        Args:
            retries (int): How often to retry in case of errors. The wait time
                between tries increases quadratically in seconds. For e.g.
                retries=3 wait times would be 0s, 1s and 4s. Actual wait times
                may be much larger due to network timeouts etc.

        Returns:
            True on successful send, False on failure.
        """
        tries = 0
        to = self.to + self.bcc
        if to:
            success = False
            while not success and tries < retries:
                try:
                    smtpserver = smtplib.SMTP(self.sender.server)
                    smtpserver.ehlo()
                    smtpserver.starttls()
                    smtpserver.ehlo()
                    smtpserver.login(self.sender.user, self.sender.password)
                    smtpserver.sendmail(self.sender.user, to, self.msg.as_string())
                except smtplib.SMTPAuthenticationError:
                    print("Failed sending: Authentication Error")
                    time.sleep(tries)
                    tries += 1
                except OSError as err:
                    print(
                        "Failed sending to <{}> {}: {} (waiting {}s)".format(
                            self.to,
                            ["once", "twice", "{} times"][min(tries, 2)].format(
                                tries + 1
                            ),
                            err,
                            tries ** 2,
                        )
                    )
                    time.sleep(tries ** 2)
                    tries += 1
                else:
                    success = True
                finally:
                    try:
                        # noinspection PyUnboundLocalVariable
                        smtpserver.close()
                    except UnboundLocalError:
                        pass
            return success
        else:
            print("No mail adresses given, no mails sent.")
            return True

    def __str__(self):
        return self.msg.as_string()


###
### CLI interface
###

if __name__ == "__main__":

    from argparse import ArgumentParser
    from getpass import getpass
    import os
    import sys

    DESCRIPTION = """Send Email"""

    def main():
        argparser = ArgumentParser(description=DESCRIPTION)
        argparser.add_argument("-s", "--subject", default="", help="email subject")
        argparser.add_argument("-c", "--content", default="", help="email content")
        argparser.add_argument(
            "-m", "--server", required=True, help="SMTP server to use for sending"
        )
        argparser.add_argument(
            "-u", "--user", required=True, help="user login (usually the sender email)"
        )
        argparser.add_argument(
            "-p", "--password", action="store_true", help="ask for server password"
        )
        argparser.add_argument(
            "-t", "--to", nargs="+", required=True, help="recipient email(s)"
        )
        argparser.add_argument("-b", "--bcc", nargs="*", help="BCC recipient email(s)")
        argparser.add_argument(
            "-a", "--attach", nargs="+", default=[], help="attachment(s)"
        )
        argparser.add_argument(
            "-f",
            "--from",
            help="from name (the first part in 'Sam Doe <sam@example.com>'). "
            "optional, will use the sender email if omitted.",
            dest="from_",
        )
        argparser.add_argument(
            "-r",
            "--reply-to",
            nargs="?",
            help="reply address (if different from sender)",
        )
        argparser.add_argument(
            "-n",
            "--dry-run",
            action="store_true",
            help="don't send email, just show it",
        )
        args = argparser.parse_args()

        if args.password:
            password = getpass(f"Enter password for {args.user} on {args.server}: ")
        else:
            try:
                password = os.environ["MAIL_PASSWORD"]
            except KeyError:
                print(
                    "Error: -p/--password not given and environment variable"
                    " MAIL_PASSWORD is empty",
                    file=sys.stderr,
                )
                sys.exit(1)
        sender = MailSender(args.user, password, args.server, args.from_, args.reply_to)
        attachments = {}
        for attachment in args.attach:
            try:
                with open(attachment, "rb") as f:
                    data = f.read()
                attachments[os.path.basename(attachment)] = data
            except Exception as err:
                print(err)
                sys.exit(1)
        mail = Mail(sender, args.to, args.subject, args.content, attachments, args.bcc)
        if args.dry_run:
            print(mail)
        else:
            mail.send()

    try:
        main()
    except KeyboardInterrupt:
        print()  # Ctrl-C most likely during password entry, so add newline
