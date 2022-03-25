#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This must be run in a Django environment. Make sure DEBUG is False, otherwise you're
testing the redirect."""


import os
import sys
from django.core.wsgi import get_wsgi_application
from django.conf import settings
import environ
from argparse import ArgumentParser
from django.contrib.sessions.backends.db import SessionStore

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(BASE_DIR)
sys.path.append(BASE_DIR)
os.environ['DJANGO_SETTINGS_MODULE'] = 'djnipscc.settings'
application = get_wsgi_application()
from pdb import set_trace as debug

parser = ArgumentParser()
parser.add_argument(
    "recipients", nargs="*", default='lee@eventhosts.cc lee@salk.edu',
    help="To fully test, pass in two email addresses, space separated. Only supply email not e.g Bob Smith <bob@smith.org>")
ns = parser.parse_args()

DATABASE = settings.DATABASE

from emailer import Message

env = environ.FileAwareEnv(DEBUG=(bool, False))

env_file = env('ENV_PATH', default='.env')

if isinstance(ns.recipients, list):
    recipients = ns.recipients
else:
    recipients = [ns.recipients]
    if len(recipients) == 1 and " " in recipients[0]:
        recipients = recipients[0].split()

hold = True

if hold:
    subject = "1. Testing To with an email string"
    print(subject)
    msg = Message(To=recipients[0], Subject=subject)
    result = msg.send(emailRedirect=None)

    subject = "2. Testing To with a list of one recipients"
    print(subject)
    msg = Message(To=recipients[0:1], Subject=subject)
    result = msg.send(emailRedirect=None)

    subject = "3. Testing msg.To with a list of one recipients"
    print(subject)
    msg = Message(Subject=subject)
    msg.To = recipients
    result = msg.send(emailRedirect=None)

    subject = "4. Testing 'to' lowercase with a list of one recipient"
    print(subject)
    msg = Message(to=recipients[0:1], Subject=subject)
    result = msg.send(emailRedirect=None)

    subject = "5. Testing Html with no body"
    print(subject)
    msg = Message(to=recipients,
                  Subject=subject,
                  Html="This is <strong>bold.</strong>."
                  )
    result = msg.send(emailRedirect=None)

    subject = '6. Testing text body'
    print(subject)
    msg = Message(to=recipients,
                  Subject=subject,
                  Body="This is plain text.",
                  )
    result = msg.send(emailRedirect=None)

    subject = '7. Testing msg.Body'
    print(subject)
    msg = Message(to=recipients,
                  Subject=subject,
                  )
    msg.Body = "This body was added later"
    result = msg.send(emailRedirect=None)

    subject = '8. Testing msg.Html'
    print(subject)
    msg = Message(to=recipients,
                  Subject=subject,
                  )
    msg.Html = "This <strong>HTML</strong> body was added after initialization"
    result = msg.send(emailRedirect=None)

    subject = '9. Testing msg.html'
    print(subject)
    msg = Message(to=recipients,
                  Subject=subject,
                  )
    msg.html = "This <strong>HTML</strong> body was added after initialization"
    result = msg.send(emailRedirect=None)



    subject = '10. Testing attachments as filenames'
    print(subject)
    msg = Message(to=recipients,
                  Subject=subject,
                  Body="Note that the current working directory of the Mailer class is settings.BASE_DIR"
                  )
    msg.attach("emailer/test_image1.jpg")
    msg.attach("emailer/test_image2.jpg")
    result = msg.send(emailRedirect=None)

    subject = '11. Testing attachments as file objects'
    print(subject)
    msg = Message(to=recipients,
                  Subject=subject,
                  Body="Note that the current working directory of the Mailer class is settings.BASE_DIR"
                  )
    msg.attach(open("emailer/test_image1.jpg", 'rb'))
    msg.attach(open("emailer/test_image2.jpg", 'rb'))
    result = msg.send(emailRedirect=None)

    subject = '12. Testing comma separated list of emails in To'
    print(subject)
    recipients = ",".join(recipients)
    msg = Message(to=recipients,
                  Subject=subject,
                  Body=f"The recipients were {recipients}"
                  )
    result = msg.send(emailRedirect=None)

subject = '13. Testing space separated list of emails in To'
print(subject)
recipients = " ".join(recipients)
msg = Message(to=recipients,
              Subject=subject,
              Body=f"The recipients were {recipients}"
              )
result = msg.send(emailRedirect=None)



