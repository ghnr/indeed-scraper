import re
import requests
import time
from bs4 import BeautifulSoup
import pandas as pd


def remove_non_utf8(text_list):
    return [text.encode('utf-8', errors='ignore').decode() for text in text_list]


COLUMNS = ["Title", "Company", "Location", "Salary", "Summary", "Link"]
# Needed for attaching to hrefs later
INDEED_DOMAIN = 'https://www.indeed.com'
# Example URL:
BASE_URL = 'https://www.indeed.com/jobs?q=programmer&l='

df = pd.DataFrame(columns=COLUMNS)

# Stops columns like the link column from wrapping in the table that we print/save
pd.set_option('display.max_colwidth', -1)
pd.set_option('display.width', 1000)

page_start = 0

while True:
    URL = BASE_URL + '&start=' + str(page_start)
    page = requests.get(URL)
    soup = BeautifulSoup(page.text, 'html.parser')
    
    job_cards = soup.find_all('div', class_='jobsearch-SerpJobCard')

    print("Scraping page " + str(int(page_start / 10) + 1))
    
    for card in job_cards:
        title = card.find('a', {'data-tn-element': 'jobTitle'}).text.strip()
        
        # Several try/excepts used because indeed.com is not consistent with their HTML tag naming and placement
        try:
            company = card.find('span', class_='company').text.strip()
        except AttributeError:
            company = '-'
        
        try:
            location = card.find('div', class_='location').text
        except AttributeError:
            location = card.find('span', class_='location').text
        
        try:
            salary = card.find('div', class_='salarySnippet').text.strip()
        except AttributeError:
            salary = '-'
        
        try:
            summary = card.find('span', class_='summary').text.strip()
        except AttributeError:
            summary = card.find('div', class_='summary').text.strip()
        
        # Links converted from local hrefs to full URLs using domain
        link = INDEED_DOMAIN + card.find('a', class_='turnstileLink')['href']
        
        # Append row of values to dataframe
        df.loc[df.shape[0]] = remove_non_utf8([title, company, location, salary, summary, link])
    
    # If "Next" button is not visible, then there are no more pages to scrape
    pagination = soup.find('div', class_='pagination').find('span', class_='np', text=re.compile(r'Next'))
    if not pagination:
        break
    else:
        # e.g. Page 1 is &start=0, Page 2 is &start=10
        page_start += 10
        # Be nice
        time.sleep(0.1)

# Duplicates aren't checked when appending so drop them here by checking the link column values
df.drop_duplicates(subset=["Title", "Company", "Location", "Salary"], inplace=True)
# Sort salary: df.sort_values("Salary", ascending=True, inplace=True)

# Save dataframe to HTML file to view later
with open('indeed_scraped.html', 'w', encoding='utf-8') as file:
    css_file = open('table.css', 'r')
    css = css_file.read()
    css_file.close()
    html = df.to_html()
    html = html.replace('class="dataframe"', 'class="hovertable"')
    # Make links clickable
    html = re.sub(r'<td>(https://.+)</td>', r'<td><a href="\1">LINK</a></td>', html)
    # For pre-HTML5 browsers
    file.write('<meta charset="UTF-8">\n' + css + html)
