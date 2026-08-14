import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

urls_to_test = [
    # GeeksforGeeks
    'https://www.geeksforgeeks.org/company-interview-corner/',
    'https://www.geeksforgeeks.org/tcs-interview-experience/',
    'https://www.geeksforgeeks.org/infosys-interview-experience/',
    'https://www.geeksforgeeks.org/accenture-interview-experience/',
    'https://www.geeksforgeeks.org/wipro-interview-experience/',
    'https://www.geeksforgeeks.org/deloitte-interview-experience/',
    'https://www.geeksforgeeks.org/sql-interview-questions/',
    'https://www.geeksforgeeks.org/top-100-data-structures-and-algorithms-dsa-interview-questions/',
    'https://www.geeksforgeeks.org/hr-interview-questions/',

    # IndiaBIX
    'https://www.indiabix.com/aptitude/questions-and-answers/',
    'https://www.indiabix.com/aptitude/numbers/',
    'https://www.indiabix.com/aptitude/time-and-work/',
    'https://www.indiabix.com/logical-reasoning/questions-and-answers/',
    'https://www.indiabix.com/verbal-ability/questions-and-answers/',
    'https://www.indiabix.com/c-programming/questions-and-answers/',
    'https://www.indiabix.com/java-programming/questions-and-answers/',
    'https://www.indiabix.com/database/questions-and-answers/',

    # AmbitionBox
    'https://www.ambitionbox.com/reviews/tcs-reviews',
    'https://www.ambitionbox.com/reviews/infosys-reviews',
    'https://www.ambitionbox.com/reviews/accenture-reviews',
    'https://www.ambitionbox.com/reviews/wipro-reviews'
]

print("Testing URLs...")
for u in urls_to_test:
    try:
        req = urllib.request.Request(u, headers=headers)
        res = urllib.request.urlopen(req, context=ctx, timeout=5)
        print(f"[SUCCESS {res.status}] {u}")
    except Exception as e:
        print(f"[FAILED] {u} -> {e}")
