import httpx
from typing import Dict, Any, Optional
import json
import asyncio

class WebTools:
    """Tools for web interactions."""
    
    @staticmethod
    async def fetch_url(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> Dict[str, Any]:
        """
        Fetch content from a URL.
        
        Args:
            url: URL to fetch
            headers: Optional request headers
            timeout: Request timeout in seconds
            
        Returns:
            Response data
        """
        # Security checks (basic URL validation)
        if not url.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        
        # Set default headers if not provided
        if headers is None:
            headers = {
                "User-Agent": "MCP-Tool/1.0"
            }
        
        # Perform request
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=timeout, follow_redirects=True)
            
            # Check response
            response.raise_for_status()
            
            # Parse content type
            content_type = response.headers.get("Content-Type", "")
            
            # Return appropriate data based on content type
            if "application/json" in content_type:
                return {
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "data": response.json(),
                    "headers": dict(response.headers)
                }
            else:
                return {
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "text": response.text,
                    "headers": dict(response.headers)
                }
    
    @staticmethod
    async def post_data(url: str, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> Dict[str, Any]:
        """
        Post data to a URL.
        
        Args:
            url: URL to post to
            data: Data to send
            headers: Optional request headers
            timeout: Request timeout in seconds
            
        Returns:
            Response data
        """
        # Security checks (basic URL validation)
        if not url.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        
        # Set default headers if not provided
        if headers is None:
            headers = {
                "User-Agent": "MCP-Tool/1.0",
                "Content-Type": "application/json"
            }
        
        # Perform request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, 
                json=data, 
                headers=headers, 
                timeout=timeout,
                follow_redirects=True
            )
            
            # Check response
            response.raise_for_status()
            
            # Parse content type
            content_type = response.headers.get("Content-Type", "")
            
            # Return appropriate data based on content type
            if "application/json" in content_type:
                return {
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "data": response.json(),
                    "headers": dict(response.headers)
                }
            else:
                return {
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "text": response.text,
                    "headers": dict(response.headers)
                }
    
    @staticmethod
    async def search_web(query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Perform a web search (simplified implementation).
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            Search results
        """
        # This is a simplified implementation
        # In a real implementation, you would use a search API or web scraping
        example_results = [
            {
                "title": f"Result for {query} - Example 1",
                "url": f"https://example.com/search?q={query}&result=1",
                "snippet": f"This is an example search result for '{query}'. It contains sample information."
            },
            {
                "title": f"Result for {query} - Example 2",
                "url": f"https://example.com/search?q={query}&result=2",
                "snippet": f"Another example search result for '{query}'. More sample information here."
            }
        ]
        
        # Simulate search delay
        await asyncio.sleep(1)
        
        return {
            "query": query,
            "results": example_results[:max_results],
            "total_results": len(example_results)
        }