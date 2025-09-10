#!/usr/bin/env python3
"""
ENHANCED MULTI-ACCOUNT JOBRIGHT SCRAPER
Simultaneously uses up to 80 JobRight accounts for maximum job diversity
"""

import requests
import json
import time
import random
import gspread
import threading
import concurrent.futures
from google.oauth2.service_account import Credentials
from datetime import datetime
from typing import List, Dict, Any
import queue
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiAccountJobRightScraper:
    def __init__(self, config_file='accounts_config.json'):
        self.config_file = config_file
        self.accounts = []
        self.active_sessions = {}
        self.job_queue = queue.Queue()
        self.results_queue = queue.Queue()
        self.load_accounts_config()

        # Google Sheets credentials
        self.google_credentials = None
        self.setup_google_credentials()

        # Deduplication
        self.processed_job_ids = set()
        self.lock = threading.Lock()

    def load_accounts_config(self):
        """Load accounts configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.accounts = [acc for acc in config['accounts'] if acc.get('active', True)]
            logger.info(f"✅ Loaded {len(self.accounts)} active accounts")
        except FileNotFoundError:
            logger.error(f"❌ Configuration file {self.config_file} not found")
            self.generate_default_config()
            self.load_accounts_config()
        except Exception as e:
            logger.error(f"❌ Error loading config: {e}")
            raise

    def generate_default_config(self):
        """Generate default configuration if file doesn't exist"""
        logger.info("🔧 Generating default configuration...")
        config = {"accounts": []}

        job_titles = ["Software Engineer", "Data Scientist", "Product Manager", "DevOps Engineer"]

        for i in range(1, 81):
            account = {
                "email": f"{i}@a.com",
                "password": "ajay4498",
                "name": f"Account_{i}",
                "job_title": job_titles[(i-1) % len(job_titles)],
                "active": True,
                "max_daily_requests": 100
            }
            config["accounts"].append(account)

        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"✅ Generated default config with 80 accounts")

    def setup_google_credentials(self):
        """Setup Google Sheets credentials"""
        try:
            import os
            credentials_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            if credentials_json:
                scope = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]
                credentials_info = json.loads(credentials_json)
                self.google_credentials = Credentials.from_service_account_info(
                    credentials_info, scopes=scope
                )
                logger.info("✅ Google Sheets credentials loaded")
            else:
                logger.warning("⚠️ No Google credentials found")
        except Exception as e:
            logger.error(f"❌ Error setting up Google credentials: {e}")

    def create_session(self, account):
        """Create authenticated session for an account"""
        session = requests.Session()

        # Critical headers for JobRight authentication
        session.headers.update({
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'X-Client-Type': 'mobile_web',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1',
            'Referer': 'https://jobright.ai/',
            'Origin': 'https://jobright.ai',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br'
        })

        try:
            # Login with account credentials
            login_data = {
                "email": account['email'],
                "password": account['password']
            }

            response = session.post(
                "https://jobright.ai/swan/auth/login/pwd",
                json=login_data,
                timeout=15
            )

            if response.status_code == 200 and response.json().get('success'):
                user_data = response.json().get('result', {})
                account['user_id'] = user_data.get('userId')
                account['session'] = session

                # Complete onboarding workflow
                self.complete_account_workflow(session, account)

                logger.info(f"✅ {account['name']} ({account['email']}) authenticated")
                return session
            else:
                logger.error(f"❌ {account['name']} login failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ {account['name']} session error: {e}")
            return None

    def complete_account_workflow(self, session, account):
        """Complete necessary workflow for job access"""
        try:
            # Get user info
            session.get("https://jobright.ai/swan/auth/newinfo", timeout=10)
            time.sleep(0.5)

            # Get user settings  
            session.get("https://jobright.ai/swan/user-settings/get", timeout=10)
            time.sleep(0.5)

            # Get A/B config if user_id available
            if account.get('user_id'):
                session.get(f"https://jobright.ai/swan/ab/user?user={account['user_id']}", timeout=10)

            logger.debug(f"✅ {account['name']} workflow completed")

        except Exception as e:
            logger.debug(f"⚠️ {account['name']} workflow error: {e}")

    def scrape_jobs_from_account(self, account, target_jobs_per_account=25):
        """Scrape jobs from a single account"""
        if 'session' not in account:
            logger.error(f"❌ {account['name']}: No active session")
            return []

        session = account['session']
        jobs = []

        try:
            logger.info(f"🔍 {account['name']}: Starting job scraping (target: {target_jobs_per_account})")

            # Method 1: Try pagination approach
            jobs.extend(self.scrape_with_pagination(session, account, target_jobs_per_account))

            # Method 2: Try job title filtering if configured
            if len(jobs) < target_jobs_per_account and account.get('job_title'):
                additional_jobs = self.scrape_with_job_title_filter(
                    session, account, target_jobs_per_account - len(jobs)
                )
                jobs.extend(additional_jobs)

            # Method 3: Try API endpoint as fallback
            if len(jobs) < target_jobs_per_account * 0.5:
                api_jobs = self.scrape_with_api(session, account, target_jobs_per_account)
                jobs.extend(api_jobs)

            # Add account info to jobs
            for job in jobs:
                job['scraper_account'] = account['name']
                job['scraper_email'] = account['email']
                job['job_title_preference'] = account.get('job_title', 'General')

            logger.info(f"✅ {account['name']}: Scraped {len(jobs)} jobs")
            return jobs

        except Exception as e:
            logger.error(f"❌ {account['name']} scraping error: {e}")
            return []

    def scrape_with_pagination(self, session, account, target_jobs):
        """Scrape using pagination approach"""
        jobs = []
        max_pages = min((target_jobs // 20) + 1, 3)  # Max 3 pages per account

        for page in range(max_pages):
            try:
                position = page * 20
                params = {"position": position} if position > 0 else {}

                response = session.get(
                    "https://jobright.ai/swan/recommend/landing/jobs",
                    params=params,
                    timeout=15
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') and data.get('result', {}).get('jobList'):
                        job_list = data['result']['jobList']
                        page_jobs = self.process_job_list(job_list, page + 1)
                        jobs.extend(page_jobs)

                        if len(jobs) >= target_jobs:
                            break
                    else:
                        break
                else:
                    break

                time.sleep(1)  # Rate limiting

            except Exception as e:
                logger.debug(f"⚠️ {account['name']} pagination error on page {page}: {e}")
                break

        return jobs

    def scrape_with_job_title_filter(self, session, account, target_jobs):
        """Scrape using job title filtering"""
        jobs = []
        job_title = account.get('job_title', 'Software Engineer')

        try:
            # Update job title filter
            filter_payload = {
                "filters": {
                    "jobTitle": job_title,
                    "jobTaxonomyList": [{"title": job_title, "taxonomyId": "00-00-00"}],
                    "jobTypes": [1],  # Full-time
                    "workModel": [1, 2, 3],  # All work models
                    "locations": [{"city": "Within US", "radiusRange": 25}],
                    "seniority": [5, 6]  # Mid/senior levels
                }
            }

            update_response = session.post(
                "https://jobright.ai/swan/filter/update/filter-v2",
                json=filter_payload,
                timeout=15
            )

            if update_response.status_code == 200 and update_response.json().get('success'):
                time.sleep(2)  # Allow backend processing

                # Fetch filtered jobs
                response = session.get(
                    "https://jobright.ai/swan/recommend/list/jobs?refresh=true&sortCondition=1",
                    timeout=15
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') and data.get('result', {}).get('jobList'):
                        job_list = data['result']['jobList'][:target_jobs]
                        jobs = self.process_job_list(job_list, 1, job_title)

            logger.debug(f"🎯 {account['name']}: {len(jobs)} jobs with title filter '{job_title}'")

        except Exception as e:
            logger.debug(f"⚠️ {account['name']} title filter error: {e}")

        return jobs

    def scrape_with_api(self, session, account, target_jobs):
        """Scrape using API endpoint"""
        jobs = []

        try:
            response = session.get(
                "https://jobright.ai/swan/recommend/list/jobs?refresh=true&sortCondition=0&position=0",
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('result', {}).get('jobList'):
                    job_list = data['result']['jobList'][:target_jobs]
                    jobs = self.process_job_list(job_list, 1)

            logger.debug(f"🔗 {account['name']}: {len(jobs)} jobs from API")

        except Exception as e:
            logger.debug(f"⚠️ {account['name']} API error: {e}")

        return jobs

    def process_job_list(self, job_list, page_num, search_context="General"):
        """Process job list with safe data handling"""
        processed_jobs = []

        for i, job_item in enumerate(job_list):
            try:
                job_result = job_item.get('jobResult', {})
                company_result = job_item.get('companyResult', {})

                def safe_extract(field_value, default=''):
                    if isinstance(field_value, list):
                        return ' | '.join(str(item) for item in field_value) if field_value else default
                    elif field_value is None:
                        return default
                    else:
                        return str(field_value)

                job_id = safe_extract(job_result.get('jobId'))

                # Thread-safe deduplication
                with self.lock:
                    if job_id and job_id in self.processed_job_ids:
                        continue
                    if job_id:
                        self.processed_job_ids.add(job_id)

                job = {
                    'job_title': safe_extract(job_result.get('jobTitle')),
                    'company': safe_extract(company_result.get('companyName', 'Company Not Listed')),
                    'location': safe_extract(job_result.get('jobLocation')),
                    'work_model': safe_extract(job_result.get('workModel')),
                    'salary': safe_extract(job_result.get('salaryDesc')),
                    'seniority': safe_extract(job_result.get('jobSeniority')),
                    'employment_type': safe_extract(job_result.get('employmentType')),
                    'is_remote': str(job_result.get('isRemote', False)),
                    'job_summary': safe_extract(job_result.get('jobSummary')),
                    'core_responsibilities': safe_extract(job_result.get('coreResponsibilities')),
                    'min_experience': safe_extract(job_result.get('minYearsOfExperience')),
                    'apply_link': safe_extract(job_result.get('applyLink')),
                    'job_id': job_id,
                    'publish_desc': safe_extract(job_result.get('publishTimeDesc')),
                    'page_number': page_num,
                    'position_in_page': i + 1,
                    'company_size': safe_extract(company_result.get('companySize')),
                    'source': f'JobRight.ai - {search_context}',
                    'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                if job['job_title']:  # Only add jobs with valid titles
                    processed_jobs.append(job)

            except Exception as e:
                logger.debug(f"⚠️ Error processing job {i}: {e}")
                continue

        return processed_jobs

    def run_multi_account_scraper(self, target_total_jobs=2000, max_concurrent_accounts=20, keyword=""):
        """Run scraper with multiple accounts simultaneously"""
        logger.info(f"🚀 MULTI-ACCOUNT JOBRIGHT SCRAPER STARTING")
        logger.info(f"🎯 Target: {target_total_jobs} jobs using up to {max_concurrent_accounts} concurrent accounts")
        logger.info(f"📧 Available accounts: {len(self.accounts)}")
        logger.info(f"🔍 Keyword filter: '{keyword}'" if keyword else "🔍 No keyword filter")
        logger.info("=" * 80)

        # Limit concurrent accounts to available accounts
        max_concurrent_accounts = min(max_concurrent_accounts, len(self.accounts))
        target_jobs_per_account = max(target_total_jobs // max_concurrent_accounts, 25)

        all_jobs = []
        successful_accounts = 0
        failed_accounts = 0

        # Create sessions for selected accounts
        logger.info(f"🔐 Creating sessions for {max_concurrent_accounts} accounts...")
        active_accounts = []

        for i, account in enumerate(self.accounts[:max_concurrent_accounts]):
            session = self.create_session(account)
            if session:
                active_accounts.append(account)
                successful_accounts += 1
            else:
                failed_accounts += 1

            # Add delay between session creations to avoid rate limiting
            if i < max_concurrent_accounts - 1:
                time.sleep(2)

        logger.info(f"✅ Active sessions: {successful_accounts}, Failed: {failed_accounts}")

        if not active_accounts:
            logger.error("❌ No active accounts available")
            return {"success": False, "message": "No accounts could be authenticated"}

        # Scrape jobs using multiple accounts simultaneously
        logger.info(f"🔍 Starting concurrent scraping with {len(active_accounts)} accounts...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(active_accounts)) as executor:
            future_to_account = {
                executor.submit(self.scrape_jobs_from_account, account, target_jobs_per_account): account 
                for account in active_accounts
            }

            for future in concurrent.futures.as_completed(future_to_account):
                account = future_to_account[future]
                try:
                    jobs = future.result()
                    all_jobs.extend(jobs)
                    logger.info(f"✅ {account['name']}: Added {len(jobs)} jobs (Total: {len(all_jobs)})")
                except Exception as e:
                    logger.error(f"❌ {account['name']}: Scraping failed - {e}")

        logger.info(f"🎉 SCRAPING COMPLETE: {len(all_jobs)} total jobs from {len(active_accounts)} accounts")

        # Filter jobs by keyword if provided
        filtered_jobs = self.filter_jobs_by_keyword(all_jobs, keyword) if keyword else all_jobs

        return {
            "success": True,
            "total_jobs": len(all_jobs),
            "filtered_jobs": len(filtered_jobs),
            "accounts_used": len(active_accounts),
            "accounts_failed": failed_accounts,
            "jobs": filtered_jobs,
            "keyword": keyword
        }

    def filter_jobs_by_keyword(self, all_jobs, keyword=""):
        """Filter jobs by keyword with safe string handling"""
        if not keyword:
            return all_jobs

        logger.info(f"🎯 Filtering {len(all_jobs)} jobs for keyword: '{keyword}'")

        keyword_lower = keyword.lower()
        filtered_jobs = []

        for job in all_jobs:
            title = str(job.get('job_title', '')).lower()
            summary = str(job.get('job_summary', '')).lower()
            responsibilities = str(job.get('core_responsibilities', '')).lower()

            if (keyword_lower in title or 
                keyword_lower in summary or 
                keyword_lower in responsibilities):
                job['keyword_match'] = f'Matches "{keyword}"'
                filtered_jobs.append(job)
            else:
                job['keyword_match'] = 'No match'

        logger.info(f"✅ Found {len(filtered_jobs)} jobs matching '{keyword}'")
        return filtered_jobs

    def export_to_google_sheets(self, jobs, sheet_url, sheet_type="ALL_JOBS"):
        """Export jobs to Google Sheets with account information"""
        if not jobs or not self.google_credentials:
            logger.error("❌ No jobs to export or missing credentials")
            return False

        try:
            logger.info(f"📊 Exporting {len(jobs)} jobs to Google Sheets ({sheet_type})")

            # Extract sheet ID
            if '/spreadsheets/d/' in sheet_url:
                sheet_id = sheet_url.split('/spreadsheets/d/')[1].split('/')[0]
            else:
                sheet_id = sheet_url

            # Setup Google Sheets client
            gc = gspread.authorize(self.google_credentials)
            spreadsheet = gc.open_by_key(sheet_id)

            # Create or get worksheet
            timestamp = datetime.now().strftime('%m%d_%H%M%S')
            worksheet_name = f"MultiAccount_{sheet_type}_{timestamp}"

            try:
                worksheet = spreadsheet.worksheet(sheet_type)
                # Clear existing content and rename
                worksheet.clear()
                worksheet.update_title(worksheet_name)
            except:
                # Create new worksheet
                worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=len(jobs) + 50, cols=25)

            # Enhanced headers with multi-account information
            headers = [
                'Job Title', 'Company', 'Location', 'Work Model', 'Remote', 'Salary',
                'Seniority', 'Employment Type', 'Job Summary', 'Core Responsibilities',
                'Min Experience', 'Apply Link', 'Job ID', 'Published Time', 'Page #', 
                'Position', 'Company Size', 'Keyword Match', 'Source', 'Scraped At',
                'Account Name', 'Account Email', 'Job Title Preference'
            ]

            # Prepare data
            data = [headers]

            for job in jobs:
                def clean_text(text, max_length=400):
                    if not text or text == 'None':
                        return ''
                    clean = str(text).replace('\n', ' ').replace('\r', ' ')
                    return clean[:max_length] + '...' if len(clean) > max_length else clean

                row = [
                    clean_text(job.get('job_title', ''), 100),
                    clean_text(job.get('company', ''), 50),
                    clean_text(job.get('location', ''), 50),
                    clean_text(job.get('work_model', ''), 30),
                    clean_text(job.get('is_remote', ''), 10),
                    clean_text(job.get('salary', ''), 30),
                    clean_text(job.get('seniority', ''), 50),
                    clean_text(job.get('employment_type', ''), 30),
                    clean_text(job.get('job_summary', ''), 400),
                    clean_text(job.get('core_responsibilities', ''), 300),
                    clean_text(job.get('min_experience', ''), 20),
                    clean_text(job.get('apply_link', ''), 100),
                    clean_text(job.get('job_id', ''), 30),
                    clean_text(job.get('publish_desc', ''), 30),
                    str(job.get('page_number', '')),
                    str(job.get('position_in_page', '')),
                    clean_text(job.get('company_size', ''), 30),
                    clean_text(job.get('keyword_match', 'N/A'), 50),
                    clean_text(job.get('source', ''), 50),
                    clean_text(job.get('scraped_at', ''), 30),
                    clean_text(job.get('scraper_account', ''), 30),
                    clean_text(job.get('scraper_email', ''), 50),
                    clean_text(job.get('job_title_preference', ''), 50)
                ]
                data.append(row)

            # Upload data to sheet
            worksheet.update(values=data, range_name='A1')

            # Format headers
            header_format = {
                "backgroundColor": {"red": 0.0, "green": 0.4, "blue": 0.8},
                "textFormat": {"bold": True, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}
            }
            worksheet.format('A1:W1', header_format)

            logger.info(f"✅ Exported to sheet: {worksheet_name}")
            return worksheet_name

        except Exception as e:
            logger.error(f"❌ Export failed: {e}")
            return None

    def run_complete_multi_account_scraper(self, sheet_url, keyword="", target_jobs=2000, max_concurrent_accounts=20):
        """Complete scraper workflow with multi-account support"""
        try:
            # Run multi-account scraping
            result = self.run_multi_account_scraper(
                target_total_jobs=target_jobs,
                max_concurrent_accounts=max_concurrent_accounts,
                keyword=keyword
            )

            if not result["success"]:
                return result

            jobs = result["jobs"]

            # Export to Google Sheets
            logger.info("📊 Exporting results to Google Sheets...")

            # Export all jobs
            all_jobs_sheet = self.export_to_google_sheets(jobs, sheet_url, "ALL_JOBS_MULTI")

            # Export filtered jobs if keyword was used
            filtered_sheet = None
            if keyword and result["filtered_jobs"] < result["total_jobs"]:
                filtered_jobs = [job for job in jobs if job.get('keyword_match', '') != 'No match']
                filtered_sheet = self.export_to_google_sheets(filtered_jobs, sheet_url, "FILTERED_JOBS_MULTI")

            # Prepare success message
            message = f"🎉 MULTI-ACCOUNT SCRAPING COMPLETE!\n\n"
            message += f"📊 Total jobs collected: {result['total_jobs']}\n"
            message += f"🎯 Jobs matching '{keyword}': {result['filtered_jobs']}\n" if keyword else ""
            message += f"👥 Accounts successfully used: {result['accounts_used']}\n"
            message += f"❌ Accounts failed: {result['accounts_failed']}\n"
            message += f"📋 Data exported to Google Sheets\n"
            message += f"⚡ Simultaneous multi-account scraping achieved maximum diversity!"

            return {
                "success": True,
                "message": message,
                "total_jobs": result["total_jobs"],
                "filtered_jobs": result["filtered_jobs"],
                "accounts_used": result["accounts_used"],
                "accounts_failed": result["accounts_failed"],
                "all_jobs_sheet": all_jobs_sheet,
                "filtered_sheet": filtered_sheet,
                "keyword": keyword
            }

        except Exception as e:
            logger.error(f"❌ Complete scraper error: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}

def main():
    """Command line interface"""
    import argparse

    parser = argparse.ArgumentParser(description='Enhanced Multi-Account JobRight Scraper')
    parser.add_argument('--target', type=int, default=2000, help='Target number of jobs')
    parser.add_argument('--accounts', type=int, default=20, help='Max concurrent accounts to use')
    parser.add_argument('--keyword', type=str, default='', help='Keyword to filter jobs')
    parser.add_argument('--sheet', type=str, required=True, help='Google Sheet ID or URL')

    args = parser.parse_args()

    scraper = MultiAccountJobRightScraper()

    result = scraper.run_complete_multi_account_scraper(
        sheet_url=args.sheet,
        keyword=args.keyword,
        target_jobs=args.target,
        max_concurrent_accounts=args.accounts
    )

    if result["success"]:
        print(result["message"])
    else:
        print(f"❌ Scraping failed: {result['message']}")

if __name__ == "__main__":
    main()
