#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Admin Panel
Tests all endpoints for 5 PostgreSQL databases: neondb, pmfby, krp, byajanudan, idpass
"""

import requests
import json
import sys
from typing import Dict, List, Any
import time

# Backend URL from environment
BACKEND_URL = "https://record-keeper-35.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Database keys to test
DB_KEYS = ["neondb", "pmfby", "krp", "byajanudan", "idpass"]

class AdminPanelTester:
    def __init__(self):
        self.results = {
            "health_check": {"status": "pending", "details": {}},
            "counts_api": {"status": "pending", "details": {}},
            "database_operations": {},
            "crud_operations": {},
            "error_handling": {"status": "pending", "details": {}}
        }
        self.test_data = {}  # Store actual data for CRUD operations
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages"""
        print(f"[{level}] {message}")
        
    def test_health_check(self):
        """Test the root health check endpoint"""
        self.log("Testing Health Check Endpoint...")
        try:
            response = requests.get(BACKEND_URL, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "databases" in data:
                    self.results["health_check"]["status"] = "pass"
                    self.results["health_check"]["details"] = {
                        "message": data.get("message"),
                        "databases": data.get("databases"),
                        "database_count": len(data.get("databases", []))
                    }
                    self.log(f"✅ Health check passed: {data['message']}")
                    self.log(f"✅ Found {len(data.get('databases', []))} databases: {data.get('databases')}")
                else:
                    self.results["health_check"]["status"] = "fail"
                    self.results["health_check"]["details"] = {"error": "Missing required fields in response"}
                    self.log("❌ Health check failed: Missing required fields", "ERROR")
            else:
                self.results["health_check"]["status"] = "fail"
                self.results["health_check"]["details"] = {"error": f"HTTP {response.status_code}"}
                self.log(f"❌ Health check failed: HTTP {response.status_code}", "ERROR")
        except Exception as e:
            self.results["health_check"]["status"] = "fail"
            self.results["health_check"]["details"] = {"error": str(e)}
            self.log(f"❌ Health check failed: {str(e)}", "ERROR")
    
    def test_counts_api(self):
        """Test the counts API endpoint"""
        self.log("Testing Counts API...")
        try:
            response = requests.get(f"{API_BASE}/counts", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "data" in data:
                    counts_data = data["data"]
                    self.results["counts_api"]["status"] = "pass"
                    self.results["counts_api"]["details"] = counts_data
                    
                    self.log("✅ Counts API passed")
                    for db_key, counts in counts_data.items():
                        if db_key == "neondb":
                            self.log(f"  {db_key}: pending={counts.get('pending', 0)}, approved={counts.get('approved', 0)}, inactive={counts.get('inactive', 0)}")
                        else:
                            self.log(f"  {db_key}: pending={counts.get('pending', 0)}, approved={counts.get('approved', 0)}")
                else:
                    self.results["counts_api"]["status"] = "fail"
                    self.results["counts_api"]["details"] = {"error": "Invalid response format"}
                    self.log("❌ Counts API failed: Invalid response format", "ERROR")
            else:
                self.results["counts_api"]["status"] = "fail"
                self.results["counts_api"]["details"] = {"error": f"HTTP {response.status_code}"}
                self.log(f"❌ Counts API failed: HTTP {response.status_code}", "ERROR")
        except Exception as e:
            self.results["counts_api"]["status"] = "fail"
            self.results["counts_api"]["details"] = {"error": str(e)}
            self.log(f"❌ Counts API failed: {str(e)}", "ERROR")
    
    def test_database_operations(self):
        """Test database read operations for all databases"""
        self.log("Testing Database Operations...")
        
        for db_key in DB_KEYS:
            self.log(f"Testing {db_key} database operations...")
            self.results["database_operations"][db_key] = {}
            
            # Test pending users
            try:
                response = requests.get(f"{API_BASE}/{db_key}/pending", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        pending_data = data.get("data", [])
                        self.results["database_operations"][db_key]["pending"] = {
                            "status": "pass",
                            "count": len(pending_data),
                            "sample_data": pending_data[:2] if pending_data else []
                        }
                        self.log(f"  ✅ {db_key}/pending: {len(pending_data)} records")
                        
                        # Store some test data for CRUD operations
                        if pending_data and db_key not in self.test_data:
                            self.test_data[db_key] = {"pending_srs": [item.get("sr") for item in pending_data[:3]]}
                    else:
                        self.results["database_operations"][db_key]["pending"] = {
                            "status": "fail",
                            "error": "Success flag false"
                        }
                        self.log(f"  ❌ {db_key}/pending: Success flag false", "ERROR")
                else:
                    self.results["database_operations"][db_key]["pending"] = {
                        "status": "fail",
                        "error": f"HTTP {response.status_code}"
                    }
                    self.log(f"  ❌ {db_key}/pending: HTTP {response.status_code}", "ERROR")
            except Exception as e:
                self.results["database_operations"][db_key]["pending"] = {
                    "status": "fail",
                    "error": str(e)
                }
                self.log(f"  ❌ {db_key}/pending: {str(e)}", "ERROR")
            
            # Test approved users
            try:
                response = requests.get(f"{API_BASE}/{db_key}/approved", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        approved_data = data.get("data", [])
                        self.results["database_operations"][db_key]["approved"] = {
                            "status": "pass",
                            "count": len(approved_data),
                            "sample_data": approved_data[:2] if approved_data else []
                        }
                        self.log(f"  ✅ {db_key}/approved: {len(approved_data)} records")
                        
                        # Store approved SRs for CRUD operations
                        if approved_data:
                            if db_key not in self.test_data:
                                self.test_data[db_key] = {}
                            self.test_data[db_key]["approved_srs"] = [item.get("sr") for item in approved_data[:3]]
                    else:
                        self.results["database_operations"][db_key]["approved"] = {
                            "status": "fail",
                            "error": "Success flag false"
                        }
                        self.log(f"  ❌ {db_key}/approved: Success flag false", "ERROR")
                else:
                    self.results["database_operations"][db_key]["approved"] = {
                        "status": "fail",
                        "error": f"HTTP {response.status_code}"
                    }
                    self.log(f"  ❌ {db_key}/approved: HTTP {response.status_code}", "ERROR")
            except Exception as e:
                self.results["database_operations"][db_key]["approved"] = {
                    "status": "fail",
                    "error": str(e)
                }
                self.log(f"  ❌ {db_key}/approved: {str(e)}", "ERROR")
            
            # Test inactive users (neondb only)
            if db_key == "neondb":
                try:
                    response = requests.get(f"{API_BASE}/neondb/inactive", timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success"):
                            inactive_data = data.get("data", [])
                            self.results["database_operations"][db_key]["inactive"] = {
                                "status": "pass",
                                "count": len(inactive_data),
                                "sample_data": inactive_data[:2] if inactive_data else []
                            }
                            self.log(f"  ✅ {db_key}/inactive: {len(inactive_data)} records")
                            
                            # Store inactive SRs for reactivation testing
                            if inactive_data:
                                if db_key not in self.test_data:
                                    self.test_data[db_key] = {}
                                self.test_data[db_key]["inactive_srs"] = [item.get("sr") for item in inactive_data[:3]]
                        else:
                            self.results["database_operations"][db_key]["inactive"] = {
                                "status": "fail",
                                "error": "Success flag false"
                            }
                            self.log(f"  ❌ {db_key}/inactive: Success flag false", "ERROR")
                    else:
                        self.results["database_operations"][db_key]["inactive"] = {
                            "status": "fail",
                            "error": f"HTTP {response.status_code}"
                        }
                        self.log(f"  ❌ {db_key}/inactive: HTTP {response.status_code}", "ERROR")
                except Exception as e:
                    self.results["database_operations"][db_key]["inactive"] = {
                        "status": "fail",
                        "error": str(e)
                    }
                    self.log(f"  ❌ {db_key}/inactive: {str(e)}", "ERROR")
    
    def test_crud_operations(self):
        """Test CRUD operations with actual data"""
        self.log("Testing CRUD Operations...")
        
        # Test with databases that have data
        test_databases = ["pmfby", "neondb"]  # Focus on these as mentioned in review request
        
        for db_key in test_databases:
            if db_key not in self.test_data:
                self.log(f"  Skipping {db_key} CRUD tests - no test data available")
                continue
                
            self.log(f"Testing {db_key} CRUD operations...")
            self.results["crud_operations"][db_key] = {}
            
            db_test_data = self.test_data[db_key]
            
            # Test Approve operation
            if "pending_srs" in db_test_data and db_test_data["pending_srs"]:
                test_sr = db_test_data["pending_srs"][0]
                if test_sr:
                    try:
                        response = requests.post(f"{API_BASE}/{db_key}/approve/{test_sr}", timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("success"):
                                self.results["crud_operations"][db_key]["approve"] = {
                                    "status": "pass",
                                    "sr_tested": test_sr,
                                    "message": data.get("message")
                                }
                                self.log(f"  ✅ {db_key}/approve/{test_sr}: Success")
                            else:
                                self.results["crud_operations"][db_key]["approve"] = {
                                    "status": "fail",
                                    "sr_tested": test_sr,
                                    "error": "Success flag false"
                                }
                                self.log(f"  ❌ {db_key}/approve/{test_sr}: Success flag false", "ERROR")
                        else:
                            self.results["crud_operations"][db_key]["approve"] = {
                                "status": "fail",
                                "sr_tested": test_sr,
                                "error": f"HTTP {response.status_code}"
                            }
                            self.log(f"  ❌ {db_key}/approve/{test_sr}: HTTP {response.status_code}", "ERROR")
                    except Exception as e:
                        self.results["crud_operations"][db_key]["approve"] = {
                            "status": "fail",
                            "sr_tested": test_sr,
                            "error": str(e)
                        }
                        self.log(f"  ❌ {db_key}/approve/{test_sr}: {str(e)}", "ERROR")
            
            # Test Reject operation
            if "pending_srs" in db_test_data and len(db_test_data["pending_srs"]) > 1:
                test_sr = db_test_data["pending_srs"][1]
                if test_sr:
                    try:
                        response = requests.post(f"{API_BASE}/{db_key}/reject/{test_sr}", timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("success"):
                                self.results["crud_operations"][db_key]["reject"] = {
                                    "status": "pass",
                                    "sr_tested": test_sr,
                                    "message": data.get("message")
                                }
                                self.log(f"  ✅ {db_key}/reject/{test_sr}: Success")
                            else:
                                self.results["crud_operations"][db_key]["reject"] = {
                                    "status": "fail",
                                    "sr_tested": test_sr,
                                    "error": "Success flag false"
                                }
                                self.log(f"  ❌ {db_key}/reject/{test_sr}: Success flag false", "ERROR")
                        else:
                            self.results["crud_operations"][db_key]["reject"] = {
                                "status": "fail",
                                "sr_tested": test_sr,
                                "error": f"HTTP {response.status_code}"
                            }
                            self.log(f"  ❌ {db_key}/reject/{test_sr}: HTTP {response.status_code}", "ERROR")
                    except Exception as e:
                        self.results["crud_operations"][db_key]["reject"] = {
                            "status": "fail",
                            "sr_tested": test_sr,
                            "error": str(e)
                        }
                        self.log(f"  ❌ {db_key}/reject/{test_sr}: {str(e)}", "ERROR")
            
            # Test Deactivate operation
            if "approved_srs" in db_test_data and db_test_data["approved_srs"]:
                test_sr = db_test_data["approved_srs"][0]
                if test_sr:
                    try:
                        response = requests.post(f"{API_BASE}/{db_key}/deactivate/{test_sr}", timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("success"):
                                self.results["crud_operations"][db_key]["deactivate"] = {
                                    "status": "pass",
                                    "sr_tested": test_sr,
                                    "message": data.get("message")
                                }
                                self.log(f"  ✅ {db_key}/deactivate/{test_sr}: Success")
                            else:
                                self.results["crud_operations"][db_key]["deactivate"] = {
                                    "status": "fail",
                                    "sr_tested": test_sr,
                                    "error": "Success flag false"
                                }
                                self.log(f"  ❌ {db_key}/deactivate/{test_sr}: Success flag false", "ERROR")
                        else:
                            self.results["crud_operations"][db_key]["deactivate"] = {
                                "status": "fail",
                                "sr_tested": test_sr,
                                "error": f"HTTP {response.status_code}"
                            }
                            self.log(f"  ❌ {db_key}/deactivate/{test_sr}: HTTP {response.status_code}", "ERROR")
                    except Exception as e:
                        self.results["crud_operations"][db_key]["deactivate"] = {
                            "status": "fail",
                            "sr_tested": test_sr,
                            "error": str(e)
                        }
                        self.log(f"  ❌ {db_key}/deactivate/{test_sr}: {str(e)}", "ERROR")
            
            # Test Delete operation
            if "approved_srs" in db_test_data and len(db_test_data["approved_srs"]) > 1:
                test_sr = db_test_data["approved_srs"][1]
                if test_sr:
                    try:
                        response = requests.delete(f"{API_BASE}/{db_key}/delete/{test_sr}", timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("success"):
                                self.results["crud_operations"][db_key]["delete"] = {
                                    "status": "pass",
                                    "sr_tested": test_sr,
                                    "message": data.get("message")
                                }
                                self.log(f"  ✅ {db_key}/delete/{test_sr}: Success")
                            else:
                                self.results["crud_operations"][db_key]["delete"] = {
                                    "status": "fail",
                                    "sr_tested": test_sr,
                                    "error": "Success flag false"
                                }
                                self.log(f"  ❌ {db_key}/delete/{test_sr}: Success flag false", "ERROR")
                        else:
                            self.results["crud_operations"][db_key]["delete"] = {
                                "status": "fail",
                                "sr_tested": test_sr,
                                "error": f"HTTP {response.status_code}"
                            }
                            self.log(f"  ❌ {db_key}/delete/{test_sr}: HTTP {response.status_code}", "ERROR")
                    except Exception as e:
                        self.results["crud_operations"][db_key]["delete"] = {
                            "status": "fail",
                            "sr_tested": test_sr,
                            "error": str(e)
                        }
                        self.log(f"  ❌ {db_key}/delete/{test_sr}: {str(e)}", "ERROR")
            
            # Test Reactivate operation (neondb only)
            if db_key == "neondb" and "inactive_srs" in db_test_data and db_test_data["inactive_srs"]:
                test_sr = db_test_data["inactive_srs"][0]
                if test_sr:
                    try:
                        response = requests.post(f"{API_BASE}/neondb/reactivate/{test_sr}", timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("success"):
                                self.results["crud_operations"][db_key]["reactivate"] = {
                                    "status": "pass",
                                    "sr_tested": test_sr,
                                    "message": data.get("message")
                                }
                                self.log(f"  ✅ {db_key}/reactivate/{test_sr}: Success")
                            else:
                                self.results["crud_operations"][db_key]["reactivate"] = {
                                    "status": "fail",
                                    "sr_tested": test_sr,
                                    "error": "Success flag false"
                                }
                                self.log(f"  ❌ {db_key}/reactivate/{test_sr}: Success flag false", "ERROR")
                        else:
                            self.results["crud_operations"][db_key]["reactivate"] = {
                                "status": "fail",
                                "sr_tested": test_sr,
                                "error": f"HTTP {response.status_code}"
                            }
                            self.log(f"  ❌ {db_key}/reactivate/{test_sr}: HTTP {response.status_code}", "ERROR")
                    except Exception as e:
                        self.results["crud_operations"][db_key]["reactivate"] = {
                            "status": "fail",
                            "sr_tested": test_sr,
                            "error": str(e)
                        }
                        self.log(f"  ❌ {db_key}/reactivate/{test_sr}: {str(e)}", "ERROR")
    
    def test_error_handling(self):
        """Test error handling with invalid inputs"""
        self.log("Testing Error Handling...")
        error_tests = {}
        
        # Test invalid database key
        try:
            response = requests.get(f"{API_BASE}/invalid_db/pending", timeout=10)
            error_tests["invalid_dbkey"] = {
                "status_code": response.status_code,
                "expected": 400,
                "passed": response.status_code == 400
            }
            self.log(f"  Invalid dbkey test: HTTP {response.status_code} (expected 400)")
        except Exception as e:
            error_tests["invalid_dbkey"] = {
                "status": "error",
                "error": str(e)
            }
            self.log(f"  ❌ Invalid dbkey test failed: {str(e)}", "ERROR")
        
        # Test non-existent SR number
        try:
            response = requests.post(f"{API_BASE}/pmfby/approve/999999", timeout=10)
            error_tests["invalid_sr"] = {
                "status_code": response.status_code,
                "expected": 404,
                "passed": response.status_code == 404
            }
            self.log(f"  Invalid SR test: HTTP {response.status_code} (expected 404)")
        except Exception as e:
            error_tests["invalid_sr"] = {
                "status": "error",
                "error": str(e)
            }
            self.log(f"  ❌ Invalid SR test failed: {str(e)}", "ERROR")
        
        # Check if all error tests passed
        all_passed = all(test.get("passed", False) for test in error_tests.values() if "passed" in test)
        self.results["error_handling"]["status"] = "pass" if all_passed else "fail"
        self.results["error_handling"]["details"] = error_tests
        
        if all_passed:
            self.log("✅ Error handling tests passed")
        else:
            self.log("❌ Some error handling tests failed", "ERROR")
    
    def run_all_tests(self):
        """Run all test suites"""
        self.log("=" * 60)
        self.log("STARTING ADMIN PANEL BACKEND API TESTS")
        self.log("=" * 60)
        
        # Run tests in order
        self.test_health_check()
        self.test_counts_api()
        self.test_database_operations()
        self.test_crud_operations()
        self.test_error_handling()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        self.log("=" * 60)
        self.log("TEST SUMMARY")
        self.log("=" * 60)
        
        # Health Check
        status = self.results["health_check"]["status"]
        self.log(f"Health Check: {'✅ PASS' if status == 'pass' else '❌ FAIL'}")
        
        # Counts API
        status = self.results["counts_api"]["status"]
        self.log(f"Counts API: {'✅ PASS' if status == 'pass' else '❌ FAIL'}")
        
        # Database Operations
        db_results = []
        for db_key, operations in self.results["database_operations"].items():
            db_status = all(op.get("status") == "pass" for op in operations.values())
            db_results.append(db_status)
            self.log(f"Database Operations ({db_key}): {'✅ PASS' if db_status else '❌ FAIL'}")
        
        # CRUD Operations
        crud_results = []
        for db_key, operations in self.results["crud_operations"].items():
            crud_status = all(op.get("status") == "pass" for op in operations.values())
            crud_results.append(crud_status)
            self.log(f"CRUD Operations ({db_key}): {'✅ PASS' if crud_status else '❌ FAIL'}")
        
        # Error Handling
        status = self.results["error_handling"]["status"]
        self.log(f"Error Handling: {'✅ PASS' if status == 'pass' else '❌ FAIL'}")
        
        # Overall Status
        overall_pass = (
            self.results["health_check"]["status"] == "pass" and
            self.results["counts_api"]["status"] == "pass" and
            all(db_results) and
            all(crud_results) and
            self.results["error_handling"]["status"] == "pass"
        )
        
        self.log("=" * 60)
        self.log(f"OVERALL RESULT: {'✅ ALL TESTS PASSED' if overall_pass else '❌ SOME TESTS FAILED'}")
        self.log("=" * 60)
        
        # Save detailed results
        with open("/app/test_results_detailed.json", "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        self.log("Detailed results saved to /app/test_results_detailed.json")

if __name__ == "__main__":
    tester = AdminPanelTester()
    tester.run_all_tests()