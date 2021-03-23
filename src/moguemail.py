#!/usr/bin/env python
# coding: utf-8

import smtplib, os

from email import Encoders

from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText

class MoguraEmail:
	mail_server = '127.0.0.1'
	sender_email = 'no@reply'
	replyto_email = 'no@reply'
	mail_from_email = 'no@reply'

        attachment_size_limit = 20 * 1024 * 1024

	message_template = """
<html>
<style type="text/css">
body {
        background-color: white;
        font: 11pt sans-serif;
}
table {
        border-width: 1px 1px 1px 1px;
        border-spacing: 2px;
        border-style: outset outset outset outset;
        border-color: gray gray gray gray;
        border-collapse: collapse;
        background-color: white;
        font: 10pt sans-serif;
}
table tr.header td{
        border-width: 1px 1px 1px 1px;
        padding: 2px 2px 2px 2px;
        border-style: inset inset inset inset;
        border-color: gray gray gray gray;
        background-color: #8FF2E0;
	font-weight: bold;
        -moz-border-radius: 0px 0px 0px 0px;
}
table tr.footer td{
	text-align: center;
	font-color: red;
	font-weight: bold;
}
table td {
        border-width: 1px 1px 1px 1px;
        padding: 2px 5px 2px 5px;
        border-style: inset inset inset inset;
        border-color: gray gray gray gray;
        -moz-border-radius: 0px 0px 0px 0px;
}
table tr.odd_row td {
        background-color: white;
}
table tr.even_row td {
        background-color: #E3E6E5;
}
</style>

<body>
%(message)s
<br/><br/>
</body>
</html>
"""

        message_attachment_too_big = u"""
<br/><br/>
<p>xlsx-файл слишком большой и не может быть передан во вложении к письму.</p>
"""

	def send(self, title, message, recipients, attachment = None, attachment_title = None, service_info = None):
		try:
			msg = MIMEMultipart()
			msg['From'] = self.sender_email 
			msg['To'] = recipients 
			msg['Subject'] = title
			msg['Reply-To'] = self.replyto_email 
			
			if service_info != None:
				msg['X-Mogura-Service-Info'] = service_info

                        if attachment != None and os.path.getsize(attachment) > self.attachment_size_limit:
                                message += self.message_attachment_too_big

			if message != None:
				msg.attach(MIMEText(self.message_template % {'message': message}, 'html', 'utf-8'))

			if attachment != None and os.path.getsize(attachment) <= self.attachment_size_limit:
				csv = MIMEBase('application', 'octet-stream')
				csv.set_payload(open(attachment).read())
				Encoders.encode_base64(csv)
				csv.add_header('Content-Disposition', 'attachment', filename=attachment_title)
				msg.attach(csv)

			s = smtplib.SMTP(self.mail_server)
			s.sendmail(self.mail_from_email, recipients.split(','), msg.as_string())
		except:
			return 1
