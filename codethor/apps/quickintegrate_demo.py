from uaiclient import Client
import json

task = f"""
API1 response
{{
    "mail" : "a@b.com",
    "body" : "long text",
    "sub" : "hello atdevs"
}}

API2 input
{{
    "subject" : "",
    "email":"",
    "body":"",
}}
"""

for c in [Client("ollama|codeqwen:latest")]:
    resp = c.chat(
        messages=[{"user": task}],
        temperature=0,
        system=f"give a key to key mapping only json output, for api1 to 2 mapping. keys should be keys of api1, values should be keys of api2 , no explanations only valid json output.{{k1:k2}}",
    )
    apimapping = json.loads(resp)
    print(apimapping)

"""
please give only a json output for key value format to map these inputs from api1 to api 2, no headings or explanation only json, key 1 should be value of 2, no backticks ,only kv pairs
"""
