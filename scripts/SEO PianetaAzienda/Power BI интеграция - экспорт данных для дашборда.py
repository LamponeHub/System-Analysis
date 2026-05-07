import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import requests

class PowerBIDataExporter:
    def __init__(self):
        self.data = {}
    
    def prepare_seo_metrics(self, audit_results, positions_data, traffic_data=None):
        """Подготовка данных SEO-метрик для Power BI"""
        
        metrics = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_pages': len(audit_results.get('pages', [])),
            'pages_with_errors': len(audit_results.get('errors', [])),
            'meta_issues_count': len(audit_results.get('meta_issues', [])),
            'avg_response_time': np.mean([p.get('response_time', 0) for p in audit_results.get('pages', []) if p.get('response_time')]),
            'avg_position': np.mean([p.get('position', 0) for p in positions_data if p.get('position')]) if positions_data else 0,
            'keywords_in_top3': len([p for p in positions_data if p.get('position') and p['position'] <= 3]),
            'keywords_in_top10': len([p for p in positions_data if p.get('position') and p['position'] <= 10]),
        }
        
        if traffic_data:
            metrics.update({
                'organic_traffic': traffic_data.get('organic_sessions', 0),
                'organic_conversion_rate': traffic_data.get('conversion_rate', 0),
                'bounce_rate': traffic_data.get('bounce_rate', 0)
            })
        
        return metrics
    
    def create_time_series_data(self, days=90):
        """Создание временных рядов для графиков"""
        dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') 
                 for i in range(days)]
        dates.reverse()
        
        # Пример данных (в реальности загружать из Яндекс.Метрики/GA)
        data = {
            'date': dates,
            'organic_sessions': np.random.randint(100, 500, days),
            'organic_users': np.random.randint(80, 400, days),
            'avg_session_duration': np.random.uniform(120, 300, days),
            'bounce_rate': np.random.uniform(30, 60, days),
            'conversions': np.random.randint(5, 30, days),
            'indexed_pages': np.random.randint(50, 150, days)
        }
        
        return pd.DataFrame(data)
    
    def create_keyword_performance_table(self, positions_data):
        """Таблица эффективности ключевых слов"""
        df = pd.DataFrame(positions_data)
        
        if not df.empty:
            df['position_group'] = pd.cut(
                df['position'],
                bins=[0, 3, 10, 30, 100, float('inf')],
                labels=['Top 3', 'Top 10', 'Top 30', 'Top 100', 'Outside 100']
            )
        
        return df
    
    def create_page_performance_table(self, audit_results):
        """Таблица производительности страниц"""
        pages_data = []
        
        for page in audit_results.get('pages', []):
            pages_data.append({
                'url': page.get('url'),
                'status_code': page.get('status_code'),
                'response_time': page.get('response_time'),
                'has_title': bool(page.get('title')),
                'has_description': bool(page.get('description')),
                'has_h1': bool(page.get('h1')),
                'issues_count': len(page.get('issues', []))
            })
        
        return pd.DataFrame(pages_data)
    
    def export_to_json(self, data, filename):
        """Экспорт в JSON для Power BI"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        print(f"Data exported to {filename}")
    
    def export_to_csv(self, df, filename):
        """Экспорт в CSV"""
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"Data exported to {filename}")
    
    def create_powerbi_dataset(self, audit_results, positions_data, traffic_data=None):
        """Создание полного набора данных для Power BI"""
        
        dataset = {
            'summary_metrics': self.prepare_seo_metrics(audit_results, positions_data, traffic_data),
            'time_series': self.create_time_series_data().to_dict('records'),
            'keyword_performance': self.create_keyword_performance_table(positions_data).to_dict('records') if positions_data else [],
            'page_performance': self.create_page_performance_table(audit_results).to_dict('records'),
            'generated_at': datetime.now().isoformat()
        }
        
        return dataset
    
    def push_to_powerbi_api(self, dataset, workspace_id, dataset_id, api_key):
        """Отправка данных в Power BI через API"""
        
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/rows"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        try:
            response = requests.post(url, headers=headers, json=dataset)
            response.raise_for_status()
            print("Data pushed to Power BI successfully")
        except Exception as e:
            print(f"Error pushing to Power BI: {e}")

# Использование
if __name__ == "__main__":
    exporter = PowerBIDataExporter()
    
    # Пример данных (в реальности загрузить из других скриптов)
    audit_results = {
        'pages': [
            {'url': 'https://example.ru/page1', 'status_code': 200, 'response_time': 1.2},
            {'url': 'https://example.ru/page2', 'status_code': 200, 'response_time': 0.8}
        ],
        'errors': [],
        'meta_issues': []
    }
    
    positions_data = [
        {'keyword': 'бизнес консалтинг', 'position': 5},
        {'keyword': 'консалтинг москва', 'position': 12}
    ]
    
    # Создание датасета
    dataset = exporter.create_powerbi_dataset(audit_results, positions_data)
    
    # Экспорт
    exporter.export_to_json(dataset, 'powerbi_seo_data.json')
    exporter.export_to_csv(
        exporter.create_keyword_performance_table(positions_data),
        'keyword_performance.csv'
    )