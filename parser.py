import requests
import time
import random
import urllib3
from bs4 import BeautifulSoup
from config import HEADERS

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def build_url(query: str, city: str, min_price=None, max_price=None):

    base_domain = "www.doski.ru"
    protocol = "https://"
    
    base_url = protocol + base_domain
    search_path = "/search.php"
    
    full_base_path = base_url + search_path
    
    query_encoded = query.replace(" ", "+")
    city_encoded = city.replace(" ", "+")
    
    final_url = full_base_path + "?q=" + query_encoded + "&c=" + city_encoded
    
    if min_price is not None:
        
        price_from_param = f"&price_from={min_price}"
        final_url = final_url + price_from_param
        
    if max_price is not None:
        
        price_to_param = f"&price_to={max_price}"
        final_url = final_url + price_to_param
        
    return final_url

def parse_doski(query: str, city: str, min_price=None, max_price=None):

    current_task_info = f"Запуск парсера для объекта: {query}"
    print(current_task_info)
    
    target_url = build_url(query, city, min_price, max_price)
    
    print(f"Сформированный адрес: {target_url}")
    
    try:
        
        session_timeout = 15
        
        response = requests.get(
            target_url, 
            headers=HEADERS, 
            timeout=session_timeout, 
            verify=False
        )
        
        wait_time = random.uniform(1.2, 3.5)
        time.sleep(wait_time)
        
    except Exception as error_context:
        
        error_message = f"Произошла критическая ошибка при запросе: {error_context}"
        print(error_message)
        
        return []

    status_code = response.status_code
    
    if status_code != 200:
        
        print(f"Сервер вернул статус: {status_code}. Прекращение операции.")
        return []

    html_content = response.text
    
    parser_engine = "lxml"
    
    soup = BeautifulSoup(html_content, parser_engine)
    
    extracted_links_list = []
    
    all_anchor_tags = soup.find_all("a", href=True)
    
    total_found_tags = len(all_anchor_tags)
    print(f"Всего тегов найдено: {total_found_tags}")

    for tag in all_anchor_tags:
        
        raw_href = tag.get("href")
        
        is_message_link = "/msg/" in raw_href
        
        if is_message_link:
            
            domain_prefix = "https://www.doski.ru"
            
            absolute_url = domain_prefix + raw_href
            
            if absolute_url not in extracted_links_list:
                
                extracted_links_list.append(absolute_url)
                
                current_count = len(extracted_links_list)
                print(f"Найдено подходящее объявление №{current_count}")

        limit_reached = len(extracted_links_list) >= 10
        
        if limit_reached:
            
            print("Лимит в 10 ссылок достигнут. Выходим из цикла.")
            break

    print("Процесс парсинга успешно завершен.")
    
    return extracted_links_list

if __name__ == "__main__":
    
    search_query = "iphone"
    search_city = "Москва"
    
    final_results = parse_doski(search_query, search_city)
    
    print("\n--- Итоговый список ссылок ---")
    
    for item in final_results:
        print(item)
        
    print("------------------------------")
