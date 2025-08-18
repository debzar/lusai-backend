import requests
from bs4 import BeautifulSoup

# Headers para simular un navegador real
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Probando la URL del ejemplo
url = "https://www.corteconstitucional.gov.co/relatoria/buscador-jurisprudencia/texto/1992-01-01/2025-08-17/La%20agente%20oficiosa%20aleg%C3%B3%20que%20se%20desconocieron%20los%20derechos%20fundamentales%20a%20la%20educaci%C3%B3n/0/0"

print(f"Probando URL: {url}")

try:
    session = requests.Session()
    session.headers.update(headers)

    response = session.get(url, timeout=30)
    response.raise_for_status()
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type', 'No especificado')}")
    print(f"Tamaño de contenido: {len(response.content)} bytes")

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Explorando la estructura
    print("\n=== TÍTULOS ===")
    titles = soup.find_all(['h1', 'h2', 'h3', 'h4'])
    for title in titles:
        print(f"{title.name}: {title.get_text(strip=True)}")
    
    print("\n=== TABLAS ===")
    tables = soup.find_all('table')
    print(f"Número de tablas encontradas: {len(tables)}")
    
    for i, table in enumerate(tables):
        print(f"\nTabla {i+1}:")
        print(f"  Clases: {table.get('class', [])}")
        print(f"  ID: {table.get('id', 'Sin ID')}")
        rows = table.find_all('tr')
        print(f"  Filas: {len(rows)}")
        if rows:
            first_row = rows[0]
            cols = first_row.find_all(['td', 'th'])
            print(f"  Columnas en primera fila: {len(cols)}")
            for j, col in enumerate(cols[:3]):  # Solo primeras 3 columnas
                text = col.get_text(strip=True)
                print(f"    Col {j+1}: {text[:100]}...")

    print("\n=== DIVS PRINCIPALES ===")
    main_divs = soup.find_all('div', {'id': True})
    for div in main_divs[:10]:  # Solo primeros 10
        div_id = div.get('id')
        text = div.get_text(strip=True)[:100]
        print(f"ID: {div_id} - Contenido: {text}...")

    print("\n=== SCRIPTS ===")
    scripts = soup.find_all('script')
    print(f"Número de scripts: {len(scripts)}")

    # Buscar contenido que parezca JSON o datos
    print("\n=== BUSCANDO DATOS JSON ===")
    for script in scripts:
        if script.string and ('json' in script.string.lower() or '[{' in script.string):
            print(f"Script con posibles datos: {script.string[:200]}...")

    print("\n=== FORMULARIOS ===")
    forms = soup.find_all('form')
    print(f"Número de formularios: {len(forms)}")
    for form in forms:
        action = form.get('action', 'Sin action')
        method = form.get('method', 'Sin method')
        print(f"  Form - Action: {action}, Method: {method}")

    # Buscar elementos con resultado
    print("\n=== ELEMENTOS CON 'RESULTADO' ===")
    result_elements = soup.find_all(text=lambda x: x and 'resultado' in x.lower())
    for elem in result_elements[:5]:
        print(f"  {elem.strip()[:100]}...")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
