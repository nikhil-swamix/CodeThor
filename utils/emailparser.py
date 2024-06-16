import sys

sys.path.append("../")
import uaiclient

from fast_mail_parser import parse_email, ParseError

with open(r'C:\Users\User\Downloads\🤖 Microsoft Retires Copilot GPT Builder.eml', 'r') as f:
    message_payload = f.read()

try:
    email = parse_email(message_payload)
except ParseError as e:
    print("Failed to parse email: ", e)
    sys.exit(1)


etext = "".join(email.text_plain)
# print(etext)
resp = uaiclient.Client("deepinfra", "microsoft/WizardLM-2-8x22B").chat(
    [{"user": f"Email:\n{etext}"}, {"user": f"i have given the above email as input"}],
    system="""
    - summarize the email given by user  for a linkedin post
    - output should be at high profile influencer level
    - output should be atleast 200 words 
    - keep any emojis and prepend points with hand arrow
    - IMPORTANT:remove any advertising by AI fire and other unwanted text. write as general information with facts and figures
    """,
)
# print(email.subject)
# print(email.date)
print(resp)
# print(email.text_html)
# print(email.headers)

# for attachment in email.attachments:
#     print(attachment.mimetype)
#     # print(attachment.content)
#     # print(attachment.filename)
