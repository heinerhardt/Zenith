#!/usr/bin/env python3
"""
Test script to run on the Langfuse server to diagnose 404 issues
This script should be run on the machine hosting the Langfuse server
"""

import requests
import json
import sys
from datetime import datetime

def test_langfuse_server():
    """Test Langfuse server endpoints"""
    
    # Configuration - update these with your actual values
    HOST = "http://localhost:3000"  # Change to your server's local address
    PUBLIC_KEY = "pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120"
    SECRET_KEY = "sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda"
    
    print("🔍 Langfuse Server Test")
    print("=" * 50)
    print(f"Testing server at: {HOST}")
    print(f"Public Key: {PUBLIC_KEY[:20]}...")
    print(f"Secret Key: {SECRET_KEY[:20]}...")
    
    # Test 1: Check if server is running
    print("\n1️⃣ Testing server health...")
    try:
        response = requests.get(f"{HOST}/api/health", timeout=10)
        print(f"   Health check: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Server is running")
        else:
            print(f"   ❌ Server responded with {response.status_code}")
            print(f"   Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Server connection failed: {e}")
        return False
    
    # Test 2: Check main page
    print("\n2️⃣ Testing main page...")
    try:
        response = requests.get(HOST, timeout=10)
        print(f"   Main page: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Main page accessible")
        else:
            print(f"   ❌ Main page error: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Main page failed: {e}")
    
    # Test 3: Check API endpoints
    print("\n3️⃣ Testing API endpoints...")
    endpoints_to_test = [
        "/api/public/ingestion",
        "/api/public/ingestion/spans",  
        "/api/public/traces",
        "/api/public/generations",
        "/api/public/events"
    ]
    
    for endpoint in endpoints_to_test:
        url = f"{HOST}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            status = "✅" if response.status_code != 404 else "❌"
            print(f"   {status} {endpoint}: {response.status_code}")
            if response.status_code == 404:
                print(f"      Response: {response.text[:100]}...")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ {endpoint}: Connection error - {e}")
    
    # Test 4: Test actual ingestion endpoint (the one causing 404)
    print("\n4️⃣ Testing ingestion with auth...")
    ingestion_url = f"{HOST}/api/public/ingestion"
    
    # Create a minimal span batch payload
    test_data = {
        "batch": [
            {
                "id": "test-span-123",
                "type": "span",
                "body": {
                    "id": "test-span-123",
                    "name": "test-span",
                    "startTime": datetime.utcnow().isoformat() + "Z",
                    "endTime": datetime.utcnow().isoformat() + "Z",
                    "input": {"test": "data"},
                    "output": {"result": "test"}
                }
            }
        ]
    }
    
    headers = {
        "Authorization": f"Basic {PUBLIC_KEY}:{SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"   POST to: {ingestion_url}")
        print(f"   Headers: {headers}")
        print(f"   Data: {json.dumps(test_data, indent=2)}")
        
        response = requests.post(
            ingestion_url, 
            json=test_data,
            headers=headers,
            timeout=10
        )
        
        print(f"   Response status: {response.status_code}")
        print(f"   Response headers: {dict(response.headers)}")
        print(f"   Response body: {response.text}")
        
        if response.status_code == 404:
            print("   ❌ 404 ERROR - This is the problem!")
            print("   🔍 Check if Langfuse is configured correctly")
            print("   🔍 Check if the ingestion endpoint is enabled")
            print("   🔍 Check Langfuse logs for more details")
        elif response.status_code == 401:
            print("   ❌ Authentication failed - check your keys")
        elif response.status_code == 200:
            print("   ✅ Ingestion successful!")
        else:
            print(f"   ❓ Unexpected status: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Ingestion test failed: {e}")
    
    # Test 5: Check Langfuse version and configuration
    print("\n5️⃣ Checking Langfuse version...")
    try:
        # Try to get version info
        version_endpoints = [
            "/api/version",
            "/api/public/version", 
            "/.well-known/version"
        ]
        
        for endpoint in version_endpoints:
            try:
                response = requests.get(f"{HOST}{endpoint}", timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ Version from {endpoint}: {response.text}")
                    break
            except:
                continue
        else:
            print("   ❓ Could not determine Langfuse version")
            
    except Exception as e:
        print(f"   ❌ Version check failed: {e}")
    
    # Test 6: Docker/Service status check
    print("\n6️⃣ Checking service status...")
    try:
        import subprocess
        
        # Check if Langfuse is running in Docker
        docker_check = subprocess.run(
            ["docker", "ps", "--filter", "name=langfuse", "--format", "table {{.Names}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=10
        )
        
        if docker_check.returncode == 0 and docker_check.stdout.strip():
            print("   Docker containers:")
            print(docker_check.stdout)
        else:
            print("   No Langfuse Docker containers found")
            
        # Check system processes
        ps_check = subprocess.run(
            ["ps", "aux"], capture_output=True, text=True, timeout=10
        )
        
        if ps_check.returncode == 0:
            langfuse_processes = [line for line in ps_check.stdout.split('\n') if 'langfuse' in line.lower()]
            if langfuse_processes:
                print("   Langfuse processes:")
                for proc in langfuse_processes:
                    print(f"   {proc}")
            else:
                print("   No Langfuse processes found")
                
    except Exception as e:
        print(f"   ❓ Service check failed: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Test Complete")
    print("If you see 404 errors, check:")
    print("1. Langfuse server configuration")
    print("2. Database connection")
    print("3. Ingestion endpoint is enabled") 
    print("4. Langfuse version compatibility")
    print("5. Server logs for detailed errors")

if __name__ == "__main__":
    test_langfuse_server()