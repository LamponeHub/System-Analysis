import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import re
import json

class SemanticClusterizer:
    def __init__(self, language='russian'):
        self.language = language
        self.lemmatizer = WordNetLemmatizer()
        
        # Стоп-слова для русского и английского
        self.stopwords_ru = set(['и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 
                                  'как', 'а', 'то', 'все', 'она', 'так', 'его', 'но', 'да', 
                                  'ты', 'к', 'у', 'же', 'вы', 'за', 'бы', 'по', 'только', 
                                  'ее', 'мне', 'было', 'вот', 'от', 'меня', 'еще', 'нет', 
                                  'о', 'из', 'ему', 'теперь', 'когда', 'даже', 'ну', 'вдруг', 
                                  'ли', 'если', 'уже', 'или', 'ни', 'быть', 'был', 'него', 
                                  'до', 'вас', 'нибудь', 'опять', 'уж', 'вам', 'ведь', 'там', 
                                  'потом', 'себя', 'ничего', 'ей', 'может', 'они', 'тут', 
                                  'где', 'есть', 'надо', 'ней', 'для', 'мы', 'тебя', 'их', 
                                  'чем', 'была', 'сам', 'чтоб', 'без', 'будто', 'чего', 'раз', 
                                  'тоже', 'себе', 'под', 'будет', 'ж', 'тогда', 'кто', 'этот', 
                                  'того', 'потому', 'этого', 'какой', 'совсем', 'ним', 'здесь', 
                                  'этом', 'один', 'почти', 'мой', 'тем', 'чтобы', 'нее', 'сейчас', 
                                  'были', 'куда', 'зачем', 'всех', 'никогда', 'можно', 'при', 
                                  'наконец', 'два', 'об', 'другой', 'хоть', 'после', 'над', 
                                  'больше', 'тот', 'через', 'эти', 'нас', 'про', 'всего', 'них', 
                                  'какая', 'много', 'разве', 'три', 'эту', 'моя', 'впрочем', 
                                  'хорошо', 'свою', 'этой', 'перед', 'иногда', 'лучше', 'чуть', 
                                  'том', 'нельзя', 'такой', 'им', 'более', 'всегда', 'конечно', 
                                  'всю', 'между'])
        
        self.stopwords_en = set(stopwords.words('english'))
    
    def preprocess_text(self, text):
        """Предобработка текста"""
        # Приведение к нижнему регистру
        text = text.lower()
        
        # Удаление специальных символов
        text = re.sub(r'[^a-zA-Zа-яА-Я0-9\s]', ' ', text)
        
        # Удаление лишних пробелов
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Токенизация
        words = text.split()
        
        # Удаление стоп-слов и лемматизация
        stopwords_set = self.stopwords_ru if self.language == 'russian' else self.stopwords_en
        
        processed_words = []
        for word in words:
            if word not in stopwords_set and len(word) > 2:
                # Простая лемматизация (для русской можно использовать pymorphy2)
                try:
                    lemma = self.lemmatizer.lemmatize(word)
                    processed_words.append(lemma)
                except:
                    processed_words.append(word)
        
        return ' '.join(processed_words)
    
    def load_keywords(self, file_path):
        """Загрузка ключевых слов из файла"""
        df = pd.read_csv(file_path)
        
        # Предполагаем, что есть колонка 'keyword' или 'query'
        keyword_col = 'keyword' if 'keyword' in df.columns else 'query'
        
        keywords = df[keyword_col].tolist()
        frequencies = df['frequency'].tolist() if 'frequency' in df.columns else [1] * len(keywords)
        
        return keywords, frequencies
    
    def cluster_keywords(self, keywords, n_clusters=20, method='kmeans'):
        """Кластеризация ключевых слов"""
        print("Preprocessing keywords...")
        processed_keywords = [self.preprocess_text(kw) for kw in keywords]
        
        print("Vectorizing...")
        vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(processed_keywords)
        
        print(f"Clustering into {n_clusters} groups...")
        if method == 'kmeans':
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(tfidf_matrix)
        else:
            # Альтернатива: иерархическая кластеризация
            from sklearn.cluster import AgglomerativeClustering
            clustering = AgglomerativeClustering(n_clusters=n_clusters)
            clusters = clustering.fit_predict(tfidf_matrix.toarray())
        
        # Создание датафрейма с результатами
        results = pd.DataFrame({
            'keyword': keywords,
            'cluster': clusters,
            'processed': processed_keywords
        })
        
        # Анализ кластеров
        cluster_analysis = {}
        for cluster_id in range(n_clusters):
            cluster_keywords = results[results['cluster'] == cluster_id]['keyword'].tolist()
            cluster_analysis[cluster_id] = {
                'keywords': cluster_keywords,
                'count': len(cluster_keywords),
                'top_keywords': cluster_keywords[:10]  # Топ-10 в кластере
            }
        
        return results, cluster_analysis
    
    def find_semantic_groups(self, keywords, similarity_threshold=0.7):
        """Поиск семантических групп на основе схожести"""
        print("Finding semantic groups...")
        processed_keywords = [self.preprocess_text(kw) for kw in keywords]
        
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(processed_keywords)
        
        # Вычисление матрицы схожести
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        groups = []
        used = set()
        
        for i in range(len(keywords)):
            if i in used:
                continue
            
            # Находим похожие ключевые слова
            similar_indices = np.where(similarity_matrix[i] >= similarity_threshold)[0]
            
            group = {
                'main_keyword': keywords[i],
                'keywords': [keywords[idx] for idx in similar_indices],
                'count': len(similar_indices)
            }
            
            groups.append(group)
            used.update(similar_indices)
        
        return groups
    
    def export_results(self, results, cluster_analysis, output_file='semantic_clusters.json'):
        """Экспорт результатов"""
        export_data = {
            'clusters': {},
            'statistics': {
                'total_keywords': len(results),
                'total_clusters': len(cluster_analysis),
                'avg_keywords_per_cluster': len(results) / len(cluster_analysis) if cluster_analysis else 0
            }
        }
        
        for cluster_id, data in cluster_analysis.items():
            export_data['clusters'][str(cluster_id)] = {
                'keywords': data['keywords'],
                'count': data['count']
            }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        # Также сохраняем Excel
        results.to_excel('semantic_clusters.xlsx', index=False)
        
        print(f"Results exported to {output_file} and semantic_clusters.xlsx")
    
    def run(self, keywords_file, n_clusters=20):
        """Полный пайплайн кластеризации"""
        keywords, frequencies = self.load_keywords(keywords_file)
        
        print(f"Loaded {len(keywords)} keywords")
        
        # Кластеризация
        results, cluster_analysis = self.cluster_keywords(keywords, n_clusters)
        
        # Поиск семантических групп
        semantic_groups = self.find_semantic_groups(keywords)
        
        # Экспорт
        self.export_results(results, cluster_analysis)
        
        # Вывод статистики
        print("\n=== CLUSTER STATISTICS ===")
        for cluster_id, data in sorted(cluster_analysis.items(), key=lambda x: x[1]['count'], reverse=True)[:10]:
            print(f"\nCluster {cluster_id}: {data['count']} keywords")
            print(f"Top keywords: {', '.join(data['top_keywords'][:5])}")
        
        return results, cluster_analysis, semantic_groups

# Использование
if __name__ == "__main__":
    # Создаем пример файла с ключевыми словами
    example_data = {
        'keyword': [
            'бизнес консалтинг',
            'консалтинг для малого бизнеса',
            'управленческий консалтинг',
            'финансовый консалтинг',
            'оптимизация бизнес процессов',
            'цифровая трансформация',
            'автоматизация бизнеса',
            'it консалтинг',
            'стратегический консалтинг',
            'консалтинговые услуги'
        ],
        'frequency': [100, 80, 60, 50, 90, 70, 85, 55, 45, 95]
    }
    
    pd.DataFrame(example_data).to_csv('keywords_example.csv', index=False)
    
    # Запуск кластеризации
    clusterizer = SemanticClusterizer(language='russian')
    results, clusters, groups = clusterizer.run('keywords_example.csv', n_clusters=5)