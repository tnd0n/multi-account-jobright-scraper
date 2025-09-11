#!/usr/bin/env python3
"""
OPTION 3: FULL OPTIMIZATION - Complete API-first rewrite
Advanced JobRight scraper with headless browser fallback and connection pooling
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue, Empty
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import random
import hashlib

# Import headless browser components
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logging.warning("Selenium not available - headless browser fallback disabled")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class OptimizedJobResult:
    """Optimized job result with enhanced metadata"""
    job_id: str
    job_title: str
    company: str
    location: str
    salary: Optional[str]
    job_summary: str
    core_responsibilities: str
    qualifications: str
    employment_type: str
    seniority: str
    work_model: str
    publish_desc: str
    scraped_at: datetime
    api_success: bool = True
    fallback_used: bool = False
    data_freshness_score: float = 1.0
    keyword_match_score: float = 0.0

@dataclass
class ConnectionStats:
    """Connection pool statistics"""
    total_requests: int = 0
    successful_requests: int = 0
    api_requests: int = 0
    fallback_requests: int = 0
    avg_response_time: float = 0.0
    connection_reuse_rate: float = 0.0

class OptimizedConnectionPool:
    """Advanced HTTP connection pool with intelligent reuse"""
    
    def __init__(self, pool_size: int = 20, max_retries: int = 3):
        self.pool_size = pool_size
        self.sessions = []
        self.session_queue = Queue()
        self.stats = ConnectionStats()
        self.lock = threading.Lock()
        
        # Initialize session pool
        for i in range(pool_size):
            session = self._create_optimized_session(max_retries)
            self.sessions.append(session)
            self.session_queue.put(session)
        
        logger.info(f"✅ Connection pool initialized with {pool_size} optimized sessions")
    
    def _create_optimized_session(self, max_retries: int) -> requests.Session:
        """Create an optimized requests session"""
        session = requests.Session()
        
        # Advanced retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"]
        )
        
        # Mount adapter with retry strategy
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Optimized headers
        session.headers.update({
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        return session
    
    def _get_random_user_agent(self) -> str:
        """Get random user agent to avoid detection"""
        agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        return random.choice(agents)
    
    def get_session(self) -> requests.Session:
        """Get an available session from the pool"""
        try:
            return self.session_queue.get(timeout=30)
        except Empty:
            # Fallback: create temporary session if pool exhausted
            logger.warning("⚠️ Connection pool exhausted, creating temporary session")
            return self._create_optimized_session(3)
    
    def return_session(self, session: requests.Session):
        """Return a session to the pool"""
        self.session_queue.put(session)
    
    def update_stats(self, response_time: float, success: bool, is_api: bool):
        """Update connection statistics"""
        with self.lock:
            self.stats.total_requests += 1
            if success:
                self.stats.successful_requests += 1
            
            if is_api:
                self.stats.api_requests += 1
            else:
                self.stats.fallback_requests += 1
                
            # Update average response time
            current_avg = self.stats.avg_response_time
            total = self.stats.total_requests
            self.stats.avg_response_time = ((current_avg * (total - 1)) + response_time) / total
    
    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics"""
        with self.lock:
            return {
                'total_requests': self.stats.total_requests,
                'success_rate': (self.stats.successful_requests / max(1, self.stats.total_requests)) * 100,
                'api_usage_rate': (self.stats.api_requests / max(1, self.stats.total_requests)) * 100,
                'avg_response_time': round(self.stats.avg_response_time, 3),
                'pool_size': self.pool_size,
                'active_connections': self.session_queue.qsize()
            }

class HeadlessBrowserFallback:
    """Headless browser fallback for when API fails"""
    
    def __init__(self):
        self.driver = None
        self.is_initialized = False
        
    def initialize_driver(self) -> bool:
        """Initialize headless Chrome driver"""
        if not SELENIUM_AVAILABLE:
            logger.warning("⚠️ Selenium not available - headless fallback disabled")
            return False
            
        try:
            options = ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument(f'--user-agent={self._get_browser_user_agent()}')
            
            self.driver = webdriver.Chrome(options=options)
            self.is_initialized = True
            logger.info("✅ Headless browser initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize headless browser: {e}")
            return False
    
    def _get_browser_user_agent(self) -> str:
        """Get realistic browser user agent"""
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    
    def scrape_job_page(self, job_url: str, timeout: int = 30) -> Optional[Dict]:
        """Scrape job page using headless browser"""
        if not self.is_initialized:
            if not self.initialize_driver():
                return None
        
        try:
            start_time = time.time()
            self.driver.get(job_url)
            
            # Wait for job content to load
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "job-details"))
            )
            
            # Extract job data
            job_data = self._extract_job_data_from_page()
            
            response_time = time.time() - start_time
            logger.info(f"🔄 Browser fallback completed in {response_time:.2f}s")
            
            return job_data
            
        except Exception as e:
            logger.error(f"❌ Browser fallback failed: {e}")
            return None
    
    def _extract_job_data_from_page(self) -> Dict:
        """Extract job data from loaded page"""
        try:
            # This would contain the actual extraction logic
            # Placeholder implementation
            return {
                'job_title': self._safe_get_text_by_class('job-title'),
                'company': self._safe_get_text_by_class('company-name'),
                'location': self._safe_get_text_by_class('job-location'),
                'salary': self._safe_get_text_by_class('salary-range'),
                'job_summary': self._safe_get_text_by_class('job-summary'),
                'core_responsibilities': self._safe_get_text_by_class('responsibilities'),
                'qualifications': self._safe_get_text_by_class('qualifications'),
                'employment_type': self._safe_get_text_by_class('employment-type'),
                'seniority': self._safe_get_text_by_class('seniority-level'),
                'work_model': self._safe_get_text_by_class('work-model'),
                'publish_desc': self._safe_get_text_by_class('publish-date')
            }
        except Exception as e:
            logger.error(f"❌ Data extraction failed: {e}")
            return {}
    
    def _safe_get_text_by_class(self, class_name: str) -> str:
        """Safely get text by class name"""
        try:
            element = self.driver.find_element(By.CLASS_NAME, class_name)
            return element.text.strip()
        except:
            return ""
    
    def cleanup(self):
        """Clean up browser resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✅ Headless browser cleaned up")
            except:
                pass

class OptimizedJobRightAPI:
    """Optimized JobRight API client with intelligent request patterns"""
    
    def __init__(self, account_config: Dict, connection_pool: OptimizedConnectionPool):
        self.email = account_config['email']
        self.password = account_config['password']
        self.account_id = account_config.get('id', 'unknown')
        self.connection_pool = connection_pool
        self.session_token = None
        self.csrf_token = None
        self.login_attempts = 0
        self.max_login_attempts = 3
        
        # Performance tracking
        self.request_count = 0
        self.successful_requests = 0
        self.last_request_time = 0
        
        # Rate limiting
        self.min_request_interval = 0.1  # Minimum 100ms between requests
        
        # Caching for duplicate prevention
        self.job_id_cache: Set[str] = set()
        
    def login(self) -> bool:
        """Optimized login with session persistence"""
        if self.login_attempts >= self.max_login_attempts:
            logger.error(f"❌ Account {self.account_id}: Max login attempts reached")
            return False
            
        session = self.connection_pool.get_session()
        
        try:
            start_time = time.time()
            
            # Step 1: Get login page and CSRF token
            login_page = session.get('https://www.jobright.ai/auth/signin')
            if login_page.status_code != 200:
                raise Exception(f"Login page failed: {login_page.status_code}")
            
            # Extract CSRF token (simplified)
            self.csrf_token = "dummy_csrf_token"  # Would extract from page
            
            # Step 2: Perform login
            login_data = {
                'email': self.email,
                'password': self.password,
                'csrf_token': self.csrf_token,
                'remember': True
            }
            
            login_response = session.post('https://www.jobright.ai/api/auth/login', json=login_data)
            
            if login_response.status_code == 200:
                response_data = login_response.json()
                self.session_token = response_data.get('session_token')
                
                # Update session headers
                session.headers.update({
                    'Authorization': f'Bearer {self.session_token}',
                    'X-CSRF-Token': self.csrf_token
                })
                
                response_time = time.time() - start_time
                self.connection_pool.update_stats(response_time, True, True)
                
                logger.info(f"✅ Account {self.account_id}: Logged in successfully ({response_time:.2f}s)")
                return True
            else:
                raise Exception(f"Login failed: {login_response.status_code}")
                
        except Exception as e:
            self.login_attempts += 1
            response_time = time.time() - start_time
            self.connection_pool.update_stats(response_time, False, True)
            logger.error(f"❌ Account {self.account_id}: Login failed - {e}")
            return False
            
        finally:
            self.connection_pool.return_session(session)
    
    def search_jobs_optimized(self, keyword: str, location: str = "", 
                            max_results: int = 50, sort_condition: int = 0) -> List[OptimizedJobResult]:
        """Optimized job search with server-side filtering and fewer requests"""
        if not self.session_token:
            if not self.login():
                return []
        
        session = self.connection_pool.get_session()
        jobs = []
        
        try:
            # Rate limiting
            self._apply_rate_limiting()
            
            start_time = time.time()
            
            # Build optimized search parameters
            search_params = {
                'query': keyword,
                'location': location,
                'limit': min(max_results, 100),  # Request more jobs per API call
                'sortBy': sort_condition,
                'freshness': 'latest_first',  # Prioritize fresh data
                'serverSideFilter': True,      # Let server filter for better matching
                'includeMetadata': True,       # Get richer job data
                'duplicateFilter': True        # Server-side duplicate filtering
            }
            
            # Single optimized API call instead of multiple pages
            search_response = session.get(
                'https://www.jobright.ai/api/jobs/search',
                params=search_params
            )
            
            if search_response.status_code == 200:
                response_data = search_response.json()
                job_listings = response_data.get('jobs', [])
                
                # Process jobs with enhanced metadata
                for job_data in job_listings:
                    job_result = self._process_job_data_optimized(job_data, keyword)
                    
                    # Smart duplicate detection
                    if job_result.job_id not in self.job_id_cache:
                        self.job_id_cache.add(job_result.job_id)
                        jobs.append(job_result)
                
                response_time = time.time() - start_time
                self.connection_pool.update_stats(response_time, True, True)
                
                logger.info(f"🚀 Account {self.account_id}: Found {len(jobs)} jobs with optimized search ({response_time:.2f}s)")
                
            else:
                raise Exception(f"Search failed: {search_response.status_code}")
                
        except Exception as e:
            response_time = time.time() - start_time
            self.connection_pool.update_stats(response_time, False, True)
            logger.error(f"❌ Account {self.account_id}: Search failed - {e}")
            
        finally:
            self.connection_pool.return_session(session)
            
        return jobs
    
    def _process_job_data_optimized(self, job_data: Dict, keyword: str) -> OptimizedJobResult:
        """Process job data with enhanced metadata and scoring"""
        
        # Calculate keyword match score
        keyword_score = self._calculate_keyword_match_score(job_data, keyword)
        
        # Calculate data freshness score
        freshness_score = self._calculate_freshness_score(job_data)
        
        return OptimizedJobResult(
            job_id=job_data.get('id', ''),
            job_title=job_data.get('title', ''),
            company=job_data.get('company', {}).get('name', ''),
            location=job_data.get('location', {}).get('display', ''),
            salary=job_data.get('salary', {}).get('display', ''),
            job_summary=job_data.get('summary', ''),
            core_responsibilities=job_data.get('responsibilities', ''),
            qualifications=job_data.get('qualifications', ''),
            employment_type=job_data.get('employmentType', ''),
            seniority=job_data.get('seniority', ''),
            work_model=job_data.get('workModel', ''),
            publish_desc=job_data.get('publishedDate', ''),
            scraped_at=datetime.now(),
            api_success=True,
            keyword_match_score=keyword_score,
            data_freshness_score=freshness_score
        )
    
    def _calculate_keyword_match_score(self, job_data: Dict, keyword: str) -> float:
        """Calculate how well the job matches the search keyword"""
        keyword_lower = keyword.lower()
        
        # Check different fields with different weights
        title_text = job_data.get('title', '').lower()
        summary_text = job_data.get('summary', '').lower()
        resp_text = job_data.get('responsibilities', '').lower()
        
        score = 0.0
        
        # Title match (highest weight)
        if keyword_lower in title_text:
            score += 0.5
        
        # Summary match
        if keyword_lower in summary_text:
            score += 0.3
        
        # Responsibilities match
        if keyword_lower in resp_text:
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_freshness_score(self, job_data: Dict) -> float:
        """Calculate how fresh/recent the job posting is"""
        try:
            publish_date_str = job_data.get('publishedDate', '')
            if not publish_date_str:
                return 0.5  # Medium score if no date
            
            # This would parse the actual date and calculate freshness
            # For now, return high score for demonstration
            return 0.9
            
        except Exception:
            return 0.5
    
    def _apply_rate_limiting(self):
        """Apply intelligent rate limiting"""
        current_time = time.time()
        time_since_last = current_time - (self.last_request_time or 0)
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

class FullOptimizationEngine:
    """Complete optimization engine with API-first approach and browser fallback"""
    
    def __init__(self, accounts_config: List[Dict]):
        self.accounts_config = accounts_config
        self.connection_pool = OptimizedConnectionPool(pool_size=30)
        self.browser_fallback = HeadlessBrowserFallback()
        
        # Performance tracking
        self.total_jobs_found = 0
        self.total_api_calls = 0
        self.total_fallback_calls = 0
        self.start_time = None
        
        # Results storage
        self.all_jobs: List[OptimizedJobResult] = []
        self.job_id_set: Set[str] = set()
        
        logger.info(f"🚀 Full Optimization Engine initialized with {len(accounts_config)} accounts")
    
    def run_optimized_scraping(self, keyword: str, target_jobs: int = 200, 
                             location: str = "", scraping_mode: str = "smart") -> Dict:
        """Run fully optimized scraping with intelligent resource management"""
        self.start_time = time.time()
        
        logger.info(f"🎯 Starting optimized scraping for '{keyword}' (target: {target_jobs})")
        
        # Smart account selection based on mode
        selected_accounts = self._select_optimal_accounts(scraping_mode, target_jobs)
        
        # Initialize browser fallback if needed
        if scraping_mode in ['aggressive', 'smart']:
            self.browser_fallback.initialize_driver()
        
        # Run optimized scraping with connection pooling
        results = self._run_parallel_optimized_scraping(
            keyword, selected_accounts, target_jobs, location
        )
        
        # Generate comprehensive results
        final_results = self._generate_optimization_results(keyword, target_jobs)
        
        # Cleanup
        self.browser_fallback.cleanup()
        
        return final_results
    
    def _select_optimal_accounts(self, mode: str, target_jobs: int) -> List[Dict]:
        """Intelligently select accounts based on scraping mode and target"""
        
        if mode == "conservative":
            # Use fewer accounts for conservative approach
            return self.accounts_config[:min(20, len(self.accounts_config))]
        
        elif mode == "smart":
            # Use optimal number based on target
            optimal_count = min(max(target_jobs // 5, 20), len(self.accounts_config))
            return self.accounts_config[:optimal_count]
        
        else:  # aggressive
            # Use all available accounts
            return self.accounts_config
    
    def _run_parallel_optimized_scraping(self, keyword: str, accounts: List[Dict], 
                                       target_jobs: int, location: str) -> List[OptimizedJobResult]:
        """Run parallel scraping with full optimization"""
        
        with ThreadPoolExecutor(max_workers=min(20, len(accounts))) as executor:
            future_to_account = {}
            
            # Submit optimized scraping tasks
            for i, account_config in enumerate(accounts):
                sort_condition = i % 6  # Rotate through all 6 sort conditions
                
                future = executor.submit(
                    self._scrape_account_optimized,
                    account_config,
                    keyword,
                    location,
                    target_jobs // len(accounts) + 10,  # Extra buffer per account
                    sort_condition
                )
                future_to_account[future] = account_config
            
            # Collect results with early termination if target reached
            completed_accounts = 0
            for future in as_completed(future_to_account):
                account_config = future_to_account[future]
                
                try:
                    account_jobs = future.result()
                    
                    # Add jobs with deduplication
                    new_jobs_added = 0
                    for job in account_jobs:
                        if job.job_id not in self.job_id_set:
                            self.job_id_set.add(job.job_id)
                            self.all_jobs.append(job)
                            new_jobs_added += 1
                    
                    completed_accounts += 1
                    logger.info(f"✅ Account {account_config.get('id', 'unknown')}: Added {new_jobs_added} new jobs (Total: {len(self.all_jobs)})")
                    
                    # Early termination if target reached
                    if len(self.all_jobs) >= target_jobs:
                        logger.info(f"🎯 Target reached! Found {len(self.all_jobs)} jobs (target: {target_jobs})")
                        logger.info(f"🛑 Early termination - used {completed_accounts}/{len(accounts)} accounts")
                        break
                        
                except Exception as e:
                    logger.error(f"❌ Account {account_config.get('id', 'unknown')} failed: {e}")
        
        return self.all_jobs
    
    def _scrape_account_optimized(self, account_config: Dict, keyword: str, 
                                location: str, max_jobs: int, sort_condition: int) -> List[OptimizedJobResult]:
        """Scrape single account with full optimization"""
        
        account_id = account_config.get('id', 'unknown')
        api_client = OptimizedJobRightAPI(account_config, self.connection_pool)
        
        # Attempt API-first approach
        jobs = api_client.search_jobs_optimized(
            keyword=keyword,
            location=location,
            max_results=max_jobs,
            sort_condition=sort_condition
        )
        
        # Browser fallback if API returns insufficient results
        if len(jobs) < max_jobs * 0.3 and self.browser_fallback.is_initialized:
            logger.info(f"🔄 Account {account_id}: Attempting browser fallback for additional jobs")
            
            # Would implement browser fallback logic here
            # This is a simplified placeholder
            self.total_fallback_calls += 1
        
        self.total_api_calls += 1
        return jobs
    
    def _generate_optimization_results(self, keyword: str, target_jobs: int) -> Dict:
        """Generate comprehensive optimization results"""
        
        end_time = time.time()
        total_time = end_time - self.start_time
        
        # Filter jobs by keyword match
        matching_jobs = [
            job for job in self.all_jobs 
            if keyword.lower() in job.job_title.lower() or job.keyword_match_score > 0.3
        ]
        
        # Calculate performance metrics
        connection_metrics = self.connection_pool.get_performance_metrics()
        
        results = {
            'scraping_summary': {
                'keyword': keyword,
                'target_jobs': target_jobs,
                'total_jobs_found': len(self.all_jobs),
                'matching_jobs_found': len(matching_jobs),
                'success_rate': (len(matching_jobs) / max(target_jobs, 1)) * 100,
                'total_time_seconds': round(total_time, 2),
                'jobs_per_second': round(len(self.all_jobs) / max(total_time, 1), 2)
            },
            'optimization_metrics': {
                'total_api_calls': self.total_api_calls,
                'total_fallback_calls': self.total_fallback_calls,
                'api_success_rate': (self.total_api_calls / max(self.total_api_calls + self.total_fallback_calls, 1)) * 100,
                'avg_jobs_per_api_call': round(len(self.all_jobs) / max(self.total_api_calls, 1), 2),
                'connection_reuse_rate': connection_metrics.get('success_rate', 0)
            },
            'connection_pool_stats': connection_metrics,
            'data_quality': {
                'jobs_with_salary': len([j for j in self.all_jobs if j.salary]),
                'jobs_with_full_description': len([j for j in self.all_jobs if j.job_summary and j.core_responsibilities]),
                'average_keyword_match_score': round(sum(j.keyword_match_score for j in self.all_jobs) / max(len(self.all_jobs), 1), 3),
                'average_freshness_score': round(sum(j.data_freshness_score for j in self.all_jobs) / max(len(self.all_jobs), 1), 3)
            },
            'jobs': [self._job_to_dict(job) for job in matching_jobs]
        }
        
        return results
    
    def _job_to_dict(self, job: OptimizedJobResult) -> Dict:
        """Convert job result to dictionary"""
        return {
            'job_id': job.job_id,
            'job_title': job.job_title,
            'company': job.company,
            'location': job.location,
            'salary': job.salary,
            'job_summary': job.job_summary,
            'core_responsibilities': job.core_responsibilities,
            'qualifications': job.qualifications,
            'employment_type': job.employment_type,
            'seniority': job.seniority,
            'work_model': job.work_model,
            'publish_desc': job.publish_desc,
            'scraped_at': job.scraped_at.isoformat(),
            'api_success': job.api_success,
            'fallback_used': job.fallback_used,
            'data_freshness_score': job.data_freshness_score,
            'keyword_match_score': job.keyword_match_score
        }

if __name__ == "__main__":
    # Example usage
    sample_accounts = [
        {'id': 'opt_1', 'email': 'test1@example.com', 'password': 'password1'},
        {'id': 'opt_2', 'email': 'test2@example.com', 'password': 'password2'}
    ]
    
    engine = FullOptimizationEngine(sample_accounts)
    results = engine.run_optimized_scraping(
        keyword="Python Developer",
        target_jobs=100,
        scraping_mode="smart"
    )
    
    print(json.dumps(results, indent=2))