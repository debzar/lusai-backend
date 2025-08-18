"""
Extractores de datos para el servicio de scraping.
"""

import logging
import time
import re
from typing import List, Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
from bs4 import BeautifulSoup

from .models import SearchResult, Sentencia
from .config import ScrapingConfig
from .utils import (
    extract_sentencia_number, 
    extract_tema_from_text, 
    extract_subtema_from_text,
    normalize_url,
    generate_sentencia_urls
)

logger = logging.getLogger(__name__)

class SeleniumExtractor:
    """Extractor usando Selenium para contenido dinámico."""
    
    def __init__(self):
        self.driver = None
    
    def extract(self, url: str, palabra: str) -> List[SearchResult]:
        """Extrae datos usando Selenium."""
        try:
            self._setup_driver()
            self.driver.get(url)
            
            # Esperar a que la página cargue completamente
            wait = WebDriverWait(self.driver, ScrapingConfig.SELENIUM_WAIT_TIMEOUT)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(ScrapingConfig.SELENIUM_RENDER_DELAY)
            
            return self._extract_results(palabra)
            
        except Exception as e:
            logger.error(f"Error con Selenium: {e}")
            return []
        finally:
            self._cleanup()
    
    def _setup_driver(self):
        """Configura el driver de Chrome."""
        chrome_options = Options()
        for key, value in ScrapingConfig.get_chrome_options().items():
            chrome_options.add_argument(f"--{key}={value}")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(ScrapingConfig.SELENIUM_PAGE_LOAD_TIMEOUT)
    
    def _extract_results(self, palabra: str) -> List[SearchResult]:
        """Extrae resultados de la página."""
        resultados = []
        
        try:
            # Buscar diferentes patrones de resultados
            selectores = [
                "table tbody tr",
                ".resultado",
                "[data-resultado]",
                ".sentencia",
                ".providencia"
            ]
            
            for selector in selectores:
                try:
                    elementos = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elementos:
                        logger.info(f"Encontrados {len(elementos)} elementos con selector: {selector}")
                        for elemento in elementos:
                            resultado = self._process_element(elemento, palabra)
                            if resultado:
                                resultados.append(resultado)
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} falló: {e}")
                    continue
            
            # Si no encontramos resultados estructurados, buscar texto libre
            if not resultados:
                resultados = self._search_free_text(palabra)
                
        except Exception as e:
            logger.error(f"Error extrayendo resultados con Selenium: {e}")
        
        return resultados
    
    def _process_element(self, elemento, palabra: str) -> Optional[SearchResult]:
        """Procesa un elemento individual encontrado con Selenium."""
        try:
            texto = elemento.text.strip()
            if not texto or len(texto) < 10:
                return None
                
            titulo = extract_sentencia_number(texto)
            if not titulo:
                return None
                
            tema = extract_tema_from_text(texto, palabra)
            subtema = extract_tema_from_text(texto, palabra)
            
            # Buscar enlaces
            enlaces = elemento.find_elements(By.TAG_NAME, "a")
            url_html = ""
            url_pdf = ""
            
            for enlace in enlaces:
                href = enlace.get_attribute("href")
                if href and "relatoria" in href:
                    url_html = normalize_url(href)
                    url_pdf = url_html.replace('.htm', '.pdf')
                    break
            
            if not url_html:
                # Generar URLs basadas en el patrón conocido
                año = re.search(r'(\d{4})', titulo)
                if año:
                    url_html, url_pdf = generate_sentencia_urls(titulo, año.group(1))
            
            # Extraer resumen
            resumen = self._extract_resumen(elemento)
            
            return SearchResult(
                tema=tema,
                subtema=subtema,
                providencias=[Sentencia(
                    titulo=titulo,
                    url_html=url_html,
                    url_pdf=url_pdf,
                    resumen=resumen
                )]
            )
            
        except Exception as e:
            logger.debug(f"Error procesando elemento Selenium: {e}")
            return None
    
    def _search_free_text(self, palabra: str) -> List[SearchResult]:
        """Busca resultados en texto libre de la página."""
        resultados = []
        
        try:
            texto_pagina = self.driver.find_element(By.TAG_NAME, "body").text
            sentencias = re.findall(ScrapingConfig.SENTENCIA_PATTERN, texto_pagina)
            
            for sentencia in sentencias[:10]:
                contexto = self._find_sentencia_context(texto_pagina, sentencia, palabra)
                if contexto:
                    resultados.append(contexto)
                    
        except Exception as e:
            logger.error(f"Error buscando texto libre: {e}")
        
        return resultados
    
    def _find_sentencia_context(self, texto_pagina: str, sentencia: str, palabra_busqueda: str) -> Optional[SearchResult]:
        """Busca el contexto alrededor de una sentencia en el texto."""
        try:
            pos = texto_pagina.find(sentencia)
            if pos == -1:
                return None
            
            # Extraer contexto alrededor de la sentencia
            inicio = max(0, pos - 200)
            fin = min(len(texto_pagina), pos + 400)
            contexto = texto_pagina[inicio:fin]
            
            tema = extract_tema_from_text(contexto, palabra_busqueda)
            subtema = extract_subtema_from_text(contexto, palabra_busqueda)
            
            # Generar URLs
            año = re.search(r'(\d{4})', sentencia)
            url_html, url_pdf = "", ""
            
            if año:
                url_html, url_pdf = generate_sentencia_urls(sentencia, año.group(1))
            
            return SearchResult(
                tema=tema,
                subtema=subtema,
                providencias=[Sentencia(
                    titulo=sentencia,
                    url_html=url_html,
                    url_pdf=url_pdf
                )]
            )
            
        except Exception as e:
            logger.debug(f"Error buscando contexto: {e}")
            return None

    def _extract_resumen(self, elemento) -> str:
        """Extrae el resumen de la sentencia del elemento."""
        try:
            # Buscar específicamente en la clase resumen-texto que es donde está el resumen real
            selectores_resumen = [
                ".resumen-texto",
                ".resumen p",
                ".resumen",
                "p.resumen-texto",
                "[class*='resumen']"
            ]
            
            for selector in selectores_resumen:
                try:
                    elemento_resumen = elemento.find_element(By.CSS_SELECTOR, selector)
                    if elemento_resumen:
                        texto = elemento_resumen.text.strip()
                        if texto and len(texto) > 50:  # Debe ser un texto significativo
                            return texto
                except:
                    continue
            
            # Si no encontramos un selector específico, buscar texto largo
            texto_elemento = elemento.text.strip()
            # Buscar párrafos largos que podrían ser el resumen
            parrafos = elemento.find_elements(By.TAG_NAME, "p")
            for parrafo in parrafos:
                texto = parrafo.text.strip()
                if len(texto) > 100:  # Párrafo largo probablemente es el resumen
                    return texto
            
            return ""
            
        except Exception as e:
            logger.debug(f"Error extrayendo resumen: {e}")
            return ""
    
    def _cleanup(self):
        """Limpia recursos del driver."""
        if self.driver:
            self.driver.quit()
    
    def _extract_resumen(self, elemento) -> str:
        """Extrae el resumen de la sentencia del elemento."""
        try:
            # Buscar específicamente en la clase resumen-texto que es donde está el resumen real
            selectores_resumen = [
                ".resumen-texto",
                ".resumen p",
                ".resumen",
                "p.resumen-texto",
                "[class*='resumen']"
            ]
            
            for selector in selectores_resumen:
                try:
                    elemento_resumen = elemento.find_element(By.CSS_SELECTOR, selector)
                    if elemento_resumen:
                        texto = elemento_resumen.text.strip()
                        if texto and len(texto) > 50:  # Debe ser un texto significativo
                            return texto
                except:
                    continue
            
            # Si no se encuentra con selectores específicos, buscar en todo el elemento
            texto_elemento = elemento.text
            if "Resumen:" in texto_elemento:
                # Extraer texto después de "Resumen:"
                partes = texto_elemento.split("Resumen:")
                if len(partes) > 1:
                    resumen = partes[1].strip()
                    if resumen and len(resumen) > 50:
                        return resumen
            
            # Buscar en elementos que contengan "Resumen:" seguido de texto
            try:
                elementos_resumen = elemento.find_elements(By.XPATH, ".//*[contains(text(), 'Resumen:')]")
                for elem in elementos_resumen:
                    texto = elem.text.strip()
                    if "Resumen:" in texto:
                        resumen = texto.split("Resumen:")[1].strip()
                        if resumen and len(resumen) > 50:
                            return resumen
            except:
                pass
            
            return ""
            
        except Exception as e:
            logger.debug(f"Error extrayendo resumen: {e}")
            return ""
    


class BeautifulSoupExtractor:
    """Extractor usando BeautifulSoup para HTML estático."""
    
    def extract(self, url: str, palabra: str) -> List[SearchResult]:
        """Extrae datos usando BeautifulSoup."""
        try:
            session = requests.Session()
            session.headers.update(ScrapingConfig.get_headers())
            
            response = session.get(url, timeout=ScrapingConfig.REQUESTS_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return self._extract_results(soup, palabra)
            
        except Exception as e:
            logger.error(f"Error con BeautifulSoup: {e}")
            return []
    
    def _extract_results(self, soup, palabra: str) -> List[SearchResult]:
        """Extrae resultados usando BeautifulSoup."""
        resultados = []
        
        try:
            patrones_busqueda = [
                "table tbody tr",
                ".resultado",
                ".sentencia", 
                ".providencia",
                "[data-resultado]",
                "a[href*='relatoria']"
            ]
            
            for patron in patrones_busqueda:
                elementos = soup.select(patron)
                if elementos:
                    logger.info(f"Encontrados {len(elementos)} elementos con patrón: {patron}")
                    for elemento in elementos:
                        resultado = self._process_element(elemento, palabra)
                        if resultado:
                            resultados.append(resultado)
                    break
            
            # Si no encontramos elementos estructurados, buscar en texto libre
            if not resultados:
                resultados = self._search_free_text(soup, palabra)
                
        except Exception as e:
            logger.error(f"Error extrayendo con BeautifulSoup: {e}")
        
        return resultados
    
    def _process_element(self, elemento, palabra: str) -> Optional[SearchResult]:
        """Procesa un elemento individual encontrado con BeautifulSoup."""
        try:
            texto = elemento.get_text(strip=True)
            if not texto or len(texto) < 10:
                return None
                
            titulo = extract_sentencia_number(texto)
            if not titulo:
                return None
                
            tema = extract_tema_from_text(texto, palabra)
            subtema = extract_subtema_from_text(texto, palabra)
            
            # Buscar enlaces
            enlaces = elemento.find_all('a', href=True)
            url_html = ""
            url_pdf = ""
            
            for enlace in enlaces:
                href = enlace.get('href')
                if href and "relatoria" in href:
                    url_html = normalize_url(href)
                    url_pdf = url_html.replace('.htm', '.pdf')
                    break
            
            if not url_html:
                # Generar URLs basadas en el patrón conocido
                año = re.search(r'(\d{4})', titulo)
                if año:
                    url_html, url_pdf = generate_sentencia_urls(titulo, año.group(1))
            
            # Extraer resumen
            resumen = self._extract_resumen(elemento)
            
            return SearchResult(
                tema=tema,
                subtema=subtema,
                providencias=[Sentencia(
                    titulo=titulo,
                    url_html=url_html,
                    url_pdf=url_pdf,
                    resumen=resumen
                )]
            )
            
        except Exception as e:
            logger.debug(f"Error procesando elemento BeautifulSoup: {e}")
            return None
    
    def _search_free_text(self, soup, palabra: str) -> List[SearchResult]:
        """Busca resultados en texto libre de la página."""
        resultados = []
        
        try:
            texto_pagina = soup.get_text()
            sentencias = re.findall(ScrapingConfig.SENTENCIA_PATTERN, texto_pagina)
            
            for sentencia in sentencias[:10]:
                contexto = self._find_sentencia_context(texto_pagina, sentencia, palabra)
                if contexto:
                    resultados.append(contexto)
                    
        except Exception as e:
            logger.error(f"Error buscando texto libre: {e}")
        
        return resultados
    
    def _find_sentencia_context(self, texto_pagina: str, sentencia: str, palabra_busqueda: str) -> Optional[SearchResult]:
        """Busca el contexto alrededor de una sentencia en el texto."""
        try:
            pos = texto_pagina.find(sentencia)
            if pos == -1:
                return None
            
            # Extraer contexto alrededor de la sentencia
            inicio = max(0, pos - 200)
            fin = min(len(texto_pagina), pos + 400)
            contexto = texto_pagina[inicio:fin]
            
            tema = extract_tema_from_text(contexto, palabra_busqueda)
            subtema = extract_subtema_from_text(contexto, palabra_busqueda)
            
            # Generar URLs
            año = re.search(r'(\d{4})', sentencia)
            url_html, url_pdf = "", ""
            
            if año:
                url_html, url_pdf = generate_sentencia_urls(sentencia, año.group(1))
            
            return SearchResult(
                tema=tema,
                subtema=subtema,
                providencias=[Sentencia(
                    titulo=sentencia,
                    url_html=url_html,
                    url_pdf=url_pdf
                )]
            )
            
        except Exception as e:
            logger.debug(f"Error buscando contexto: {e}")
            return None
    
    def _extract_resumen(self, elemento) -> str:
        """Extrae el resumen de la sentencia del elemento usando BeautifulSoup."""
        try:
            # Buscar específicamente en la clase resumen-texto que es donde está el resumen real
            selectores_resumen = [
                ".resumen-texto",
                ".resumen p",
                ".resumen",
                "p.resumen-texto",
                "[class*='resumen']"
            ]
            
            for selector in selectores_resumen:
                try:
                    elementos_resumen = elemento.select(selector)
                    for elemento_resumen in elementos_resumen:
                        texto = elemento_resumen.get_text(strip=True)
                        if texto and len(texto) > 50:  # Debe ser un texto significativo
                            return texto
                except:
                    continue
            
            # Si no se encuentra con selectores específicos, buscar en todo el elemento
            texto_elemento = elemento.get_text()
            if "Resumen:" in texto_elemento:
                # Extraer texto después de "Resumen:"
                partes = texto_elemento.split("Resumen:")
                if len(partes) > 1:
                    resumen = partes[1].strip()
                    if resumen and len(resumen) > 50:
                        return resumen
            
            # Buscar en elementos que contengan "Resumen:" seguido de texto
            try:
                elementos_resumen = elemento.find_all(text=re.compile(r'Resumen:', re.IGNORECASE))
                for elem in elementos_resumen:
                    if hasattr(elem, 'parent'):
                        texto = elem.parent.get_text()
                        if "Resumen:" in texto:
                            resumen = texto.split("Resumen:")[1].strip()
                            if resumen and len(resumen) > 50:
                                return resumen
            except:
                pass
            
            return ""
            
        except Exception as e:
            logger.debug(f"Error extrayendo resumen con BeautifulSoup: {e}")
            return ""
    
    def _extract_magistrado(self, elemento) -> str:
        """Extrae el nombre del magistrado del elemento usando BeautifulSoup."""
        try:
            # Buscar en diferentes selectores que puedan contener el magistrado
            selectores_magistrado = [
                ".magistrado",
                ".magistrado-nombre",
                ".presidente",
                ".juez",
                ".relator",
                "span",
                "div",
                "td"
            ]
            
            for selector in selectores_magistrado:
                try:
                    elementos_magistrado = elemento.select(selector)
                    for elemento_magistrado in elementos_magistrado:
                        texto = elemento_magistrado.get_text(strip=True)
                        if texto and "Magistrado" in texto:
                            # Extraer solo el nombre, no el título
                            nombre = texto.replace("Magistrado", "").replace("Magistrada", "").strip()
                            if nombre and len(nombre) > 2:
                                return nombre
                except:
                    continue
            
            # Buscar texto que contenga "Magistrado" seguido de un nombre
            texto_elemento = elemento.get_text()
            patron_magistrado = r'Magistrado[ao]?\s*:?\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ\s]+)'
            match = re.search(patron_magistrado, texto_elemento)
            if match:
                return match.group(1).strip()
            
            return ""
            
        except Exception as e:
            logger.debug(f"Error extrayendo magistrado con BeautifulSoup: {e}")
            return ""
