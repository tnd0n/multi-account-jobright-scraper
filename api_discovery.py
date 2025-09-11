#!/usr/bin/env python3
"""
JobRight API Discovery Tool
Systematically tests API endpoints, parameters, and capabilities
to discover undocumented features and optimization opportunities
"""

import requests
import json
import time
import logging
from datetime import datetime
from enhanced_multi_account_scraper import MultiAccountJobRightScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobRightAPIDiscovery:
    def __init__(self):
        self.scraper = MultiAccountJobRightScraper()
        self.test_session = None
        self.test_account = None
        self.discovered_endpoints = []
        self.discovered_parameters = {}
        self.api_capabilities = {}
        
    def setup_test_session(self):
        """Setup a test session with authenticated account"""
        logger.info("🔍 Setting up API discovery test session...")
        
        # Use the first available account for testing
        self.scraper.load_accounts_config()  # This populates self.scraper.accounts
        
        if not self.scraper.accounts:
            logger.error("❌ No accounts available for testing")
            return False
            
        self.test_account = self.scraper.accounts[0]
        logger.info(f"Using test account: {self.test_account.get('email', 'unknown')}")
        
        # Create authenticated session
        session = self.scraper.create_session(self.test_account)
        if session:
            self.test_session = session
            logger.info(f"✅ Test session ready with {self.test_account['email']}")
            return True
        else:
            logger.error("❌ Failed to authenticate test account")
            return False
    
    def discover_endpoint_parameters(self, base_endpoint, known_params=None):
        """Test various parameters on known endpoints"""
        logger.info(f"🔍 Testing parameters for: {base_endpoint}")
        
        if known_params is None:
            known_params = {}
        
        # Parameter discovery tests
        test_parameters = {
            'position': [0, 20, 50, 100],
            'limit': [10, 20, 50, 100, 200],
            'pageSize': [10, 20, 50, 100],
            'sortCondition': [0, 1, 2, 3, 4, 5],
            'sortBy': ['relevance', 'date', 'salary', 'location', 'company'],
            'sortOrder': ['asc', 'desc'],
            'refresh': [True, False],
            'includeDetails': [True, False],
            'includeCompany': [True, False],
            'format': ['json', 'detailed'],
            'version': ['v1', 'v2', 'v3'],
            'fields': ['all', 'basic', 'detailed'],
            'expand': ['company', 'salary', 'location', 'all']
        }
        
        successful_params = {}
        
        for param_name, param_values in test_parameters.items():
            for param_value in param_values:
                try:
                    if not self.test_session:
                        logger.error("❌ No authenticated session available")
                        return {}
                    
                    test_params = known_params.copy()
                    test_params[param_name] = param_value
                    
                    response = self.test_session.get(
                        base_endpoint,
                        params=test_params,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('success') and data.get('result'):
                            job_count = len(data.get('result', {}).get('jobList', []))
                            successful_params[f"{param_name}={param_value}"] = {
                                'status_code': response.status_code,
                                'job_count': job_count,
                                'response_size': len(response.text),
                                'has_pagination': 'pagination' in str(data).lower()
                            }
                            logger.info(f"✅ {param_name}={param_value}: {job_count} jobs")
                        else:
                            logger.debug(f"⚠️ {param_name}={param_value}: Success=False")
                    else:
                        logger.debug(f"❌ {param_name}={param_value}: HTTP {response.status_code}")
                        
                    time.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    logger.debug(f"⚠️ {param_name}={param_value}: Error {e}")
                    continue
        
        return successful_params
    
    def discover_alternative_endpoints(self):
        """Test for additional API endpoints using common patterns"""
        logger.info("🔍 Discovering alternative API endpoints...")
        
        base_urls = [
            "https://jobright.ai/swan",
            "https://jobright.ai/api",
            "https://jobright.ai/v1",
            "https://jobright.ai/v2"
        ]
        
        endpoint_patterns = [
            # Job-related endpoints
            "/jobs", "/jobs/search", "/jobs/list", "/jobs/advanced", "/jobs/filtered",
            "/search", "/search/jobs", "/search/advanced", "/search/filters",
            "/recommend/jobs", "/recommend/search", "/recommend/advanced",
            "/recommend/landing/jobs/advanced", "/recommend/landing/search",
            
            # Company endpoints  
            "/companies", "/companies/search", "/companies/list",
            "/company", "/company/jobs", "/company/search",
            
            # Filter and preference endpoints
            "/filters", "/filters/available", "/filters/options",
            "/preferences", "/user/preferences", "/search/preferences",
            "/taxonomy", "/categories", "/skills",
            
            # Analytics and insights
            "/analytics", "/insights", "/trends", "/stats",
            "/recommend/insights", "/recommend/analytics",
            
            # Alternative data formats
            "/recommend/landing/jobs/v2", "/recommend/landing/jobs/detailed",
            "/recommend/list/jobs/v2", "/recommend/list/jobs/detailed"
        ]
        
        discovered_endpoints = {}
        
        for base_url in base_urls:
            for pattern in endpoint_patterns:
                endpoint = f"{base_url}{pattern}"
                try:
                    if not self.test_session:
                        logger.error("❌ No authenticated session available")
                        return {}
                        
                    response = self.test_session.get(endpoint, timeout=5)
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            discovered_endpoints[endpoint] = {
                                'status_code': 200,
                                'response_size': len(response.text),
                                'has_data': bool(data),
                                'success': data.get('success', False),
                                'result_keys': list(data.get('result', {}).keys()) if data.get('result') else []
                            }
                            logger.info(f"✅ Found endpoint: {endpoint}")
                        except:
                            discovered_endpoints[endpoint] = {
                                'status_code': 200,
                                'content_type': response.headers.get('content-type', ''),
                                'is_html': 'html' in response.headers.get('content-type', '').lower()
                            }
                    elif response.status_code == 404:
                        logger.debug(f"❌ Not found: {endpoint}")
                    elif response.status_code in [401, 403]:
                        # Might exist but require different auth
                        discovered_endpoints[endpoint] = {'status_code': response.status_code, 'note': 'auth_required'}
                        logger.info(f"🔒 Auth required: {endpoint}")
                    else:
                        logger.debug(f"⚠️ {endpoint}: HTTP {response.status_code}")
                        
                    time.sleep(0.3)  # Rate limiting
                    
                except Exception as e:
                    logger.debug(f"⚠️ {endpoint}: {e}")
                    continue
        
        return discovered_endpoints
    
    def test_advanced_filtering_capabilities(self):
        """Test advanced filtering and search capabilities"""
        logger.info("🔍 Testing advanced filtering capabilities...")
        
        filter_endpoint = "https://jobright.ai/swan/filter/update/filter-v2"
        jobs_endpoint = "https://jobright.ai/swan/recommend/list/jobs"
        
        # Test various filter combinations
        filter_tests = [
            # Salary filters
            {"salaryMin": 50000, "salaryMax": 150000},
            {"salaryMin": 100000},
            {"salaryMax": 200000},
            
            # Location filters
            {"locations": ["New York", "San Francisco", "Remote"]},
            {"locations": ["Remote"]},
            {"excludeLocations": ["California"]},
            
            # Experience filters
            {"minExperience": 2, "maxExperience": 5},
            {"experienceLevel": ["entry", "mid", "senior"]},
            
            # Job type filters
            {"employmentTypes": ["full-time", "contract", "part-time"]},
            {"workModels": ["remote", "hybrid", "on-site"]},
            
            # Company filters
            {"companySize": ["startup", "mid-size", "enterprise"]},
            {"industries": ["technology", "finance", "healthcare"]},
            
            # Advanced filters
            {"keywords": ["python", "machine learning", "AI"]},
            {"skillsRequired": ["Python", "JavaScript", "React"]},
            {"jobTitles": ["Software Engineer", "Data Scientist", "Product Manager"]},
            {"excludeKeywords": ["unpaid", "internship"]},
            
            # Date filters
            {"postedSince": "7days"},
            {"postedSince": "30days"},
            {"updatedSince": "24hours"},
            
            # Sorting and limit tests
            {"sortBy": "salary", "sortOrder": "desc", "limit": 50},
            {"sortBy": "date", "sortOrder": "desc", "limit": 100},
            {"includeDetails": True, "includeCompanyInfo": True}
        ]
        
        successful_filters = {}
        
        for i, filter_config in enumerate(filter_tests):
            try:
                if not self.test_session:
                    logger.error("❌ No authenticated session available")
                    return {}
                    
                # Apply filter
                filter_payload = {"filters": filter_config}
                
                update_response = self.test_session.post(
                    filter_endpoint,
                    json=filter_payload,
                    timeout=10
                )
                
                if update_response.status_code == 200:
                    time.sleep(1)  # Allow backend processing
                    
                    # Get filtered results
                    jobs_response = self.test_session.get(
                        f"{jobs_endpoint}?refresh=true&sortCondition=1",
                        timeout=10
                    )
                    
                    if jobs_response.status_code == 200:
                        data = jobs_response.json()
                        if data.get('success') and data.get('result'):
                            job_count = len(data.get('result', {}).get('jobList', []))
                            successful_filters[f"filter_test_{i}"] = {
                                'filter_config': filter_config,
                                'job_count': job_count,
                                'filter_success': True,
                                'jobs_success': True
                            }
                            logger.info(f"✅ Filter test {i}: {job_count} jobs with {filter_config}")
                
                time.sleep(1)  # Rate limiting between tests
                
            except Exception as e:
                logger.debug(f"⚠️ Filter test {i}: {e}")
                continue
        
        return successful_filters
    
    def analyze_response_structures(self):
        """Analyze response structures to understand data capabilities"""
        logger.info("🔍 Analyzing API response structures...")
        
        # Get sample responses from different endpoints
        endpoints_to_analyze = [
            "https://jobright.ai/swan/recommend/landing/jobs",
            "https://jobright.ai/swan/recommend/list/jobs?refresh=true&sortCondition=1",
            "https://jobright.ai/swan/auth/newinfo",
            "https://jobright.ai/swan/user-settings/get"
        ]
        
        response_analysis = {}
        
        for endpoint in endpoints_to_analyze:
            try:
                if not self.test_session:
                    logger.error("❌ No authenticated session available")
                    return {}
                    
                response = self.test_session.get(endpoint, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    def analyze_structure(obj, path=""):
                        """Recursively analyze JSON structure"""
                        analysis = {}
                        if isinstance(obj, dict):
                            for key, value in obj.items():
                                current_path = f"{path}.{key}" if path else key
                                if isinstance(value, (dict, list)):
                                    analysis[current_path] = {
                                        'type': type(value).__name__,
                                        'length': len(value) if isinstance(value, list) else None,
                                        'keys': list(value.keys()) if isinstance(value, dict) else None,
                                        'nested': analyze_structure(value, current_path)
                                    }
                                else:
                                    analysis[current_path] = {
                                        'type': type(value).__name__,
                                        'sample_value': str(value)[:100] if value is not None else None
                                    }
                        elif isinstance(obj, list) and obj:
                            analysis[f"{path}[0]"] = analyze_structure(obj[0], f"{path}[0]")
                        
                        return analysis
                    
                    response_analysis[endpoint] = analyze_structure(data)
                    logger.info(f"✅ Analyzed structure: {endpoint}")
                
                time.sleep(0.5)
                
            except Exception as e:
                logger.debug(f"⚠️ Analysis error for {endpoint}: {e}")
                continue
        
        return response_analysis
    
    def generate_discovery_report(self):
        """Generate comprehensive API discovery report"""
        logger.info("📊 Generating API discovery report...")
        
        report = {
            'discovery_timestamp': datetime.now().isoformat(),
            'test_account': self.test_account['email'] if self.test_account else None,
            'findings': {}
        }
        
        # Test parameter discovery
        logger.info("Testing landing/jobs endpoint parameters...")
        landing_params = self.discover_endpoint_parameters(
            "https://jobright.ai/swan/recommend/landing/jobs",
            {"position": 0}
        )
        report['findings']['landing_jobs_parameters'] = landing_params
        
        logger.info("Testing list/jobs endpoint parameters...")
        list_params = self.discover_endpoint_parameters(
            "https://jobright.ai/swan/recommend/list/jobs",
            {"refresh": True, "sortCondition": 1}
        )
        report['findings']['list_jobs_parameters'] = list_params
        
        # Discover new endpoints
        new_endpoints = self.discover_alternative_endpoints()
        report['findings']['discovered_endpoints'] = new_endpoints
        
        # Test advanced filtering
        advanced_filters = self.test_advanced_filtering_capabilities()
        report['findings']['advanced_filtering'] = advanced_filters
        
        # Analyze response structures
        structures = self.analyze_response_structures()
        report['findings']['response_structures'] = structures
        
        return report
    
    def run_full_discovery(self):
        """Run complete API discovery process"""
        logger.info("🚀 Starting comprehensive JobRight API discovery...")
        
        if not self.setup_test_session():
            logger.error("❌ Cannot proceed without authenticated session")
            return None
        
        try:
            report = self.generate_discovery_report()
            
            # Save discovery report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"api_discovery_report_{timestamp}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"✅ API discovery complete! Report saved to: {report_file}")
            
            # Print summary
            self.print_discovery_summary(report)
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Discovery process failed: {e}")
            return None
    
    def print_discovery_summary(self, report):
        """Print summary of key findings"""
        print("\n" + "="*80)
        print("📊 JOBRIGHT API DISCOVERY SUMMARY")
        print("="*80)
        
        findings = report.get('findings', {})
        
        # Parameter discoveries
        landing_params = findings.get('landing_jobs_parameters', {})
        list_params = findings.get('list_jobs_parameters', {})
        
        print(f"\n🔧 PARAMETER DISCOVERIES:")
        print(f"   Landing/jobs endpoint: {len(landing_params)} working parameter combinations")
        print(f"   List/jobs endpoint: {len(list_params)} working parameter combinations")
        
        # Best performing parameters
        if landing_params:
            best_landing = max(landing_params.items(), key=lambda x: x[1].get('job_count', 0))
            print(f"   Best landing param: {best_landing[0]} ({best_landing[1]['job_count']} jobs)")
        
        if list_params:
            best_list = max(list_params.items(), key=lambda x: x[1].get('job_count', 0))
            print(f"   Best list param: {best_list[0]} ({best_list[1]['job_count']} jobs)")
        
        # New endpoints
        new_endpoints = findings.get('discovered_endpoints', {})
        working_endpoints = [ep for ep, data in new_endpoints.items() if data.get('status_code') == 200]
        
        print(f"\n🌐 ENDPOINT DISCOVERIES:")
        print(f"   Found {len(working_endpoints)} new working endpoints")
        for endpoint in working_endpoints[:5]:  # Show first 5
            print(f"   ✅ {endpoint}")
        if len(working_endpoints) > 5:
            print(f"   ... and {len(working_endpoints) - 5} more")
        
        # Advanced filtering
        advanced_filters = findings.get('advanced_filtering', {})
        print(f"\n🎯 FILTERING DISCOVERIES:")
        print(f"   Found {len(advanced_filters)} working filter combinations")
        
        if advanced_filters:
            best_filter = max(advanced_filters.items(), key=lambda x: x[1].get('job_count', 0))
            print(f"   Best filter: {best_filter[1]['job_count']} jobs with {best_filter[1]['filter_config']}")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    discovery = JobRightAPIDiscovery()
    discovery.run_full_discovery()