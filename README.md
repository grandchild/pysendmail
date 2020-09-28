## Send Mail from the Commandline, with Python

```shell
$ cd pysendmail
$ ␣export MAIL_PASSWORD=s3cr3t  # A leading space might prevent your password
                                # from appearing in your terminal history.
                                # (Often the case, but depends on your setup.)

# Now send an email:

$ ./sendmail.py --user me@example.com --server smtp.example.com --to you@example.org \
    --subject test --content "Hi there!"

# or, shorter:

$ ./sendmail.py -u me@example.com -m smtp.example.com -t you@example.org \
    -s test -c "Hi there!"
```


### Usage Help

```
./sendmail.py -h
usage: sendmail.py [-h] [-s SUBJECT] [-c CONTENT] -m SERVER -u USER [-p] -t TO
                   [TO ...] [-b [BCC [BCC ...]]] [-a ATTACH [ATTACH ...]]
                   [-f FROM_] [-r [REPLY_TO]] [-n]

Send Email

optional arguments:
  -h, --help            show this help message and exit
  -s SUBJECT, --subject SUBJECT
                        email subject
  -c CONTENT, --content CONTENT
                        email content
  -m SERVER, --server SERVER
                        SMTP server to use for sending
  -u USER, --user USER  user login (usually the sender email)
  -p, --password        ask for server password
  -t TO [TO ...], --to TO [TO ...]
                        recipient email(s)
  -b [BCC [BCC ...]], --bcc [BCC [BCC ...]]
                        BCC recipient email(s)
  -a ATTACH [ATTACH ...], --attach ATTACH [ATTACH ...]
                        attachment(s)
  -f FROM_, --from FROM_
                        from name (the first part in 'Sam Doe
                        <sam@example.com>'). optional, will use the sender
                        email if omitted.
  -r [REPLY_TO], --reply-to [REPLY_TO]
                        reply address (if different from sender)
  -n, --dry-run         don't send email, just show it
```


### License

[![License](https://img.shields.io/github/license/grandchild/pysendmail.svg)](
https://creativecommons.org/publicdomain/zero/1.0/)

You may use this code without attribution, that is without mentioning where it's from or
who wrote it. I would actually prefer if you didn't mention me. You may even claim it's
your own.
