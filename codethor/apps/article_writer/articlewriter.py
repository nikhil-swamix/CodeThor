import uaiclient
import os
import json
import time
import re
from typing import Dict, Pattern


def make_index(abs_dirpath):
    files = [name for name in os.listdir(abs_dirpath) if name.endswith('.md')]
    json.dump(files, open(f"{abs_dirpath}/index.json", "w"))
    print("Index created successfully: Total files: ", len(files))


def substitute_vars(text: str, replace_dict: Dict[str, str]) -> str:
    def replace_func(match: re.Match) -> str:
        return replace_dict[match.group(0)]

    pattern: Pattern = re.compile("|".join(map(re.escape, replace_dict.keys())))
    return pattern.sub(replace_func, text)


db = {
    "titles": [
        "Top 10 Waterproofing Solutions in {location} by {businessname}",
        "Why {businessname} is {location}'s Go-To for Terrace Waterproofing",
        "Protect Your Home: Expert Waterproofing Services in {location}",
        "5 Reasons to Choose {businessname} for Roof Waterproofing in {location}",
        "Monsoon-Proof Your Home with {businessname}'s Exterior Waterproofing",
        "The Ultimate Guide to Basement Waterproofing in {location}",
        "Leak-Free Living: {businessname}'s Watertank Waterproofing Solutions",
        "Transform Your Wet Areas with {businessname}'s Waterproofing Expertise",
        "{location}'s Trusted Name in Waterproofing: {businessname}",
        "Eco-Friendly Waterproofing Options from {businessname} in {location}",
        "Say Goodbye to Water Damage: {businessname}'s Comprehensive Solutions",
        "Increase Your Property Value with {businessname}'s Waterproofing Services",
        "The Science Behind {businessname}'s Effective Waterproofing Techniques",
        "From Terrace to Basement: Complete Waterproofing by {businessname}",
        "Why {location} Homeowners Trust {businessname} for Waterproofing",
        "Innovative Waterproofing Solutions for {location}'s Unique Climate",
        "Extend Your Roof's Lifespan with {businessname}'s Waterproofing",
        "Mold-Free Homes: The {businessname} Waterproofing Advantage",
        "Emergency Waterproofing Services in {location} by {businessname}",
        "{businessname}: Bringing Cutting-Edge Waterproofing to {location}",
        "Affordable and Reliable: {businessname}'s Waterproofing Services",
        "The {businessname} Difference: Superior Waterproofing in {location}",
        "Protect Your Investment: Commercial Waterproofing by {businessname}",
        "Residential Waterproofing Experts in {location}: {businessname}",
        "Energy-Efficient Homes Start with {businessname}'s Waterproofing",
        "{location}'s Weather is No Match for {businessname}'s Waterproofing",
        "The Complete Waterproofing Checklist for {location} Homes",
        "Why DIY Waterproofing Fails: Trust {businessname} in {location}",
        "Seasonal Waterproofing Tips from {location}'s Experts: {businessname}",
        "{businessname}: Pioneering Waterproofing Techniques in {location}",
        "Leak Detection and Waterproofing Services by {businessname}",
        "Future-Proof Your Home with {businessname}'s Waterproofing Solutions",
        "The Hidden Dangers of Poor Waterproofing: {businessname}'s Insights",
        "{location}'s Best-Kept Secret for Home Protection: {businessname}",
        "Waterproofing Made Easy: {businessname}'s Hassle-Free Process",
        "From Foundations to Roofs: Comprehensive Waterproofing by {businessname}",
        "Why {location} Architects Recommend {businessname} for Waterproofing",
        "Waterproofing for Old Homes: {businessname}'s Specialized Approach",
        "Green Waterproofing Solutions: {businessname}'s Commitment to {location}",
        "{businessname}: Bringing Peace of Mind to {location} Homeowners",
        "The Long-Term Benefits of Professional Waterproofing by {businessname}",
        "Waterproofing on a Budget: {businessname}'s Cost-Effective Solutions",
        "{location}'s Waterproofing Experts Reveal Top Home Protection Tips",
        "Beyond Leaks: The Many Benefits of {businessname}'s Waterproofing",
        "Smart Home Waterproofing: {businessname}'s Innovative Approaches",
        "{businessname}: Setting the Gold Standard for Waterproofing in {location}",
        "Waterproofing for All Seasons: {businessname}'s Year-Round Protection",
        "The {businessname} Promise: Dry Homes for {location} Residents",
        "Customized Waterproofing Solutions by {businessname} for {location} Homes",
        "{location}'s Waterproofing Revolution Led by {businessname}",
    ]
}

ProjectDir = r"D:\GitHub\FREELANCE\Client-Pranav\vamanawaterproofingsolutions.com"
BlogsDirOfMDFiles = os.path.join(ProjectDir, "static", "blogs")
client = uaiclient.Client("openai|gpt-4o-mini")
VARS = {"{location}": "Hyderabad", "{businessname}": "Vamana Waterproofing"}
SYSTEM = """vamanawaterproofingsolutions.com\n
Vamana Waterproofing Solutions for Your Water Leakage? Protect your home from water damage with our high-quality waterproofing products and services. WhatsApp 9642518564 Facebook Terrace Waterproofing Protect your roof from water damage and extend its lifespan with our professional waterproofing services. Prevent leaks and water intrusion Improve energy efficiency Extend the life of your roof Watch Video Roof Waterproofing Exterior Waterproofing Protect your exteriors from monsoon damage with our high-performance waterproofing solutions. Prevent leaks and moisture buildup Improve indoor air quality Increase the value of your home Watch Video Basement Waterproofing Watertank Waterproofing Ensure your watertank remains leak-proof and durable with our advanced waterproofing solutions. Ultimate Leak Protection Long-Lasting Durability Eco-Friendly Options No Hazardous chemicals Watch Video Watertank Waterproofing Wet Areas Waterproofing Keep your kitchen and bathrooms dry and safe with our easy waterproofing solutions. Stops leaks Prevents mold Easy to apply Safe for families Watch Video Wet Areas Waterproofing Find our offices at the address below on the map. Drop by to learn more about our waterproofing solutions.
"""


for title in db['titles']:
    title = substitute_vars(title, VARS)
    filename = f"{BlogsDirOfMDFiles}/{re.sub(r'[^A-Za-z0-9-]', '', title.replace(' ', '-'))}.md"

    if os.path.exists(filename):
        print(f"Skipping existing file: {filename.split('/')[-1]}")
        continue

    body = client.chat(
        [
            {
                "user": f"title of the article is {title} \nbased on the context, generate a 500 word article seo friendly,  with appropriate marketing style and structure. include a Call to action (subtle) once in between and in end, the phone number and website. the content should be oriented around service and benefits, be more substantial towards title. only output a pure markdown, nothing else, not even backticks."
            }
        ],
        system=SYSTEM,
    )

    with open(filename, "w") as f:
        f.write(body)
    print(f"Created file: {filename}")

make_index(BlogsDirOfMDFiles)
    # print(body)
