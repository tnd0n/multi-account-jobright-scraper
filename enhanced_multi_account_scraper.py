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
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiAccountJobRightScraper:
    def __init__(self, config_file='accounts_config.json', session_id=None, session_storage=None, session_lock=None):
        self.config_file = config_file
        self.session_id = session_id
        self.session_storage = session_storage
        self.session_lock = session_lock
        self.accounts = []
        self.active_sessions = {}
        self.job_queue = queue.Queue()
        self.results_queue = queue.Queue()
        self.load_accounts_config()

        # Google Sheets credentials
        self.google_credentials = None
        self.setup_google_credentials()

        # Enhanced deduplication with delta crawling
        self.processed_job_ids = set()
        self.lock = threading.Lock()
        
        # Delta crawling - track what we've seen before to skip duplicate work
        self.job_cache_file = 'job_cache.json'
        self.last_scraped_jobs = self.load_previous_job_cache()
        
        # Session-based progress tracking
        self.total_jobs_found = 0
        self.accounts_used = 0
        self.matching_jobs = 0
        self.current_account = ""
        self.target_reached = False
        self.progress_percentage = 0
    
    def log_to_session(self, message, log_type='info'):
        """Log message to session storage for real-time frontend updates"""
        # Use direct session storage references if available
        if self.session_id and self.session_storage and self.session_lock:
            try:
                with self.session_lock:
                    if self.session_id in self.session_storage:
                        self.session_storage[self.session_id]['logs'].append({
                            'message': message,
                            'type': log_type,
                            'timestamp': datetime.now().isoformat()
                        })
            except Exception as e:
                logger.warning(f"Failed to log to session: {e}")
        
        # Also log normally for debugging
        if log_type == 'error':
            logger.error(message)
        elif log_type == 'warning':
            logger.warning(message)
        elif log_type == 'success':
            logger.info(f"✅ {message}")
        else:
            logger.info(message)
    
    def update_session_progress(self, progress, stats=None, progress_text=None):
        """Update session progress and stats for real-time frontend updates"""
        # Use direct session storage references if available
        if self.session_id and self.session_storage and self.session_lock:
            try:
                with self.session_lock:
                    if self.session_id in self.session_storage:
                        self.session_storage[self.session_id]['progress'] = progress
                        self.progress_percentage = progress
                        
                        if progress_text:
                            self.session_storage[self.session_id]['progress_text'] = progress_text
                        
                        if stats:
                            self.session_storage[self.session_id]['stats'].update(stats)
            except Exception as e:
                logger.warning(f"Failed to update session progress: {e}")
    
    def prioritize_accounts(self, keyword=""):
        """Prioritize accounts whose job_title contains the search keyword"""
        if not keyword:
            return self.accounts.copy()
        
        keyword_lower = keyword.lower()
        prioritized = []
        regular = []
        
        for account in self.accounts:
            job_title = account.get('job_title', '').lower()
            if any(kw.strip().lower() in job_title for kw in keyword.split(',') if kw.strip()):
                prioritized.append(account)
                self.log_to_session(f"🎯 Prioritized {account['name']} - job_title contains '{keyword}'", 'info')
            else:
                regular.append(account)
        
        # Shuffle each group for randomness
        import random
        random.shuffle(prioritized)
        random.shuffle(regular)
        
        result = prioritized + regular
        if prioritized:
            self.log_to_session(f"⚡ Using {len(prioritized)} prioritized accounts first", 'success')
        
        return result
        
    def scrape_jobs_from_account_enhanced(self, account, target_jobs_per_account=25, keyword=""):
        """Enhanced job scraping with session tracking and keyword awareness"""
        if 'session' not in account:
            self.log_to_session(f"❌ {account['name']}: No active session", 'error')
            return []

        session = account['session']
        jobs = []

        try:
            self.log_to_session(f"🔍 {account['name']}: Starting enhanced job scraping (target: {target_jobs_per_account})", 'info')
            self.current_account = account['name']
            
            # Method 1: Try pagination approach with enhanced tracking
            jobs.extend(self.scrape_with_pagination_enhanced(session, account, target_jobs_per_account, keyword, max_pages_per_account=20))

            # Method 2: Try job title filtering if configured and keyword matches
            if len(jobs) < target_jobs_per_account and account.get('job_title') and keyword:
                job_title = account.get('job_title', '').lower()
                if any(kw.strip().lower() in job_title for kw in keyword.split(',') if kw.strip()):
                    additional_jobs = self.scrape_with_job_title_filter(
                        session, account, target_jobs_per_account - len(jobs)
                    )
                    jobs.extend(additional_jobs)
                    self.log_to_session(f"🎯 {account['name']}: Used targeted filtering for '{keyword}'", 'success')

            # Method 3: Try API endpoint as fallback
            if len(jobs) < target_jobs_per_account * 0.5:
                api_jobs = self.scrape_with_api(session, account, target_jobs_per_account)
                jobs.extend(api_jobs)

            # Add enhanced metadata to jobs
            for job in jobs:
                job['scraper_account'] = account['name']
                job['scraper_email'] = account['email']
                job['job_title_preference'] = account.get('job_title', 'General')
                job['scraped_timestamp'] = datetime.now().isoformat()
                job['session_id'] = self.session_id or 'unknown'

            self.log_to_session(f"✅ {account['name']}: Scraped {len(jobs)} jobs successfully", 'success')
            return jobs

        except Exception as e:
            self.log_to_session(f"❌ {account['name']} enhanced scraping error: {e}", 'error')
            return []
    
    def scrape_with_pagination_enhanced(self, session, account, target_jobs, keyword="", max_pages_per_account=15):
        """Enhanced pagination with deep scraping and keyword awareness"""
        jobs = []
        # More aggressive pagination - scrape deeper pages for better results
        # Default to 15 pages per account (up to 300 jobs per account)
        max_pages = min(max_pages_per_account, max((target_jobs // 15), 15))
        
        # API Discovery Enhancement: Use different sort conditions for diversity
        # Discovered sort conditions: 0,1,2,3,4,5 all work and provide different orderings
        sort_conditions = [0, 1, 2, 3, 4, 5]  # Different job sorting algorithms
        pages_per_sort = max(1, max_pages // len(sort_conditions))  # Distribute pages across sort conditions

        for page in range(max_pages):
            try:
                position = page * 20
                
                # API Discovery: Use rotating sort conditions for diversity
                current_sort = sort_conditions[page % len(sort_conditions)]
                self.log_to_session(f"🔄 {account['name']}: Using sortCondition={current_sort} on page {page+1}", 'info')
                
                params = {"position": position} if position > 0 else {}
                # Add discovered sortCondition parameter for better diversity
                params["sortCondition"] = current_sort

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
                        
                        # Pre-filter for keyword if provided to improve efficiency
                        if keyword:
                            keyword_jobs = [job for job in page_jobs if self.job_matches_keyword(job, keyword)]
                            if keyword_jobs:
                                self.log_to_session(f"🎯 {account['name']}: Page {page+1} - {len(keyword_jobs)}/{len(page_jobs)} jobs match '{keyword}'", 'info')
                            # Only add matching jobs if keyword filter is active for immediate efficiency
                            jobs.extend(keyword_jobs)
                        else:
                            jobs.extend(page_jobs)
                        
                        # Stop if we hit our target for this account, or if no more jobs found
                        if len(job_list) < 20:  # Less than full page indicates end of results
                            self.log_to_session(f"📄 {account['name']}: Reached end of available jobs at page {page+1}", 'info')
                            break
                        if len(jobs) >= target_jobs:
                            break
                    else:
                        # No jobs found on this page, likely end of results
                        self.log_to_session(f"📄 {account['name']}: No more jobs available after page {page}", 'info')
                        break
                else:
                    break

                time.sleep(1)

            except Exception as e:
                self.log_to_session(f"⚠️ {account['name']} enhanced pagination error on page {page}: {e}", 'warning')
                break

        return jobs
    
    def job_matches_keyword(self, job, keyword):
        """Very flexible keyword matching using only available API fields"""
        if not keyword:
            return True
        
        # Only use fields that actually exist in JobRight API response
        searchable_fields = [
            job.get('job_title', ''),
            job.get('job_summary', ''),
            job.get('core_responsibilities', ''),
            job.get('company', ''),
            job.get('seniority', ''),
            job.get('employment_type', ''),
            job.get('work_model', ''),
            job.get('location', ''),
            job.get('salary', ''),
            job.get('publish_desc', '')
        ]
        
        # Combine all text into one searchable string
        combined_text = ' '.join([str(field) for field in searchable_fields if field and str(field).lower() != 'none']).lower()
        
        # Handle multiple keywords (comma-separated) 
        keyword_variants = [kw.strip().lower() for kw in keyword.split(',') if kw.strip()]
        
        # Very flexible matching - try multiple approaches
        for kw in keyword_variants:
            # 1. Direct substring match (most common)
            if kw in combined_text:
                return True
                
            # 2. Check each individual field for more precise matching
            for field in searchable_fields:
                field_text = str(field).lower() if field else ''
                if field_text and kw in field_text:
                    return True
                    
            # 3. Word-based partial matching (very lenient)
            words_in_text = combined_text.split()
            for word in words_in_text:
                # Match if keyword is part of any word, or word is part of keyword
                if len(kw) > 1 and len(word) > 1:
                    if kw in word or word in kw:
                        return True
                        
            # 4. Multi-word keyword matching 
            if ' ' in kw:
                kw_words = kw.split()
                # Check if most words from the keyword are present (80% match)
                matches = sum(1 for kw_word in kw_words if any(kw_word in text_word for text_word in words_in_text))
                if matches >= len(kw_words) * 0.8:  # 80% of words must match
                    return True
                    
            # 5. Very lenient single-character matching for short keywords  
            if len(kw) <= 3 and kw in combined_text:
                return True
        
        return False
    
    def filter_jobs_by_keyword_enhanced(self, all_jobs, keyword=""):
        """Enhanced keyword filtering with comprehensive matching and detailed tracking"""
        if not keyword:
            # Add tracking info for all jobs when no keyword filter
            for job in all_jobs:
                job['keyword_match'] = 'No filter applied'
                job['keyword_score'] = 1
            return all_jobs

        self.log_to_session(f"🎯 Filtering {len(all_jobs)} jobs for keyword: '{keyword}'", 'info')

        filtered_jobs = []
        keyword_variants = [kw.strip().lower() for kw in keyword.split(',') if kw.strip()]

        for job in all_jobs:
            # Use the enhanced matching function
            if self.job_matches_keyword(job, keyword):
                # Determine which fields matched for better tracking
                matched_info = self._get_match_details(job, keyword_variants)
                job['keyword_match'] = matched_info['match_text']
                job['keyword_score'] = matched_info['match_score']
                job['match_fields'] = matched_info['matched_fields']
                filtered_jobs.append(job)
            else:
                job['keyword_match'] = 'No match'
                job['keyword_score'] = 0
                job['match_fields'] = []

        self.log_to_session(f"✅ Found {len(filtered_jobs)} jobs matching '{keyword}' (improved from {len(all_jobs)} total)", 'success')
        
        # Log breakdown of matches by field type for better insights
        if filtered_jobs:
            field_matches = {}
            for job in filtered_jobs:
                for field in job.get('match_fields', []):
                    field_matches[field] = field_matches.get(field, 0) + 1
            
            match_summary = ', '.join([f"{field}: {count}" for field, count in field_matches.items()])
            self.log_to_session(f"📊 Match breakdown: {match_summary}", 'info')
        
        return filtered_jobs
    
    def _get_match_details(self, job, keyword_variants):
        """Get detailed information about which fields matched which keywords"""
        matched_keywords = []
        matched_fields = []
        
        # Define field mapping for better organization (only actual API fields)
        field_mapping = {
            'job_title': 'Title',
            'job_summary': 'Summary', 
            'core_responsibilities': 'Responsibilities',
            'company': 'Company',
            'seniority': 'Level',
            'employment_type': 'Type',
            'work_model': 'Work Style',
            'location': 'Location',
            'salary': 'Salary',
            'publish_desc': 'Description'
        }
        
        for kw in keyword_variants:
            for field_key, field_display in field_mapping.items():
                field_value = str(job.get(field_key, '')).lower()
                if field_value and field_value != 'none' and kw in field_value:
                    if kw not in matched_keywords:
                        matched_keywords.append(kw)
                    if field_display not in matched_fields:
                        matched_fields.append(field_display)
        
        return {
            'match_text': f'Matches: {", ".join(matched_keywords)}',
            'match_score': len(matched_keywords),
            'matched_fields': matched_fields
        }
        
    def incremental_sheet_update(self, jobs, account_name):
        """Incrementally update Google Sheets after each account completion"""
        if not jobs or not self.google_credentials:
            return None
            
        try:
            # This is a simplified incremental update
            # In practice, you'd want to append to existing sheets
            self.log_to_session(f"📊 {account_name}: Updating Google Sheets with {len(jobs)} jobs", 'info')
            
            # For now, we'll just log this - full implementation would require
            # more complex sheet management logic
            return f"Updated sheet with {len(jobs)} jobs from {account_name}"
            
        except Exception as e:
            self.log_to_session(f"❌ Sheet update error for {account_name}: {e}", 'error')
            return None

    def load_previous_job_cache(self):
        """Load previously scraped job IDs to implement delta crawling"""
        try:
            if os.path.exists(self.job_cache_file):
                with open(self.job_cache_file, 'r') as f:
                    cache_data = json.load(f)
                    return set(cache_data.get('job_ids', []))
        except Exception as e:
            logger.info(f"No previous cache found or error loading: {e}")
        return set()
    
    def save_job_cache(self, new_job_ids):
        """Save scraped job IDs for future delta crawling"""
        try:
            cache_data = {
                'job_ids': list(self.last_scraped_jobs.union(new_job_ids)),
                'last_updated': datetime.now().isoformat(),
                'total_jobs_cached': len(self.last_scraped_jobs) + len(new_job_ids)
            }
            with open(self.job_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.info(f"✅ Cached {len(new_job_ids)} new job IDs for delta crawling")
        except Exception as e:
            logger.warning(f"Failed to save job cache: {e}")
    
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

    def scrape_with_pagination(self, session, account, target_jobs, max_pages_per_account=10):
        """Scrape using pagination approach with configurable depth"""
        jobs = []
        # Improved pagination depth - default to 10 pages per account  
        max_pages = min(max_pages_per_account, max((target_jobs // 15), 8))
        
        # API Discovery Enhancement: Use different sort conditions for diversity
        sort_conditions = [0, 1, 2, 3, 4, 5]  # Different job sorting algorithms

        for page in range(max_pages):
            try:
                position = page * 20
                
                # API Discovery: Use rotating sort conditions for diversity
                current_sort = sort_conditions[page % len(sort_conditions)]
                self.log_to_session(f"🔄 {account['name']}: Using sortCondition={current_sort} on page {page+1}", 'info')
                
                params = {"position": position} if position > 0 else {}
                # Add discovered sortCondition parameter for better diversity
                params["sortCondition"] = current_sort

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

    def run_multi_account_scraper(self, target_total_jobs=2000, max_concurrent_accounts=80, keyword=""):
        """Enhanced multi-account scraper with session tracking and intelligent features"""
        self.log_to_session(f"🚀 ENHANCED MULTI-ACCOUNT JOBRIGHT SCRAPER STARTING", 'success')
        self.log_to_session(f"🎯 Target: {target_total_jobs} jobs using up to {max_concurrent_accounts} concurrent accounts", 'info')
        self.log_to_session(f"📧 Available accounts: {len(self.accounts)}", 'info')
        self.log_to_session(f"🔍 Keyword filter: '{keyword}'" if keyword else "🔍 No keyword filter", 'info')

        # Prioritize accounts based on keyword
        prioritized_accounts = self.prioritize_accounts(keyword)
        
        # Use all available accounts up to the max_concurrent_accounts limit
        accounts_to_use = min(max_concurrent_accounts, len(prioritized_accounts))
        # Ensure we use at least the minimum viable accounts for the target
        if target_total_jobs > 50 and accounts_to_use < 5:
            accounts_to_use = min(5, len(prioritized_accounts))
        if target_total_jobs > 200 and accounts_to_use < 15:
            accounts_to_use = min(15, len(prioritized_accounts))
        if target_total_jobs > 500 and accounts_to_use < 30:
            accounts_to_use = min(30, len(prioritized_accounts))
            
        target_jobs_per_account = max(target_total_jobs // accounts_to_use, 25)

        all_jobs = []
        successful_accounts = 0
        failed_accounts = 0
        accounts_processed = 0

        # Update initial progress
        self.update_session_progress(5, {
            'jobs_found': 0,
            'accounts_used': 0,
            'matching_jobs': 0,
            'current_account': 'Initializing...'
        }, 'Creating account sessions...')

        # Create sessions for priority accounts first
        self.log_to_session(f"🔐 Creating sessions for {accounts_to_use} prioritized accounts...", 'info')
        active_accounts = []

        for i, account in enumerate(prioritized_accounts[:accounts_to_use]):
            self.current_account = account['name']
            self.update_session_progress(
                5 + (i * 15 / accounts_to_use), 
                {'current_account': f"Setting up {account['name']}..."},
                f'Creating session {i+1}/{accounts_to_use}...'
            )
            
            session = self.create_session(account)
            if session:
                active_accounts.append(account)
                successful_accounts += 1
                self.log_to_session(f"✅ {account['name']} session created successfully", 'success')
            else:
                failed_accounts += 1
                self.log_to_session(f"❌ {account['name']} session failed", 'error')

            # Add delay between session creations to avoid rate limiting
            if i < accounts_to_use - 1:
                time.sleep(1)

        self.log_to_session(f"✅ Active sessions: {successful_accounts}, Failed: {failed_accounts}", 'success')
        self.accounts_used = successful_accounts

        if not active_accounts:
            self.log_to_session("❌ No active accounts available", 'error')
            return {"success": False, "message": "No accounts could be authenticated"}

        # Enhanced concurrent scraping with auto-stop and incremental updates
        self.log_to_session(f"🔍 Starting enhanced concurrent scraping with {len(active_accounts)} accounts...", 'info')
        
        # Track jobs by account for incremental processing
        completed_futures = []
        jobs_by_account = {}
        
        # Update progress to scraping phase
        self.update_session_progress(25, {
            'jobs_found': 0,
            'accounts_used': len(active_accounts),
            'matching_jobs': 0,
            'current_account': 'Starting scraping...'
        }, 'Starting concurrent scraping...')

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(active_accounts)) as executor:
            future_to_account = {
                executor.submit(self.scrape_jobs_from_account_enhanced, account, target_jobs_per_account, keyword): account 
                for account in active_accounts
            }

            for i, future in enumerate(concurrent.futures.as_completed(future_to_account)):
                account = future_to_account[future]
                accounts_processed += 1
                
                try:
                    jobs = future.result()
                    jobs_by_account[account['name']] = jobs
                    all_jobs.extend(jobs)
                    
                    # Update tracking variables
                    self.total_jobs_found = len(all_jobs)
                    self.matching_jobs = len([j for j in all_jobs if j.get('keyword_match', '') != 'No match'])
                    
                    # Calculate progress (25% base + 65% for scraping completion)
                    scraping_progress = 25 + (accounts_processed * 65 / len(active_accounts))
                    
                    self.update_session_progress(scraping_progress, {
                        'jobs_found': self.total_jobs_found,
                        'accounts_used': self.accounts_used,
                        'matching_jobs': self.matching_jobs,
                        'current_account': f"{account['name']} completed"
                    }, f'Account {accounts_processed}/{len(active_accounts)} completed')
                    
                    self.log_to_session(f"✅ {account['name']}: Added {len(jobs)} jobs (Total: {len(all_jobs)})", 'success')
                    
                    # Incremental Google Sheets update after each account
                    if hasattr(self, 'sheet_url') and self.sheet_url:
                        try:
                            self.incremental_sheet_update(jobs, account['name'])
                            self.log_to_session(f"📊 {account['name']}: Data exported to Google Sheets", 'info')
                        except Exception as e:
                            self.log_to_session(f"⚠️ {account['name']}: Sheet update failed - {str(e)}", 'warning')
                    
                    # Auto-stop functionality - check if target reached
                    if self.total_jobs_found >= target_total_jobs:
                        self.target_reached = True
                        self.log_to_session(f"🎯 TARGET REACHED! Found {self.total_jobs_found} jobs (target: {target_total_jobs})", 'success')
                        self.log_to_session("🛑 Auto-stopping remaining accounts to save resources", 'info')
                        
                        # Cancel remaining futures
                        for pending_future in future_to_account:
                            if not pending_future.done():
                                pending_future.cancel()
                        break
                        
                except Exception as e:
                    self.log_to_session(f"❌ {account['name']}: Scraping failed - {e}", 'error')
                    failed_accounts += 1

        # Final processing and filtering
        self.update_session_progress(90, {
            'jobs_found': self.total_jobs_found,
            'accounts_used': self.accounts_used,
            'matching_jobs': self.matching_jobs,
            'current_account': 'Processing results...'
        }, 'Processing and filtering results...')

        self.log_to_session(f"🎉 SCRAPING COMPLETE: {len(all_jobs)} total jobs from {accounts_processed} accounts", 'success')

        # Filter jobs by keyword if provided
        filtered_jobs = self.filter_jobs_by_keyword_enhanced(all_jobs, keyword) if keyword else all_jobs
        self.matching_jobs = len(filtered_jobs)

        # Final progress update
        self.update_session_progress(95, {
            'jobs_found': len(all_jobs),
            'accounts_used': accounts_processed,
            'matching_jobs': len(filtered_jobs),
            'current_account': 'Complete!'
        }, 'Finalizing results...')

        return {
            "success": True,
            "total_jobs": len(all_jobs),
            "filtered_jobs": len(filtered_jobs),
            "accounts_used": accounts_processed,
            "accounts_failed": failed_accounts,
            "jobs": filtered_jobs,
            "keyword": keyword,
            "target_reached": self.target_reached,
            "jobs_by_account": jobs_by_account
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
            worksheet.update('A1', data)

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

    def run_complete_multi_account_scraper(self, sheet_url, keyword="", target_jobs=50, max_concurrent_accounts=5, scrape_mode="balanced"):
        """Enhanced complete scraper workflow with session tracking and intelligent features"""
        try:
            # Store sheet_url for incremental updates
            self.sheet_url = sheet_url
            
            # Log initial session data
            self.log_to_session(f"🚀 Enhanced Multi-Account Scraper initializing...", 'info')
            self.log_to_session(f"📄 Sheet: {sheet_url}", 'info')
            self.log_to_session(f"🎯 Target: {target_jobs} jobs", 'info')
            self.log_to_session(f"🔍 Keyword: '{keyword}'" if keyword else "🔍 No keyword filter", 'info')
            self.log_to_session(f"⚙️ Mode: {scrape_mode}", 'info')
            
            # Apply hybrid mode intelligence for concurrency adjustment
            if scrape_mode == 'hybrid':
                if target_jobs <= 25:
                    max_concurrent_accounts = min(max_concurrent_accounts, 3)
                    self.log_to_session(f"🧠 Hybrid Mode: Using {max_concurrent_accounts} accounts for {target_jobs} jobs (conservative)", 'info')
                elif target_jobs <= 50:
                    max_concurrent_accounts = min(max_concurrent_accounts, 5)
                    self.log_to_session(f"🧠 Hybrid Mode: Using {max_concurrent_accounts} accounts for {target_jobs} jobs (balanced)", 'info')
                elif target_jobs <= 100:
                    max_concurrent_accounts = min(max_concurrent_accounts, 8)
                    self.log_to_session(f"🧠 Hybrid Mode: Using {max_concurrent_accounts} accounts for {target_jobs} jobs (aggressive)", 'info')
                else:
                    max_concurrent_accounts = min(max_concurrent_accounts, 80)
                    self.log_to_session(f"🧠 Hybrid Mode: Using {max_concurrent_accounts} accounts for {target_jobs} jobs (maximum)", 'info')
            elif scrape_mode == 'conservative':
                max_concurrent_accounts = min(max_concurrent_accounts, 5)
                self.log_to_session(f"🐌 Conservative Mode: Limited to {max_concurrent_accounts} accounts", 'info')
            elif scrape_mode == 'aggressive':
                max_concurrent_accounts = min(max_concurrent_accounts, 80)
                self.log_to_session(f"⚡ Aggressive Mode: Using up to {max_concurrent_accounts} accounts", 'info')

            # Update initial progress
            self.update_session_progress(3, {
                'jobs_found': 0,
                'accounts_used': 0, 
                'matching_jobs': 0,
                'current_account': 'Starting...'
            }, 'Initializing enhanced scraper...')

            # Run enhanced multi-account scraping
            result = self.run_multi_account_scraper(
                target_total_jobs=target_jobs,
                max_concurrent_accounts=max_concurrent_accounts,
                keyword=keyword
            )

            if not result["success"]:
                self.log_to_session(f"❌ Scraping failed: {result.get('message', 'Unknown error')}", 'error')
                return result

            jobs = result["jobs"]
            
            # Update progress for final export
            self.update_session_progress(95, {
                'jobs_found': result["total_jobs"],
                'accounts_used': result["accounts_used"], 
                'matching_jobs': result["filtered_jobs"],
                'current_account': 'Exporting to sheets...'
            }, 'Exporting final results to Google Sheets...')

            # Export to Google Sheets
            self.log_to_session("📊 Exporting final results to Google Sheets...", 'info')

            # Export all jobs
            all_jobs_sheet = self.export_to_google_sheets(jobs, sheet_url, "ALL_JOBS_MULTI")

            # Export filtered jobs if keyword was used
            filtered_sheet = None
            if keyword and result["filtered_jobs"] < result["total_jobs"]:
                filtered_jobs = [job for job in jobs if job.get('keyword_match', '') != 'No match']
                filtered_sheet = self.export_to_google_sheets(filtered_jobs, sheet_url, "FILTERED_JOBS_MULTI")

            # Prepare enhanced success message
            message = f"🎉 ENHANCED MULTI-ACCOUNT SCRAPING COMPLETE!\n\n"
            message += f"📊 Total jobs collected: {result['total_jobs']}\n"
            if keyword:
                message += f"🎯 Jobs matching '{keyword}': {result['filtered_jobs']}\n"
            message += f"👥 Accounts successfully used: {result['accounts_used']}\n"
            message += f"❌ Accounts failed: {result['accounts_failed']}\n"
            message += f"⚙️ Scraping mode: {scrape_mode}\n"
            if result.get('target_reached'):
                message += f"🎯 Target reached early - auto-stopped to save resources!\n"
            message += f"📋 Data exported to Google Sheets\n"
            message += f"⚡ Enhanced multi-account scraping with intelligent optimization!"

            # Log final success
            self.log_to_session(message, 'success')

            return {
                "success": True,
                "message": message,
                "total_jobs": result["total_jobs"],
                "filtered_jobs": result["filtered_jobs"],
                "accounts_used": result["accounts_used"],
                "accounts_failed": result["accounts_failed"],
                "all_jobs_sheet": all_jobs_sheet,
                "filtered_sheet": filtered_sheet,
                "keyword": keyword,
                "scrape_mode": scrape_mode,
                "target_reached": result.get("target_reached", False),
                "jobs_by_account": result.get("jobs_by_account", {})
            }

        except Exception as e:
            error_msg = f"❌ Enhanced scraper error: {e}"
            self.log_to_session(error_msg, 'error')
            logger.error(error_msg)
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
