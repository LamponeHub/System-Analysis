import pandas as pd
import xml.etree.ElementTree as ET

def parse_openvas_report(xml_file):
    """
    Пример функции для парсинга отчета OpenVAS/Greenbone.
    Извлекает только критические и высокие уязвимости.
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    vulnerabilities = []
    
    # Поиск результатов сканирования (структура может варьироваться в зависимости от версии)
    for result in root.findall('.//result'):
        threat = result.find('threat').text
        if threat in ['Critical', 'High']:
            vuln = {
                'name': result.find('name').text,
                'threat': threat,
                'host': result.find('host').text,
                'port': result.find('port').text,
                'description': result.find('description').text[:100] + "..." # Краткое описание
            }
            vulnerabilities.append(vuln)
            
    df = pd.DataFrame(vulnerabilities)
    return df

# Пример использования (для портфолио можно сохранить как .py файл)
# df_vulns = parse_openvas_report('scan_result.xml')
# print(df_vulns.to_markdown())