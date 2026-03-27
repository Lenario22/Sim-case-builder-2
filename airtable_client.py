"""
Airtable Client Module
Handles all Airtable API interactions with robust error handling, rate limiting,
and data validation. This module ensures secure, resilient communication with Airtable.
"""

import requests
import time
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AirtableErrorType(Enum):
    """Enumeration of Airtable-specific error types."""
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION = "authentication"
    INVALID_REQUEST = "invalid_request"
    NOT_FOUND = "not_found"
    SERVER_ERROR = "server_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


@dataclass
class AirtableResponse:
    """Standard response wrapper for Airtable operations."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error_type: Optional[AirtableErrorType] = None
    error_message: str = ""
    retry_after: Optional[int] = None  # Seconds to wait before retry
    
    def __str__(self) -> str:
        if self.success:
            return f"✓ Success: {len(self.data) if self.data else 0} records"
        return f"✗ Error ({self.error_type.value}): {self.error_message}"


class RateLimiter:
    """
    Simple token bucket rate limiter for Airtable API.
    Airtable allows ~5 requests per second per base.
    """
    
    def __init__(self, max_requests: int = 4, window_seconds: float = 1.0):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_times: List[float] = []
    
    def acquire(self) -> None:
        """
        Wait if necessary to ensure rate limit compliance.
        """
        now = time.time()
        
        # Remove old requests outside the window
        self.request_times = [
            req_time for req_time in self.request_times
            if now - req_time < self.window_seconds
        ]
        
        # If at limit, wait for oldest request to exit window
        if len(self.request_times) >= self.max_requests:
            sleep_time = self.window_seconds - (now - self.request_times[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.request_times.append(time.time())


class AirtableClient:
    """
    Robust Airtable API client with error handling and rate limiting.
    
    Features:
    - Automatic rate limit management
    - Detailed error handling with retry logic
    - Data validation before sending
    - Comprehensive logging
    """
    
    BASE_URL = "https://api.airtable.com/v0"
    DEFAULT_TIMEOUT = 10
    
    def __init__(self, api_key: str, base_id: str):
        """
        Initialize Airtable client.
        
        Args:
            api_key: Airtable API personal access token
            base_id: Base ID to query
            
        Raises:
            ValueError: If api_key or base_id are empty
        """
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty")
        if not base_id or not base_id.strip():
            raise ValueError("Base ID cannot be empty")
        
        self.api_key = api_key.strip()
        self.base_id = base_id.strip()
        self.rate_limiter = RateLimiter()
        
        logger.info(f"Airtable client initialized for base {self.base_id[:8]}...")
    
    def _build_headers(self) -> Dict[str, str]:
        """Build standard request headers with authorization."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "SimCaseBuilder/1.0"
        }
    
    def _classify_error(self, status_code: int, 
                       response_body: Dict[str, Any]) -> Tuple[AirtableErrorType, str]:
        """
        Classify the type of error from Airtable response.
        
        Args:
            status_code: HTTP status code
            response_body: Response JSON body
            
        Returns:
            Tuple of (error_type, human_readable_message)
        """
        error_code = response_body.get("error", {}).get("type", "")
        
        if status_code == 429:
            retry_after = response_body.get("error", {}).get("retryAfter", 30)
            return (
                AirtableErrorType.RATE_LIMIT,
                f"Rate limit exceeded. Retry after {retry_after}s"
            )
        elif status_code == 401 or error_code == "INVALID_CREDENTIALS":
            return (
                AirtableErrorType.AUTHENTICATION,
                "Invalid API key or authentication failed"
            )
        elif status_code == 400 or error_code in ["INVALID_REQUEST", "INVALID_FIELD_MAPPING"]:
            return (
                AirtableErrorType.INVALID_REQUEST,
                response_body.get("error", {}).get("message", "Invalid request format")
            )
        elif status_code == 404 or error_code == "NOT_FOUND":
            return (
                AirtableErrorType.NOT_FOUND,
                "Table or record not found"
            )
        elif status_code >= 500:
            return (
                AirtableErrorType.SERVER_ERROR,
                f"Airtable server error ({status_code})"
            )
        else:
            return (
                AirtableErrorType.UNKNOWN,
                f"Unknown error: {response_body.get('error', {}).get('message', 'No error details')}"
            )
    
    def create_record(self, table_name: str, 
                     fields: Dict[str, Any],
                     max_retries: int = 2) -> AirtableResponse:
        """
        Create a single record in the specified table.
        
        Args:
            table_name: Name of the table
            fields: Dictionary of field names to values
            max_retries: Number of retries on rate limit
            
        Returns:
            AirtableResponse with success status and record data
        """
        if not isinstance(fields, dict):
            return AirtableResponse(
                success=False,
                error_type=AirtableErrorType.INVALID_REQUEST,
                error_message="Fields must be a dictionary"
            )
        
        url = f"{self.BASE_URL}/{self.base_id}/{table_name.replace(' ', '%20')}"
        payload = {"records": [{"fields": fields}]}
        
        return self._make_request(
            "POST",
            url,
            json=payload,
            max_retries=max_retries
        )
    
    def batch_create_records(self, table_name: str,
                            records: List[Dict[str, Any]],
                            batch_size: int = 10) -> AirtableResponse:
        """
        Create multiple records with automatic batching.
        Airtable API allows max 10 records per request.
        
        Args:
            table_name: Name of the table
            records: List of field dictionaries
            batch_size: Records per request (max 10)
            
        Returns:
            AirtableResponse with aggregated results
        """
        if batch_size > 10:
            batch_size = 10
        
        all_created_records = []
        errors = []
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            batch_payload = {"records": [{"fields": record} for record in batch]}
            
            url = f"{self.BASE_URL}/{self.base_id}/{table_name.replace(' ', '%20')}"
            response = self._make_request("POST", url, json=batch_payload, max_retries=2)
            
            if response.success:
                all_created_records.extend(response.data.get("records", []))
            else:
                errors.append(f"Batch {i//batch_size + 1}: {response.error_message}")
        
        if errors:
            return AirtableResponse(
                success=False,
                error_type=AirtableErrorType.INVALID_REQUEST,
                error_message="; ".join(errors),
                data={"created": len(all_created_records), "failed": len(errors)}
            )
        
        return AirtableResponse(
            success=True,
            data={"records": all_created_records}
        )
    
    def get_records(self, table_name: str,
                   filter_formula: Optional[str] = None,
                   max_records: int = 100) -> AirtableResponse:
        """
        Retrieve records from table with optional filtering.
        
        Args:
            table_name: Name of the table
            filter_formula: Optional Airtable filter formula
            max_records: Maximum records to retrieve
            
        Returns:
            AirtableResponse with records data
        """
        url = f"{self.BASE_URL}/{self.base_id}/{table_name.replace(' ', '%20')}"
        params = {"maxRecords": max_records}
        
        if filter_formula:
            params["filterByFormula"] = filter_formula
        
        return self._make_request("GET", url, params=params)
    
    def update_record(self, table_name: str, record_id: str,
                     fields: Dict[str, Any]) -> AirtableResponse:
        """
        Update a single record.
        
        Args:
            table_name: Name of the table
            record_id: Record ID to update
            fields: Dictionary of fields to update
            
        Returns:
            AirtableResponse with updated record
        """
        url = f"{self.BASE_URL}/{self.base_id}/{table_name.replace(' ', '%20')}/{record_id}"
        payload = {"fields": fields}
        
        return self._make_request("PATCH", url, json=payload)
    
    def delete_record(self, table_name: str, record_id: str) -> AirtableResponse:
        """
        Delete a single record.
        
        Args:
            table_name: Name of the table
            record_id: Record ID to delete
            
        Returns:
            AirtableResponse indicating success
        """
        url = f"{self.BASE_URL}/{self.base_id}/{table_name.replace(' ', '%20')}/{record_id}"
        
        return self._make_request("DELETE", url)
    
    def _make_request(self, method: str, url: str,
                     json: Optional[Dict] = None,
                     params: Optional[Dict] = None,
                     max_retries: int = 2) -> AirtableResponse:
        """
        Execute HTTP request with error handling and retry logic.
        
        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            url: Full URL to request
            json: JSON payload for POST/PATCH
            params: Query parameters for GET
            max_retries: Number of retries on rate limit
            
        Returns:
            AirtableResponse with results or error
        """
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # Respect rate limiting
                self.rate_limiter.acquire()
                
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self._build_headers(),
                    json=json,
                    params=params,
                    timeout=self.DEFAULT_TIMEOUT
                )
                
                # Handle successful response
                if response.status_code in [200, 201]:
                    data = response.json()
                    logger.info(f"{method} {url} → {response.status_code}")
                    return AirtableResponse(success=True, data=data)
                
                # Handle 204 No Content (successful deletion)
                elif response.status_code == 204:
                    logger.info(f"{method} {url} → 204 (deleted)")
                    return AirtableResponse(success=True, data={"deleted": True})
                
                # Handle error responses
                else:
                    try:
                        error_body = response.json()
                    except:
                        error_body = {"error": {"message": response.text}}
                    
                    error_type, error_msg = self._classify_error(
                        response.status_code,
                        error_body
                    )
                    
                    # Rate limit: retry with backoff
                    if error_type == AirtableErrorType.RATE_LIMIT and retry_count < max_retries:
                        retry_after = error_body.get("error", {}).get("retryAfter", 30)
                        logger.warning(
                            f"Rate limited. Retrying in {retry_after}s "
                            f"({retry_count + 1}/{max_retries})"
                        )
                        time.sleep(retry_after)
                        retry_count += 1
                        continue
                    
                    logger.error(f"{method} {url} → {response.status_code}: {error_msg}")
                    return AirtableResponse(
                        success=False,
                        error_type=error_type,
                        error_message=error_msg,
                        retry_after=error_body.get("error", {}).get("retryAfter")
                    )
            
            except requests.Timeout:
                logger.error(f"Request timeout to {url}")
                return AirtableResponse(
                    success=False,
                    error_type=AirtableErrorType.NETWORK_ERROR,
                    error_message="Request timed out after 10 seconds"
                )
            
            except requests.ConnectionError as e:
                logger.error(f"Connection error to Airtable: {e}")
                return AirtableResponse(
                    success=False,
                    error_type=AirtableErrorType.NETWORK_ERROR,
                    error_message=f"Connection error: {str(e)}"
                )
            
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return AirtableResponse(
                    success=False,
                    error_type=AirtableErrorType.UNKNOWN,
                    error_message=f"Unexpected error: {str(e)}"
                )
        
        return AirtableResponse(
            success=False,
            error_type=AirtableErrorType.RATE_LIMIT,
            error_message="Max retries exceeded. Try again later."
        )
