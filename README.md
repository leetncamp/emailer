# emailer
sendgrid smtp emailer
You'll need these in your settings.py file

SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', default=None)
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = 'apikey'  # this is exactly the value 'apikey'
EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
EMAIL_PORT = 587
EMAIL_USE_TLS = True



and an .evn file with SENDGRID_API_KEY=yourkeyhere in your project root.
and django-enviorn
