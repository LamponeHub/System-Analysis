import openai
import json
import requests
from bs4 import BeautifulSoup
import time

class SEOContentGenerator:
    def __init__(self, api_key, model="gpt-4"):
        self.api_key = api_key
        self.model = model
        openai.api_key = api_key
    
    def analyze_competitors(self, keywords, competitor_urls):
        """Анализ контента конкурентов"""
        competitor_data = []
        
        for url in competitor_urls:
            try:
                response = requests.get(url, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Извлечение основного контента
                content = {
                    'url': url,
                    'title': soup.find('title').text if soup.find('title') else '',
                    'h1': soup.find('h1').text if soup.find('h1') else '',
                    'word_count': len(soup.get_text().split()),
                    'headings': [h.text for h in soup.find_all(['h2', 'h3'])][:10]
                }
                
                competitor_data.append(content)
                
            except Exception as e:
                print(f"Error analyzing {url}: {e}")
        
        return competitor_data
    
    def generate_article_outline(self, keyword, competitor_data, language='ru'):
        """Генерация структуры статьи"""
        
        prompt = f"""
        Создай подробную структуру SEO-статьи на тему: "{keyword}"
        
        Язык: {'Russian' if language == 'ru' else 'English'}
        
        Данные конкурентов:
        {json.dumps(competitor_data, ensure_ascii=False, indent=2)}
        
        Требования:
        1. Заголовок H1 (до 60 символов)
        2. Meta description (150-160 символов)
        3. Структура с H2 и H3 подзаголовками (минимум 5-7 разделов)
        4. Включи разделы: введение, основная часть, практические рекомендации, заключение
        5. Учти LSI-ключи и семантическое ядро
        
        Формат ответа JSON:
        {{
            "h1": "...",
            "meta_description": "...",
            "introduction": "...",
            "sections": [
                {{"h2": "...", "h3": ["...", "..."]}},
                ...
            ],
            "conclusion": "...",
            "lsi_keywords": ["...", "..."]
        }}
        """
        
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert SEO content strategist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        outline = json.loads(response.choices[0].message.content)
        return outline
    
    def generate_section_content(self, keyword, section_data, outline):
        """Генерация контента для раздела"""
        
        prompt = f"""
        Напиши подробный контент для раздела статьи.
        
        Основная тема: {keyword}
        Раздел H2: {section_data['h2']}
        Подразделы H3: {', '.join(section_data.get('h3', []))}
        
        Общая структура статьи:
        {json.dumps(outline, ensure_ascii=False, indent=2)}
        
        Требования:
        1. Объем: 400-600 слов
        2. Используй подзаголовки H3
        3. Добавь маркированные списки где уместно
        4. Включи практические примеры
        5. Оптимизируй для SEO (естественное вхождение ключей)
        6. Пиши понятным, профессиональным языком
        7. Добавь call-to-action в конце раздела
        
        Язык: Russian
        """
        
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a professional SEO copywriter."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    
    def generate_full_article(self, keyword, competitor_urls=None, language='ru'):
        """Генерация полной статьи"""
        
        print(f"Generating article for: {keyword}")
        
        # Анализ конкурентов (если предоставлены URL)
        competitor_data = []
        if competitor_urls:
            print("Analyzing competitors...")
            competitor_data = self.analyze_competitors(keyword, competitor_urls)
        
        # Генерация структуры
        print("Creating outline...")
        outline = self.generate_article_outline(keyword, competitor_data, language)
        
        # Генерация контента по разделам
        print("Writing content...")
        article = {
            'keyword': keyword,
            'outline': outline,
            'sections_content': [],
            'full_text': ""
        }
        
        full_text = f"# {outline['h1']}\n\n"
        full_text += f"{outline['introduction']}\n\n"
        
        for section in outline['sections']:
            section_content = self.generate_section_content(keyword, section, outline)
            article['sections_content'].append({
                'section': section,
                'content': section_content
            })
            
            full_text += f"## {section['h2']}\n\n"
            if section.get('h3'):
                for h3 in section['h3']:
                    full_text += f"### {h3}\n\n"
            full_text += f"{section_content}\n\n"
            
            time.sleep(1)  # Не перегружаем API
        
        full_text += f"## Заключение\n\n{outline['conclusion']}"
        
        article['full_text'] = full_text
        
        return article
    
    def review_and_optimize(self, article, target_keywords):
        """GPT-ревью и оптимизация контента"""
        
        prompt = f"""
        Проведи SEO-аудит и оптимизацию статьи.
        
        Статья:
        {article['full_text'][:3000]}... (сокращено)
        
        Целевые ключевые слова: {', '.join(target_keywords)}
        
        Проверь:
        1. Плотность ключевых слов (должна быть 1-3%)
        2. Наличие ключей в заголовках H1, H2
        3. Длину meta description
        4. Читаемость текста
        5. Наличие LSI-ключей
        6. Структуру и форматирование
        7. Уникальность и ценность контента
        
        Дай рекомендации по улучшению в формате JSON:
        {{
            "seo_score": 0-100,
            "issues": ["...", "..."],
            "recommendations": ["...", "..."],
            "keyword_density": {{"keyword": "percentage"}},
            "readability_score": "good/medium/poor"
        }}
        """
        
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert SEO auditor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=1000
        )
        
        review = json.loads(response.choices[0].message.content)
        return review
    
    def save_article(self, article, filename):
        """Сохранение статьи"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(article['full_text'])
        
        # Сохранение метаданных
        metadata = {
            'keyword': article['keyword'],
            'h1': article['outline']['h1'],
            'meta_description': article['outline']['meta_description'],
            'lsi_keywords': article['outline']['lsi_keywords'],
            'word_count': len(article['full_text'].split())
        }
        
        with open(filename.replace('.md', '_meta.json'), 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"Article saved to {filename}")

# Использование
if __name__ == "__main__":
    # Инициализация
    generator = SEOContentGenerator(api_key="your-openai-api-key", model="gpt-4")
    
    # Генерация статьи
    keyword = "бизнес консалтинг для малого бизнеса"
    competitor_urls = [
        "https://example-competitor1.ru/consulting",
        "https://example-competitor2.ru/services"
    ]
    
    article = generator.generate_full_article(
        keyword=keyword,
        competitor_urls=competitor_urls,
        language='ru'
    )
    
    # Ревью
    target_keywords = ["бизнес консалтинг", "консалтинг для малого бизнеса", "услуги консалтинга"]
    review = generator.review_and_optimize(article, target_keywords)
    
    print(f"SEO Score: {review['seo_score']}/100")
    print(f"Issues: {review['issues']}")
    print(f"Recommendations: {review['recommendations']}")
    
    # Сохранение
    generator.save_article(article, f"article_{keyword.replace(' ', '_')}.md")