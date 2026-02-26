import requests
from urllib.parse import urlparse

def check_security_headers(url):
    """
    Проверяет наличие важных security headers.
    """
    headers_to_check = [
        'Strict-Transport-Security',
        'Content-Security-Policy',
        'X-Frame-Options',
        'X-Content-Type-Options',
        'X-XSS-Protection'
    ]
    
    try:
        response = requests.get(url, timeout=5)
        found_headers = {}
        
        for header in headers_to_check:
            status = "✅ Present" if header in response.headers else "❌ Missing"
            found_headers[header] = status
            
        return {
            'url': url,
            'status_code': response.status_code,
            'headers_status': found_headers
        }
    except Exception as e:
        return {'url': url, 'error': str(e)}

# Пример использования
# result = check_security_headers('https://example.com')
# print(result)