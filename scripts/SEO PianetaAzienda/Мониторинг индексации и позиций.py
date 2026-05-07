import requests
from googlesearch import search
import pandas as pd
import time
from datetime import datetime
import json

class SEOMonitor:
    def __init__(self, site_url):
        self.site_url = site_url
        self.results = {
            'indexed_pages': [],
            'positions': {},
            'errors': []
        }
    
    def check_indexed_pages(self, max_results=100):
        """Проверка проиндексированных страниц через site: оператор"""
        query = f"site:{self.site_url}"
        
        try:
            indexed_urls = []
            
            for url in search(query, num_results=max_results, advanced=True):
                indexed_urls.append({
                    'url': url.url,
                    'title': url.title,
                    'description': url.description
                })
                
                time.sleep(2)  # Avoid rate limiting
            
            self.results['indexed_pages'] = indexed_urls
            
            print(f"Found {len(indexed_urls)} indexed pages")
            return indexed_urls
            
        except Exception as e:
            print(f"Error checking indexed pages: {e}")
            return []
    
    def check_keyword_positions(self, keywords, location='ru', num_results=20):
        """Проверка позиций по ключевым словам"""
        positions_data = []
        
        for keyword in keywords:
            print(f"Checking position for: {keyword}")
            
            try:
                found_position = None
                
                for i, url in enumerate(search(keyword, num_results=num_results, lang=location)):
                    if self.site_url in url:
                        found_position = i + 1
                        break
                    
                    time.sleep(2)
                
                position_data = {
                    'keyword': keyword,
                    'position': found_position,
                    'checked_at': datetime.now().isoformat(),
                    'url': self.site_url
                }
                
                positions_data.append(position_data)
                
                if found_position:
                    print(f"  Position: {found_position}")
                else:
                    print(f"  Not found in top {num_results}")
                
            except Exception as e:
                print(f"  Error: {e}")
                self.results['errors'].append({
                    'keyword': keyword,
                    'error': str(e)
                })
            
            time.sleep(5)  # Avoid rate limiting
        
        self.results['positions'] = positions_data
        return positions_data
    
    def check_google_search_console(self, api_key, property_url):
        """Интеграция с Google Search Console API"""
        # Это пример, требует настройки OAuth2
        print("GSC API integration requires OAuth2 setup")
        pass
    
    def check_yandex_webmaster(self, token, site_id):
        """Интеграция с Яндекс.Вебмастер API"""
        url = f"https://api.webmaster.yandex.net/v4/hosts/{site_id}/urls"
        
        headers = {
            "Authorization": f"OAuth {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return data
            
        except Exception as e:
            print(f"Yandex Webmaster API error: {e}")
            return None
    
    def analyze_crawl_budget(self, log_file_path):
        """Анализ логов сервера для проверки crawl budget"""
        import re
        from collections import Counter
        
        googlebot_ips = []
        crawled_urls = Counter()
        status_codes = Counter()
        
        # Паттерны для Googlebot
        googlebot_pattern = re.compile(r'Googlebot', re.IGNORECASE)
        
        try:
            with open(log_file_path, 'r') as f:
                for line in f:
                    if googlebot_pattern.search(line):
                        # Извлечение URL и статус-кода
                        match = re.search(r'"GET\s+([^\s]+)\s+HTTP', line)
                        if match:
                            url = match.group(1)
                            crawled_urls[url] += 1
                        
                        # Статус-код
                        status_match = re.search(r'\s(\d{3})\s', line)
                        if status_match:
                            status_codes[status_match.group(1)] += 1
            
            analysis = {
                'total_crawls': sum(crawled_urls.values()),
                'unique_urls': len(crawled_urls),
                'most_crawled': crawled_urls.most_common(20),
                'status_codes': dict(status_codes),
                'recommendations': []
            }
            
            # Рекомендации
            if analysis['total_crawls'] > 10000:
                analysis['recommendations'].append("High crawl activity - check for duplicate content")
            
            if '404' in status_codes and int(status_codes['404']) > 100:
                analysis['recommendations'].append("Many 404 errors - fix broken links")
            
            if '500' in status_codes:
                analysis['recommendations'].append("Server errors detected - investigate immediately")
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing logs: {e}")
            return None
    
    def generate_monitoring_report(self, output_file='seo_monitoring_report.xlsx'):
        """Генерация отчета"""
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Индексированные страницы
            if self.results['indexed_pages']:
                df_indexed = pd.DataFrame(self.results['indexed_pages'])
                df_indexed.to_excel(writer, sheet_name='Indexed Pages', index=False)
            
            # Позиции
            if self.results['positions']:
                df_positions = pd.DataFrame(self.results['positions'])
                df_positions.to_excel(writer, sheet_name='Positions', index=False)
            
            # Ошибки
            if self.results['errors']:
                df_errors = pd.DataFrame(self.results['errors'])
                df_errors.to_excel(writer, sheet_name='Errors', index=False)
        
        print(f"Report saved to {output_file}")
    
    def setup_automatic_monitoring(self, keywords, check_interval_days=7):
        """Настройка автоматического мониторинга"""
        import schedule
        
        def job():
            print(f"Running scheduled SEO check - {datetime.now()}")
            self.check_keyword_positions(keywords)
            self.generate_monitoring_report()
        
        schedule.every(check_interval_days).days.do(job)
        
        print("Automatic monitoring started")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

# Использование
if __name__ == "__main__":
    monitor = SEOMonitor("https://pianetaazienda.ru")
    
    # Проверка индексации
    monitor.check_indexed_pages(max_results=50)
    
    # Проверка позиций
    keywords = [
        "бизнес консалтинг москва",
        "консалтинг для малого бизнеса",
        "управленческий консалтинг"
    ]
    
    monitor.check_keyword_positions(keywords)
    
    # Генерация отчета
    monitor.generate_monitoring_report()
    
    # Анализ логов (если есть доступ)
    # crawl_analysis = monitor.analyze_crawl_budget('/path/to/access.log')
    # print(crawl_analysis)