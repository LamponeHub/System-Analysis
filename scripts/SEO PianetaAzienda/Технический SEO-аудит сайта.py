import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import concurrent.futures
import json

class TechnicalSEOAudit:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.results = {
            'pages': [],
            'errors': [],
            'meta_issues': [],
            'performance': []
        }
        
    def check_status_code(self, url):
        """Проверка статус-кода страницы"""
        try:
            response = requests.get(url, timeout=10)
            return {
                'url': url,
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'ok': response.status_code == 200
            }
        except Exception as e:
            return {
                'url': url,
                'status_code': None,
                'response_time': None,
                'error': str(e),
                'ok': False
            }
    
    def analyze_meta_tags(self, url, html):
        """Анализ мета-тегов"""
        soup = BeautifulSoup(html, 'html.parser')
        
        meta = {
            'url': url,
            'title': soup.find('title').text.strip() if soup.find('title') else None,
            'title_length': len(soup.find('title').text) if soup.find('title') else 0,
            'description': soup.find('meta', attrs={'name': 'description'})['content'] 
                          if soup.find('meta', attrs={'name': 'description'}) else None,
            'h1': soup.find('h1').text.strip() if soup.find('h1') else None,
            'h1_count': len(soup.find_all('h1')),
            'hreflang': [],
            'canonical': None
        }
        
        # Проверка hreflang
        for tag in soup.find_all('link', rel='alternate'):
            if tag.get('hreflang'):
                meta['hreflang'].append({
                    'lang': tag.get('hreflang'),
                    'href': tag.get('href')
                })
        
        # Проверка canonical
        canonical = soup.find('link', rel='canonical')
        if canonical:
            meta['canonical'] = canonical.get('href')
        
        # Выявление проблем
        issues = []
        if not meta['title']:
            issues.append('Missing title')
        elif meta['title_length'] < 30 or meta['title_length'] > 60:
            issues.append(f'Title length issue: {meta["title_length"]} chars')
        
        if not meta['description']:
            issues.append('Missing meta description')
        
        if meta['h1_count'] == 0:
            issues.append('Missing H1')
        elif meta['h1_count'] > 1:
            issues.append(f'Multiple H1 tags: {meta["h1_count"]}')
        
        meta['issues'] = issues
        return meta
    
    def check_core_web_vitals(self, url):
        """Базовая проверка производительности"""
        try:
            response = requests.get(url, timeout=10)
            
            # Размер страницы
            page_size = len(response.content) / 1024  # KB
            
            # Время загрузки
            load_time = response.elapsed.total_seconds()
            
            # Проверка сжатия
            is_compressed = response.headers.get('Content-Encoding') in ['gzip', 'br']
            
            return {
                'url': url,
                'page_size_kb': round(page_size, 2),
                'load_time_sec': round(load_time, 2),
                'compressed': is_compressed,
                'status': 'good' if load_time < 2 and page_size < 1000 else 'needs_improvement'
            }
        except Exception as e:
            return {
                'url': url,
                'error': str(e)
            }
    
    def get_all_urls(self, max_pages=100):
        """Сбор всех URL сайта"""
        urls = {self.base_url}
        to_visit = [self.base_url]
        visited = set()
        
        while to_visit and len(urls) < max_pages:
            current_url = to_visit.pop(0)
            if current_url in visited:
                continue
                
            try:
                response = requests.get(current_url, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    
                    # Пропускаем внешние ссылки, якоря, javascript
                    if href.startswith(('http', 'https')):
                        if self.base_url in href:
                            full_url = href.split('#')[0]
                            if full_url not in urls:
                                urls.add(full_url)
                                to_visit.append(full_url)
                    elif href.startswith('/'):
                        full_url = f"{self.base_url}{href.split('#')[0]}"
                        if full_url not in urls:
                            urls.add(full_url)
                            to_visit.append(full_url)
                
                visited.add(current_url)
                time.sleep(0.5)  # Не перегружаем сервер
                
            except Exception as e:
                print(f"Error crawling {current_url}: {e}")
        
        return list(urls)
    
    def run_full_audit(self, output_file='seo_audit_report.xlsx'):
        """Запуск полного аудита"""
        print(f"Starting SEO audit for: {self.base_url}")
        
        # Сбор всех URL
        urls = self.get_all_urls()
        print(f"Found {len(urls)} pages")
        
        # Параллельная проверка статус-кодов
        print("Checking status codes...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            status_results = list(executor.map(self.check_status_code, urls))
        
        # Анализ мета-тегов и производительности
        meta_results = []
        performance_results = []
        
        for result in status_results:
            if result['ok']:
                url = result['url']
                try:
                    response = requests.get(url, timeout=10)
                    
                    # Мета-теги
                    meta = self.analyze_meta_tags(url, response.text)
                    meta_results.append(meta)
                    
                    if meta['issues']:
                        self.results['meta_issues'].append(meta)
                    
                    # Производительность
                    perf = self.check_core_web_vitals(url)
                    performance_results.append(perf)
                    
                except Exception as e:
                    self.results['errors'].append({'url': url, 'error': str(e)})
            
            else:
                self.results['errors'].append(result)
        
        # Сохранение результатов
        self.results['pages'] = status_results
        
        # Excel отчет
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Основные страницы
            df_pages = pd.DataFrame(status_results)
            df_pages.to_excel(writer, sheet_name='All Pages', index=False)
            
            # Проблемы с мета-тегами
            if meta_results:
                df_meta = pd.DataFrame(meta_results)
                df_meta.to_excel(writer, sheet_name='Meta Tags', index=False)
            
            # Производительность
            if performance_results:
                df_perf = pd.DataFrame(performance_results)
                df_perf.to_excel(writer, sheet_name='Performance', index=False)
            
            # Ошибки
            if self.results['errors']:
                df_errors = pd.DataFrame(self.results['errors'])
                df_errors.to_excel(writer, sheet_name='Errors', index=False)
        
        print(f"Audit complete! Report saved to {output_file}")
        return self.results

# Использование
if __name__ == "__main__":
    audit = TechnicalSEOAudit("https://pianetaazienda.ru")
    results = audit.run_full_audit()