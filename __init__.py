import base64
import re
import traceback
from pdb import set_trace as debug
import os
import markdown2
from django.conf import settings
from django.utils.text import slugify
from markdownify import markdownify
from sendgrid import SendGridAPIClient, Disposition, FileName, FileType, FileContent, ContentId
from sendgrid.helpers.mail import From, To, Subject, PlainTextContent, HtmlContent, Mail, Attachment
import logging
log = logging.getLogger(__name__)

try:
    basestring
except NameError:
    basestring = str

emailRedirect = settings.EMAIL_REDIRECT


class Message:
    """The old messages class used upper case field names. To be drop in compatible, I'm supporting that here. Omit
    'From' and it will be a do-not-reply@domain rather than the default django setting found in settings.py """

    """f(subject, text_content, from_email, [to]) followed by msg.attach_alternative(html_content, "text/html")"""

    """And the parent class:
        EmailMessage Objects

        class EmailMessage[source]
        The EmailMessage class is initialized with the following parameters (in the given order, if positional arguments are used). All parameters are optional and can be set at any time prior to calling the send() method.

        subject: The subject line of the email.
        body: The body text. This should be a plain text message.
        from_email: The sender’s address. Both fred@example.com and "Fred" <fred@example.com> forms are legal. If omitted, the EMAIL_DEFAULT_FROM setting is used.
        to: A list or tuple of recipient addresses.
        bcc: A list or tuple of addresses used in the “Bcc” header when sending the email.
        connection: An email backend instance. Use this parameter if you want to use the same connection for multiple messages. If omitted, a new connection is created when send() is called.
        attachments: A list of attachments to put on the message. These can be either MIMEBase instances, or (filename, content, mimetype) triples.
        headers: A dictionary of extra headers to put on the message. The keys are the header name, values are the header values. It’s up to the caller to ensure header names and values are in the correct format for an email message. The corresponding attribute is extra_headers.
        cc: A list or tuple of recipient addresses used in the “Cc” header when sending the email.
        reply_to: A list or tuple of recipient addresses used in the “Reply-To” header when sending the email.

        All parameters are optional and can be set at any time prior to calling the send() method.
    """

    default_headers = {
        'X-Mail-Generator': 'Eventhosts-Email-Template',
        "Auto-Submitted": "auto-generated",
    }

    def __init__(self, *args, **kwargs):
        """Initialize all variables"""
        self.To = ""
        self.From = ""
        self.Subject = ""
        self.Body = ""
        self.Html = ""
        self.html = ""
        self.body = ""
        self.from_email = ""
        self.subject = ""
        self.to = ""
        self.attachments = []
        if not settings.SENDGRID_API_KEY:
            raise Exception("SENDGRID_API_KEY not defined in .env when sending a Message()")
        self.sendgrid_client = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)


        To = kwargs.pop("To", None)
        if To:
            to = To
        From = kwargs.pop("From", None)
        if From:
            from_email = From
        Subject = kwargs.pop("Subject", None)
        if Subject:
            subject = Subject
        Html = kwargs.pop("Html", kwargs.pop("html", None))

        Body = kwargs.pop("Body", None)
        if Body:
            body = Body
        Replyto = kwargs.pop("Replyto", None)
        init_headers = kwargs.pop("headers", {})
        init_headers.update(self.default_headers)
        self.__dict__.update(locals())

        super().__init__()

    def __str__(self):
        return "{0} : {1}".format(str(self.to), self.subject)

    def set_delete_header(self):
        """Insert a header into this email that will cause it to be deleted by the procmail rule:
        :0
        * ^X-neurips-delete
        /dev/null
        """
        self.extra_headers.update({'X-NeurIPS-delete': ""})

    def attach(self, filepath_or_object):
        self.attachments.append(filepath_or_object)

    def attach_file(self, filepath_or_object):
        self.attach(filepath_or_object)


    def send(self, **kwargs):

        """First, try to be compatible with the old To, From, and Html attributes.  Then consider are we redirecting
        email? """

        if not settings.EMAIL_DEFAULT_FROM:  # The raise below would happen if EMAIL_DEFAULT_FROM were defined as None or ""
            raise Exception("Define settings.EMAIL_DEFAULT_FROM")

        if hasattr(self.To, "__iter__") and not isinstance(self.To, basestring):
            # if the To field is a list, convert it into a comma separated list of email addresses as a string.
            self.To = ",".join(self.To)

        if hasattr(self, "To") and (not hasattr(self, "to") or self.to == []):
            self.to = self.To

        if hasattr(self.to, "__iter__") and not isinstance(self.to, basestring):
            # if the To field is a list, convert it into a comma separated list of email addresses as a string.
            self.to = ",".join(self.to)

        if hasattr(self, "From") and self.from_email == settings.EMAIL_DEFAULT_FROM:
            """When we call super in __init__, if no from_email is available, the default gets filled in at init time.
            Test for that default"""

            self.from_email = self.From

        if hasattr(self, "Subject") and self.subject == "":
            self.subject = self.Subject

        if hasattr(self, "Body") and self.body == "":
            self.body = self.Body

        if hasattr(self, 'Html') and not hasattr(self, "html"):
            self.html = self.Html

        if hasattr(self, "html") and (self.html != "" and self.html is not None):

            if self.body == "":
                # html and no body
                self.body = markdownify(self.html)
            self.attach_alternative(self.html, "text/html")

        if self.body and ((hasattr(self, "Html") and (self.Html == "" or self.Html is None)) or not hasattr(self, "Html")):
            # Body and no Html
            self.Html = markdown2.markdown(self.body)
            # self.attach_alternative(self.html, "text/html")  # TODO attache the alternative some other way

        if hasattr(self.from_email, "__getitem__") and not isinstance(self.from_email, str):
            # The 'from' is iterable. We can't have that. It's possible a queryset passed
            # in from getting sponsor handlers. We must pick just one or if the query is empty, then
            if len(self.from_email) == 0:
                self.from_email = ""  # This will get replaced with a do-not-reply below
            else:
                self.from_email = self.from_email[0]

        if self.from_email is None or self.from_email == "":
            """Looks like no From was specified. Try to guess the domain. We are too early on the model page get a 
            conference object at this point so guess. Maybe this can be moved to just below Conferences. """

            self.from_email = settings.EMAIL_DEFAULT_FROM

        if not hasattr(self.to, '__iter__'):
            # This could be a single email or a comma separated list of emails.
            self.to = self.to.split(
                ",")  # This will make a list out of a string without commas, e.g. 'support@neurips.cc'.split(","") returns ['support@neurips.cc']

        if not self.Html:
            self.Html = "&nbsp;"
        if not self.Body:
            self.Body = " "

        if emailRedirect:
            email_to = self.__dict__.get("To", self.__dict__.get("to"))
            if email_to and not isinstance(self.to, basestring):
                redirectStr = "Redirected from {0}:: ".format(", ".join(email_to))
            elif isinstance(self.subject, basestring):
                redirectStr = "Redirected from {0}:: ".format(email_to)

            subRE = re.compile(r"^Redirected\ from.*::")
            if self.subject is None:
                self.subject = ""
            subject = redirectStr + subRE.sub("", self.subject)
            self.subject = subject
            self.to = emailRedirect

        debug()
        message = Mail(
            from_email=self.from_email,
            to_emails=self.to,
            subject=self.subject,
            plain_text_content=self.Body,
            html_content=self.Html,
        )
        if hasattr(self, "Replyto") and self.Replyto and isinstance(self.Replyto, basestring):
            message.reply_to = self.Replyto


        # message.set_headers({'X-Priority': '2'})
        for file in self.attachments:
            # file is either a string or a file object
            if isinstance(file, str):
                data = open(file, 'rb').read()
            elif hasattr(file, "seek"):
                file.seek(0)
                data = file.read()

            encoded = base64.b64encode(data).decode()
            attachment = Attachment()
            attachment.file_content = FileContent(encoded)
            extension = os.path.splitext(file)[-1].strip(".")
            attachment.file_type = FileType(f'application/{extension}')
            attachment.file_name = FileName(os.path.basename(file))
            attachment.disposition = Disposition('attachment')
            attachment.content_id = ContentId(slugify(attachment.file_name))
            message.add_attachment(attachment)

        try:
            response = self.sendgrid_client.send(message=message)
            # TODO log or store a record of sending this message
            if response._status_code >= 300:
                log.critial(f"SENDGRID-SEND-FAILURE: {response.subject}")
            return {'code': response._status_code}
        except Exception as e:
            tb = traceback.format_exc()
            error_message = f"{tb}\n\n{e.body}: "
            log.exception(error_message)
            return {"code": 1000, "error": tb}


    def snlSend(self):
        """Backward compatibility with an old emailer"""
        return self.send()

