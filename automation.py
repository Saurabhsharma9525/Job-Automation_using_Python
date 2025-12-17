import os
import requests
import pandas as pd
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv
import yagmail

# Load environment variables
load_dotenv()

API_KEY = os.getenv("SERPAPI_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

# ------------------------------
# GOOGLE JOB SEARCH FUNCTION
# ------------------------------
def search_google_jobs(query, location_filter):
    url = "https://serpapi.com/search.json"

    params = {
        "engine": "google_jobs",
        "q": query,
        "hl": "en",
        "api_key": API_KEY
    }

    try:
        response = requests.get(url, params=params).json()
    except Exception as e:
        print(f"Request error: {e}")
        return []

    jobs = response.get("jobs_results", [])

    filtered_jobs = []

    for job in jobs:
        title = job.get("title", "")
        company = job.get("company_name", "")
        location = job.get("location", "")
        link = job.get("apply_link", "")

        # filtering
        if (
            location_filter.lower() in location.lower()
            or location_filter.lower() == "all"
        ):
            filtered_jobs.append({
                "Title": title,
                "Company": company,
                "Location": location,
                "Apply Link": link
            })

    return filtered_jobs


# ------------------------------
# MAIN JOB SEARCH FUNCTION
# ------------------------------
def run_job_search():
    print("Running Job Search...")

    queries = [
        ("entry level data analyst jobs", "ALL"), 
        ("startup data analyst jobs", "ALL"),
        ("data analyst jobs remote", "Remote"),
        ("data analyst jobs india", "India")
    ]

    all_results = []

    for query, fltr in queries:
        results = search_google_jobs(query, fltr)
        all_results.extend(results)

    # If empty then avoid crash
    if not all_results:
        print("No jobs found today.")
        return

    save_to_csv(all_results)
    send_html_email(all_results)

    print("✔ Job search completed successfully!")


# ------------------------------
# SAVE RESULTS TO CSV
# ------------------------------
def save_to_csv(jobs):
    df = pd.DataFrame(jobs)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"jobs_{timestamp}.csv"
    df.to_csv(filename, index=False)
    print(f"CSV saved: {filename}")


# ------------------------------
# SEND EMAIL (HTML FORMAT)
# ------------------------------
def send_html_email(jobs):
    try:
        yag = yagmail.SMTP(SENDER_EMAIL, SENDER_PASSWORD)
    except Exception as e:
        print("SMTP Login Failed:", e)
        return

    html = """
    <h2>🔥 Daily Data Analytics Job Alerts</h2>
    <p>Here are today's job updates:</p>
    <hr>
    """

    for job in jobs:
        html += f"""
        <p>
        <b>Job Title:</b> {job['Title']}<br>
        <b>Company:</b> {job['Company']}<br>
        <b>Location:</b> {job['Location']}<br>
        <a href="{job['Apply Link']}">Apply Here</a>
        </p>
        <hr>
        """

    try:
        yag.send(
            to=RECEIVER_EMAIL,
            subject="📌 Daily Data Analyst Job Updates",
            contents=html
        )
        print("✔ Email sent successfully!")
    except Exception as e:
        print("Email sending error:", e)


# ------------------------------
# SCHEDULER (SET DAILY TIME)
# ------------------------------
schedule.every().day.at("14:32").do(run_job_search)

print("Automation Started. Waiting for next run...")

while True:
    schedule.run_pending()
    time.sleep(10)
