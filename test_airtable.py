#!/usr/bin/env python3
"""
Quick test script to verify Airtable connection and permissions.
Run this to debug sync issues.
"""

from dotenv import load_dotenv
import os
import requests

load_dotenv()

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "sim case builder 2")

print(f"🔍 Testing Airtable Connection...")
print(f"   Base ID: {AIRTABLE_BASE_ID}")
print(f"   Table Name: {AIRTABLE_TABLE_NAME}")
print(f"   Token: {AIRTABLE_PAT[:10]}... (hidden)")
print()

# Test 1: List tables in the base
print("📋 Fetching tables in your base...")
url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
headers = {"Authorization": f"Bearer {AIRTABLE_PAT}"}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    tables = response.json().get("tables", [])
    print(f"✅ Found {len(tables)} table(s):")
    for table in tables:
        print(f"   - {table['name']} (ID: {table['id']})")
    
    # Find our table
    our_table = next((t for t in tables if t["name"] == AIRTABLE_TABLE_NAME), None)
    if our_table:
        print(f"\n✅ Found your table: '{AIRTABLE_TABLE_NAME}'")
        table_id = our_table["id"]
        
        # Test 2: Get fields in the table
        print(f"\n📊 Fields in '{AIRTABLE_TABLE_NAME}':")
        for field in our_table.get("fields", []):
            print(f"   - {field['name']} ({field['type']})")
        
        # Test 3: Try to create a test record
        print(f"\n🧪 Attempting to create a test record...")
        create_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table_id.replace(' ', '%20')}"
        test_record = {
            "records": [{
                "fields": {
                    "Case Name": "TEST RECORD",
                    "Diagnosis": "Test",
                    "Age": 50
                }
            }]
        }
        
        create_response = requests.post(create_url, json=test_record, headers=headers)
        
        if create_response.status_code in (200, 201):
            print(f"✅ SUCCESS! Test record created.")
            record_id = create_response.json()["records"][0]["id"]
            print(f"   Record ID: {record_id}")
            
            # Clean up: Delete the test record
            delete_url = f"{create_url}/{record_id}"
            del_response = requests.delete(delete_url, headers=headers)
            if del_response.status_code == 200:
                print(f"✅ Test record deleted.")
        else:
            print(f"❌ FAILED to create record")
            print(f"   Status: {create_response.status_code}")
            print(f"   Error: {create_response.text}")
    else:
        print(f"\n❌ Table '{AIRTABLE_TABLE_NAME}' not found!")
        print(f"   Make sure the table name is EXACTLY correct (case-sensitive)")
else:
    print(f"❌ Failed to fetch tables")
    print(f"   Status: {response.status_code}")
    print(f"   Error: {response.text}")
    print(f"\n   This usually means:")
    print(f"   1. Your token is invalid or expired")
    print(f"   2. Your token doesn't have permission to read the base")
    print(f"   3. Your base ID is wrong")
