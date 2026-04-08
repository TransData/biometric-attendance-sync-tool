"""
ZKBio Time API Adapter for biometric-attendance-sync-tool
Connects to ZKBio Time server instead of directly to biometric devices
"""
import datetime
import requests
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class ZKBioTimeAPI:
    """Adapter to connect to ZKBio Time server API instead of direct device"""
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self._authenticate()
    
    def _authenticate(self):
        """Get authentication token from ZKBio Time"""
        url = f"{self.base_url}/api-token-auth/"
        headers = {"Content-Type": "application/json"}
        data = {"username": self.username, "password": self.password}
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        self.token = result.get('token')
        if not self.token:
            raise Exception("No token received from ZKBio Time API")
        
        logger.info("Successfully authenticated with ZKBio Time API")
    
    def _get_headers(self) -> Dict:
        """Get headers with authentication token"""
        return {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/json"
        }
    
    def get_devices(self) -> List[Dict]:
        """Get list of devices from ZKBio Time"""
        url = f"{self.base_url}/iclock/api/terminals/"
        response = requests.get(url, headers=self._get_headers(), timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if result.get('code') == 0:
            return result.get('data', [])
        raise Exception(f"Failed to get devices: {result.get('msg', 'Unknown error')}")
    
    def get_transactions(self, start_time: datetime.datetime, end_time: datetime.datetime, 
                        page: int = 1, page_size: int = 100) -> Dict:
        """
        Get attendance transactions from ZKBio Time
        
        Args:
            start_time: Start datetime for filtering
            end_time: End datetime for filtering
            page: Page number for pagination
            page_size: Number of records per page
            
        Returns:
            Dict with 'data' (list of transactions), 'count', 'next', 'previous'
        """
        url = f"{self.base_url}/iclock/api/transactions/"
        params = {
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "page": page,
            "page_size": page_size
        }
        
        response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if result.get('code') == 0:
            return result
        raise Exception(f"Failed to get transactions: {result.get('msg', 'Unknown error')}")
    
    def get_all_transactions(self, start_time: datetime.datetime, 
                           end_time: datetime.datetime) -> List[Dict]:
        """
        Get all attendance transactions (handles pagination)
        
        Args:
            start_time: Start datetime for filtering
            end_time: End datetime for filtering
            
        Returns:
            List of all transaction records
        """
        all_transactions = []
        page = 1
        
        while True:
            result = self.get_transactions(start_time, end_time, page=page)
            all_transactions.extend(result.get('data', []))
            
            # Check if there's a next page
            if not result.get('next'):
                break
            
            page += 1
        
        logger.info(f"Retrieved {len(all_transactions)} transactions from ZKBio Time")
        return all_transactions
    
    def transaction_to_attendance_log(self, transaction: Dict) -> Dict:
        """
        Convert ZKBio Time transaction to format compatible with erpnext_sync.py
        
        Args:
            transaction: Transaction dict from ZKBio Time API
            
        Returns:
            Dict in format expected by erpnext_sync.py
        """
        # Map punch_state to punch value
        # ZKBio Time: "0" = Check In, "1" = Check Out
        punch_state = transaction.get('punch_state', '0')
        punch_value = 0 if punch_state == '0' else 1  # 0=IN, 1=OUT
        
        # Parse punch_time
        punch_time_str = transaction.get('punch_time', '')
        try:
            punch_time = datetime.datetime.strptime(punch_time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            logger.error(f"Invalid punch_time format: {punch_time_str}")
            return None
        
        # Get employee code (this is what we'll use as employee_field_value in ERPNext)
        emp_code = transaction.get('emp_code')
        if not emp_code:
            logger.error(f"No emp_code in transaction: {transaction}")
            return None
        
        # Create attendance log in format compatible with erpnext_sync.py
        attendance_log = {
            'uid': transaction.get('id', 0),
            'user_id': str(emp_code),  # ERPNext employee field value
            'timestamp': punch_time,
            'punch': punch_value,  # 0=IN, 1=OUT
            'status': 1,  # Always successful
            'emp_name': transaction.get('first_name', ''),
            'department': transaction.get('department', ''),
            'terminal_sn': transaction.get('terminal_sn', ''),
            'terminal_alias': transaction.get('terminal_alias', ''),
        }
        
        return attendance_log
