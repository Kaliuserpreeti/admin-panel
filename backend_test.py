#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Admin Panel
Testing all fixes mentioned in the review request:
1. Deactivate operation (CRITICAL - was broken before)
2. Error handling (HTTPException re-raising)
3. Health check endpoint
4. Full CRUD flow test
5. All database operations
6. IDPass specific test
"""

import requests
import json
import sys
from typing import Dict, Any, List, Optional

# Backend URL from frontend environment
BACKEND_URL = "https://record-keeper-35.preview.emergentagent.com/api"

class AdminPanelTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.failed_tests = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details
        }
        self.test_results.append(result)
        if not success:
            self.failed_tests.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> tuple[bool, Any]:
        """Make HTTP request and return (success, response_data)"""
        try:
            url = f"{self.backend_url}{endpoint}"
            response = requests.request(method, url, timeout=30, **kwargs)
            
            # Try to parse JSON response
            try:
                data = response.json()
            except:
                data = {"text": response.text, "status_code": response.status_code}
            
            return response.status_code < 400, {
                "status_code": response.status_code,
                "data": data
            }
        except Exception as e:
            return False, {"error": str(e)}
    
    def test_health_endpoint(self):
        """Test the new health check endpoint"""
        print("\n=== TESTING HEALTH ENDPOINT ===")
        
        success, response = self.make_request("GET", "/health")
        
        if success:
            data = response.get("data", {})
            if "status" in data and "databases" in data:
                db_status = data.get("databases", {})
                connected_dbs = [db for db, status in db_status.items() if status == "connected"]
                self.log_test("Health Check Endpoint", True, 
                            f"Status: {data.get('status')}, Connected DBs: {len(connected_dbs)}/5")
            else:
                self.log_test("Health Check Endpoint", False, "Invalid response format")
        else:
            self.log_test("Health Check Endpoint", False, f"Request failed: {response}")
    
    def test_error_handling(self):
        """Test proper HTTP error status codes"""
        print("\n=== TESTING ERROR HANDLING ===")
        
        # Test invalid database key - should return 400, not 500
        success, response = self.make_request("GET", "/invalid_db/pending")
        
        expected_status = 400
        actual_status = response.get("status_code", 0)
        
        if actual_status == expected_status:
            self.log_test("Error Handling - Invalid DB Key", True, 
                        f"Correctly returned HTTP {actual_status}")
        else:
            self.log_test("Error Handling - Invalid DB Key", False, 
                        f"Expected HTTP {expected_status}, got {actual_status}")
        
        # Test non-existent record - should return 404
        success, response = self.make_request("POST", "/pmfby/approve/999999")
        
        expected_status = 404
        actual_status = response.get("status_code", 0)
        
        if actual_status == expected_status:
            self.log_test("Error Handling - Non-existent Record", True, 
                        f"Correctly returned HTTP {actual_status}")
        else:
            self.log_test("Error Handling - Non-existent Record", False, 
                        f"Expected HTTP {expected_status}, got {actual_status}")
    
    def get_counts(self) -> Dict[str, Dict[str, int]]:
        """Get current counts for all databases"""
        success, response = self.make_request("GET", "/counts")
        if success:
            return response.get("data", {}).get("data", {})
        return {}
    
    def get_pending_records(self, dbkey: str) -> List[Dict]:
        """Get pending records for a database"""
        success, response = self.make_request("GET", f"/{dbkey}/pending")
        if success:
            return response.get("data", {}).get("data", [])
        return []
    
    def get_approved_records(self, dbkey: str) -> List[Dict]:
        """Get approved records for a database"""
        success, response = self.make_request("GET", f"/{dbkey}/approved")
        if success:
            return response.get("data", {}).get("data", [])
        return []
    
    def test_deactivate_operation(self):
        """Test the CRITICAL deactivate operation that was previously broken"""
        print("\n=== TESTING DEACTIVATE OPERATION (CRITICAL) ===")
        
        # Get initial counts
        initial_counts = self.get_counts()
        pmfby_initial = initial_counts.get("pmfby", {})
        
        print(f"Initial PMFBY counts: {pmfby_initial}")
        
        # Get an approved record to deactivate
        approved_records = self.get_approved_records("pmfby")
        
        if not approved_records:
            self.log_test("Deactivate Operation", False, "No approved records found to test deactivation")
            return
        
        # Use the first approved record
        test_record = approved_records[0]
        test_sr = test_record.get("sr")
        
        print(f"Testing deactivation with SR: {test_sr}")
        
        # Attempt to deactivate
        success, response = self.make_request("POST", f"/pmfby/deactivate/{test_sr}")
        
        if success:
            # Check if counts changed correctly
            new_counts = self.get_counts()
            pmfby_new = new_counts.get("pmfby", {})
            
            pending_increased = pmfby_new.get("pending", 0) > pmfby_initial.get("pending", 0)
            approved_decreased = pmfby_new.get("approved", 0) < pmfby_initial.get("approved", 0)
            
            if pending_increased and approved_decreased:
                self.log_test("Deactivate Operation", True, 
                            f"Successfully moved record from approved to pending. New counts: {pmfby_new}")
            else:
                self.log_test("Deactivate Operation", False, 
                            f"Counts didn't change as expected. Before: {pmfby_initial}, After: {pmfby_new}")
        else:
            error_msg = response.get("data", {}).get("detail", "Unknown error")
            self.log_test("Deactivate Operation", False, f"Deactivation failed: {error_msg}")
    
    def test_full_crud_flow(self):
        """Test complete CRUD flow: Approve -> Deactivate -> Approve -> Reject"""
        print("\n=== TESTING FULL CRUD FLOW ===")
        
        # Get initial state
        initial_counts = self.get_counts()
        pmfby_initial = initial_counts.get("pmfby", {})
        
        # Get a pending record to work with
        pending_records = self.get_pending_records("pmfby")
        
        if not pending_records:
            self.log_test("CRUD Flow Test", False, "No pending records found for CRUD flow test")
            return
        
        test_record = pending_records[0]
        test_sr = test_record.get("sr")
        
        print(f"Testing CRUD flow with SR: {test_sr}")
        
        # Step 1: Approve the pending record
        success, response = self.make_request("POST", f"/pmfby/approve/{test_sr}")
        
        if not success:
            self.log_test("CRUD Flow - Approve Step", False, f"Failed to approve: {response}")
            return
        
        # Verify approval worked
        counts_after_approve = self.get_counts()
        pmfby_after_approve = counts_after_approve.get("pmfby", {})
        
        # Step 2: Deactivate the approved record
        success, response = self.make_request("POST", f"/pmfby/deactivate/{test_sr}")
        
        if not success:
            self.log_test("CRUD Flow - Deactivate Step", False, f"Failed to deactivate: {response}")
            return
        
        # Verify deactivation worked
        counts_after_deactivate = self.get_counts()
        pmfby_after_deactivate = counts_after_deactivate.get("pmfby", {})
        
        # Step 3: Reject the record from pending
        success, response = self.make_request("POST", f"/pmfby/reject/{test_sr}")
        
        if not success:
            self.log_test("CRUD Flow - Reject Step", False, f"Failed to reject: {response}")
            return
        
        # Verify final state
        final_counts = self.get_counts()
        pmfby_final = final_counts.get("pmfby", {})
        
        # Check if the flow worked correctly
        approve_worked = pmfby_after_approve.get("approved", 0) > pmfby_initial.get("approved", 0)
        deactivate_worked = pmfby_after_deactivate.get("pending", 0) > pmfby_after_approve.get("pending", 0)
        reject_worked = pmfby_final.get("pending", 0) < pmfby_after_deactivate.get("pending", 0)
        
        if approve_worked and deactivate_worked and reject_worked:
            self.log_test("Full CRUD Flow", True, 
                        f"Complete flow successful. Final counts: {pmfby_final}")
        else:
            self.log_test("Full CRUD Flow", False, 
                        f"Flow incomplete. Initial: {pmfby_initial}, Final: {pmfby_final}")
    
    def test_all_database_operations(self):
        """Test basic operations on all 5 databases"""
        print("\n=== TESTING ALL DATABASE OPERATIONS ===")
        
        databases = ["neondb", "pmfby", "krp", "byajanudan", "idpass"]
        
        for dbkey in databases:
            print(f"\nTesting database: {dbkey}")
            
            # Test pending endpoint
            success, response = self.make_request("GET", f"/{dbkey}/pending")
            if success:
                pending_count = len(response.get("data", {}).get("data", []))
                self.log_test(f"{dbkey} - Pending Endpoint", True, f"Found {pending_count} pending records")
            else:
                self.log_test(f"{dbkey} - Pending Endpoint", False, f"Failed: {response}")
            
            # Test approved endpoint
            success, response = self.make_request("GET", f"/{dbkey}/approved")
            if success:
                approved_count = len(response.get("data", {}).get("data", []))
                self.log_test(f"{dbkey} - Approved Endpoint", True, f"Found {approved_count} approved records")
            else:
                self.log_test(f"{dbkey} - Approved Endpoint", False, f"Failed: {response}")
        
        # Test neondb inactive endpoint (DB1 only)
        success, response = self.make_request("GET", "/neondb/inactive")
        if success:
            inactive_count = len(response.get("data", {}).get("data", []))
            self.log_test("neondb - Inactive Endpoint", True, f"Found {inactive_count} inactive records")
        else:
            self.log_test("neondb - Inactive Endpoint", False, f"Failed: {response}")
    
    def test_idpass_specific(self):
        """Test IDPass database specific functionality (user_name field)"""
        print("\n=== TESTING IDPASS SPECIFIC FUNCTIONALITY ===")
        
        # Get IDPass records to verify user_name field handling
        success, response = self.make_request("GET", "/idpass/approved")
        
        if success:
            records = response.get("data", {}).get("data", [])
            if records:
                # Check if records have user_name field (not user_id)
                sample_record = records[0]
                has_user_name = "user_name" in sample_record
                has_user_id = "user_id" in sample_record
                
                if has_user_name:
                    self.log_test("IDPass - user_name Field", True, 
                                f"Correctly uses user_name field. Sample: {sample_record.get('user_name')}")
                else:
                    self.log_test("IDPass - user_name Field", False, 
                                f"Missing user_name field. Available fields: {list(sample_record.keys())}")
            else:
                self.log_test("IDPass - user_name Field", True, "No records to test, but endpoint works")
        else:
            self.log_test("IDPass - user_name Field", False, f"Failed to get IDPass records: {response}")
    
    def test_counts_api(self):
        """Test the counts API"""
        print("\n=== TESTING COUNTS API ===")
        
        success, response = self.make_request("GET", "/counts")
        
        if success:
            data = response.get("data", {}).get("data", {})
            if isinstance(data, dict) and len(data) == 5:
                total_pending = sum(db.get("pending", 0) for db in data.values())
                total_approved = sum(db.get("approved", 0) for db in data.values())
                
                self.log_test("Counts API", True, 
                            f"All 5 databases present. Total pending: {total_pending}, approved: {total_approved}")
                
                # Print detailed counts
                for dbkey, counts in data.items():
                    print(f"   {dbkey}: {counts}")
            else:
                self.log_test("Counts API", False, f"Invalid counts data: {data}")
        else:
            self.log_test("Counts API", False, f"Failed: {response}")
    
    def run_all_tests(self):
        """Run all tests in the specified priority order"""
        print("🚀 Starting Comprehensive Admin Panel Backend API Testing")
        print(f"Backend URL: {self.backend_url}")
        print("=" * 80)
        
        # Test in priority order as specified in review request
        self.test_health_endpoint()
        self.test_error_handling()
        self.test_deactivate_operation()  # CRITICAL
        self.test_full_crud_flow()
        self.test_all_database_operations()
        self.test_idpass_specific()
        self.test_counts_api()
        
        # Summary
        print("\n" + "=" * 80)
        print("🏁 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = total_tests - len(self.failed_tests)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        else:
            print("\n🎉 ALL TESTS PASSED!")
        
        return len(self.failed_tests) == 0

if __name__ == "__main__":
    tester = AdminPanelTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)