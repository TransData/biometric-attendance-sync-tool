"""
Test script for ZKBio Time API adapter
"""
import datetime
from zkbiotime_adapter import ZKBioTimeAPI

# ZKBio Time configuration
ZKBIOTIME_URL = "http://116.58.33.218:81"
ZKBIOTIME_USERNAME = "admin"
ZKBIOTIME_PASSWORD = "admin@123"

def test_zkbiotime_api():
    print("=" * 60)
    print("Testing ZKBio Time API Connection")
    print("=" * 60)
    
    try:
        # Initialize API connection
        print("\n1. Authenticating with ZKBio Time...")
        api = ZKBioTimeAPI(ZKBIOTIME_URL, ZKBIOTIME_USERNAME, ZKBIOTIME_PASSWORD)
        print("   ✅ Authentication successful")
        
        # Get devices
        print("\n2. Fetching devices...")
        devices = api.get_devices()
        print(f"   ✅ Found {len(devices)} device(s)")
        for device in devices:
            print(f"      - {device['alias']} (SN: {device['sn']}, IP: {device['ip_address']})")
            print(f"        Status: {'Online' if device['state'] == '1' else 'Offline'}")
            print(f"        Users: {device['user_count']}, Transactions: {device['transaction_count']}")
        
        # Get today's transactions
        print("\n3. Fetching today's attendance records...")
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + datetime.timedelta(days=1)
        
        transactions = api.get_all_transactions(today, tomorrow)
        print(f"   ✅ Retrieved {len(transactions)} attendance records for today")
        
        if transactions:
            print("\n4. Sample attendance records:")
            for i, txn in enumerate(transactions[:5], 1):
                log = api.transaction_to_attendance_log(txn)
                if log:
                    print(f"\n   Record {i}:")
                    print(f"      Employee: {log['user_id']} ({log['emp_name']})")
                    print(f"      Time: {log['timestamp']}")
                    print(f"      Punch: {'IN' if log['punch'] == 0 else 'OUT'}")
                    print(f"      Department: {log['department']}")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed! ZKBio Time API is working correctly.")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    test_zkbiotime_api()
