import deepl
import requests
import json
import time
from pathlib import Path

class MultilingualContentManager:
    def __init__(self, deepl_api_key, yandex_api_key=None):
        self.deepl_translator = deepl.Translator(deepl_api_key)
        self.yandex_api_key = yandex_api_key
        self.glossary = {}
    
    def load_glossary(self, glossary_file='corporate_glossary.json'):
        """Загрузка корпоративного глоссария"""
        if Path(glossary_file).exists():
            with open(glossary_file, 'r', encoding='utf-8') as f:
                self.glossary = json.load(f)
            print(f"Loaded glossary with {len(self.glossary)} terms")
    
    def save_glossary(self, glossary_file='corporate_glossary.json'):
        """Сохранение глоссария"""
        with open(glossary_file, 'w', encoding='utf-8') as f:
            json.dump(self.glossary, f, ensure_ascii=False, indent=2)
    
    def add_to_glossary(self, term_ru, term_it, term_en):
        """Добавление термина в глоссарий"""
        self.glossary[term_ru] = {
            'italian': term_it,
            'english': term_en
        }
        self.save_glossary()
    
    def translate_with_glossary(self, text, source_lang='RU', target_lang='IT'):
        """Перевод с учетом глоссария"""
        # Замена терминов из глоссария на плейсхолдеры
        placeholders = {}
        modified_text = text
        
        for i, (ru_term, translations) in enumerate(self.glossary.items()):
            if ru_term in modified_text:
                placeholder = f"__TERM_{i}__"
                modified_text = modified_text.replace(ru_term, placeholder)
                
                if target_lang.upper() == 'IT':
                    placeholders[placeholder] = translations['italian']
                elif target_lang.upper() == 'EN':
                    placeholders[placeholder] = translations['english']
        
        # Перевод через DeepL
        try:
            result = self.deepl_translator.translate_text(
                modified_text,
                source_lang=source_lang,
                target_lang=target_lang
            )
            
            translated_text = result.text
            
            # Замена плейсхолдеров обратно на термины
            for placeholder, term in placeholders.items():
                translated_text = translated_text.replace(placeholder, term)
            
            return translated_text
            
        except Exception as e:
            print(f"DeepL translation error: {e}")
            return None
    
    def yandex_translate(self, text, source_lang='ru', target_lang='it'):
        """Перевод через Yandex Translate API"""
        if not self.yandex_api_key:
            return None
        
        url = "https://translate.api.cloud.yandex.net/translate/v2/translate"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {self.yandex_api_key}"
        }
        
        body = {
            "texts": [text],
            "targetLanguageCode": target_lang,
            "sourceLanguageCode": source_lang,
            "format": "PLAIN_TEXT"
        }
        
        try:
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            
            result = response.json()
            return result['translations'][0]['text']
            
        except Exception as e:
            print(f"Yandex translation error: {e}")
            return None
    
    def translate_content_batch(self, content_list, source_lang='RU', target_languages=['IT', 'EN']):
        """Пакетный перевод контента"""
        results = {
            'original': content_list,
            'translations': {}
        }
        
        for target_lang in target_languages:
            print(f"Translating to {target_lang}...")
            translations = []
            
            for i, content in enumerate(content_list):
                print(f"  Processing {i+1}/{len(content_list)}")
                
                # Пробуем DeepL
                translated = self.translate_with_glossary(content, source_lang, target_lang)
                
                # Если DeepL не сработал, пробуем Yandex
                if not translated and self.yandex_api_key:
                    source_code = 'ru' if source_lang == 'RU' else source_lang.lower()
                    target_code = target_lang.lower()
                    translated = self.yandex_translate(content, source_code, target_code)
                
                translations.append(translated if translated else content)
                time.sleep(0.5)  # Rate limiting
            
            results['translations'][target_lang] = translations
        
        return results
    
    def translate_web_page(self, url, source_lang='RU', target_languages=['IT', 'EN']):
        """Перевод веб-страницы"""
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Извлечение основного контента
            content_elements = {
                'title': soup.find('title').text if soup.find('title') else '',
                'meta_description': '',
                'h1': '',
                'content': []
            }
            
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                content_elements['meta_description'] = meta_desc.get('content', '')
            
            h1 = soup.find('h1')
            if h1:
                content_elements['h1'] = h1.text
            
            # Извлечение параграфов
            paragraphs = soup.find_all('p')
            content_elements['content'] = [p.text for p in paragraphs[:20]]  # Первые 20 параграфов
        
            # Перевод
            all_content = (
                [content_elements['title'], 
                 content_elements['meta_description'], 
                 content_elements['h1']] + 
                content_elements['content']
            )
            
            translations = self.translate_content_batch(
                all_content, 
                source_lang, 
                target_languages
            )
            
            return {
                'url': url,
                'original': content_elements,
                'translations': translations
            }
            
        except Exception as e:
            print(f"Error translating page {url}: {e}")
            return None
    
    def export_translations(self, translations, output_format='json'):
        """Экспорт переводов"""
        if output_format == 'json':
            with open('translations.json', 'w', encoding='utf-8') as f:
                json.dump(translations, f, ensure_ascii=False, indent=2)
        
        elif output_format == 'csv':
            import pandas as pd
            
            df_data = {
                'original': translations['original']
            }
            
            for lang, texts in translations['translations'].items():
                df_data[f'translation_{lang}'] = texts
            
            df = pd.DataFrame(df_data)
            df.to_csv('translations.csv', index=False, encoding='utf-8-sig')
        
        print("Translations exported successfully")

# Использование
if __name__ == "__main__":
    # Инициализация
    manager = MultilingualContentManager(
        deepl_api_key="your-deepl-api-key",
        yandex_api_key="your-yandex-api-key"
    )
    
    # Загрузка глоссария
    manager.load_glossary()
    
    # Добавление новых терминов
    manager.add_to_glossary(
        term_ru="бизнес-консалтинг",
        term_it="consulenza aziendale",
        term_en="business consulting"
    )
    
    # Перевод контента
    content = [
        "Мы предоставляем услуги бизнес-консалтинга для малого и среднего бизнеса",
        "Оптимизация бизнес-процессов",
        "Цифровая трансформация компании"
    ]
    
    translations = manager.translate_content_batch(
        content,
        source_lang='RU',
        target_languages=['IT', 'EN']
    )
    
    # Экспорт
    manager.export_translations(translations, output_format='json')
    manager.export_translations(translations, output_format='csv')