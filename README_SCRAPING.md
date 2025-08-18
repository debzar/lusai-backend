# 🚀 Servicio de Scraping Mejorado - Corte Constitucional de Colombia

## 📋 Descripción

Este servicio de scraping ha sido completamente reescrito para extraer datos reales de la página web de la Corte Constitucional de Colombia, en lugar de generar respuestas simuladas.

## ✨ Características Principales

- **Múltiples estrategias de extracción**: Selenium, BeautifulSoup y APIs
- **Manejo de contenido dinámico**: Compatible con aplicaciones Angular
- **Extracción inteligente**: Busca patrones específicos de sentencias judiciales
- **Fallback robusto**: Múltiples métodos de respaldo
- **Logging detallado**: Para debugging y monitoreo

## 🛠️ Instalación

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Instalar ChromeDriver (para Selenium)

#### En Ubuntu/Debian:
```bash
# Instalar Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install google-chrome-stable

# Instalar ChromeDriver
sudo apt install chromium-chromedriver
```

#### En macOS:
```bash
# Con Homebrew
brew install --cask google-chrome
brew install --cask chromedriver
```

#### En Windows:
- Descargar Chrome desde: https://www.google.com/chrome/
- Descargar ChromeDriver desde: https://chromedriver.chromium.org/
- Agregar ChromeDriver al PATH

### 3. Verificar instalación

```bash
python test_scraping_mejorado.py
```

## 🔧 Uso

### Uso básico

```python
from app.services.scraping_service import buscar_sentencias

# Buscar sentencias
resultados = buscar_sentencias(
    fecha_inicio="1992-01-01",
    fecha_fin="2025-08-17",
    palabra="agente oficioso",
    extra="",
    pagina=0
)

# Procesar resultados
for resultado in resultados:
    print(f"Tema: {resultado['tema']}")
    print(f"Subtema: {resultado['subtema']}")
    
    for providencia in resultado['providencias']:
        print(f"  - {providencia['titulo']}")
        print(f"    HTML: {providencia['url_html']}")
        print(f"    PDF: {providencia['url_pdf']}")
```

### Uso asíncrono

```python
from app.services.scraping_service import buscar_sentencias_async
import asyncio

async def main():
    resultados = await buscar_sentencias_async(
        fecha_inicio="1992-01-01",
        fecha_fin="2025-08-17",
        palabra="agente oficioso",
        extra="",
        pagina=0
    )
    return resultados

# Ejecutar
resultados = asyncio.run(main())
```

## 🎯 Estrategias de Extracción

### 1. **Selenium** (Prioridad Alta)
- **Ventaja**: Maneja contenido dinámico y JavaScript
- **Uso**: Para páginas que requieren renderizado completo
- **Configuración**: Chrome en modo headless

### 2. **BeautifulSoup + Requests** (Prioridad Media)
- **Ventaja**: Más rápido que Selenium
- **Uso**: Para páginas con HTML estático
- **Configuración**: Headers personalizados para simular navegador

### 3. **APIs Ocultas** (Prioridad Baja)
- **Ventaja**: Acceso directo a datos estructurados
- **Uso**: Cuando la página tiene endpoints de API
- **Configuración**: Headers específicos para AJAX

### 4. **Fallback** (Último recurso)
- **Ventaja**: Siempre devuelve algún resultado
- **Uso**: Cuando fallan todas las estrategias anteriores
- **Configuración**: Datos de ejemplo basados en patrones conocidos

## 📊 Estructura de Respuesta

```json
[
  {
    "tema": "DERECHO A LA EDUCACIÓN Y AGENTE OFICIOSO",
    "subtema": "Protección del derecho a la educación de menores por parte de agente oficiosa",
    "providencias": [
      {
        "titulo": "T-322/25",
        "url_html": "https://www.corteconstitucional.gov.co/relatoria/2025/T-322-25.htm",
        "url_pdf": "https://www.corteconstitucional.gov.co/relatoria/2025/T-322-25.pdf"
      }
    ]
  }
]
```

## 🔍 Patrones de Búsqueda

El servicio busca automáticamente:

- **Sentencias**: T-XXX/XX, C-XXX/XX, SU-XXX/XX
- **Autos**: AUTO-XXX/XX
- **Enlaces**: URLs que contengan "relatoria"
- **Contexto**: Texto alrededor de las sentencias para extraer tema y subtema

## 🚨 Solución de Problemas

### Error: "ChromeDriver not found"
```bash
# Verificar instalación de Chrome
google-chrome --version

# Verificar instalación de ChromeDriver
chromedriver --version

# Si ChromeDriver no está en PATH, especificar ruta
export PATH=$PATH:/usr/local/bin/chromedriver
```

### Error: "Selenium no disponible"
```bash
# Reinstalar Selenium
pip uninstall selenium
pip install selenium==4.15.2

# Verificar versión
python -c "import selenium; print(selenium.__version__)"
```

### Error: "Timeout esperando resultados"
- La página puede estar tardando en cargar
- Verificar conexión a internet
- Aumentar timeout en el código si es necesario

### No se encuentran resultados
- Verificar que la URL de búsqueda sea correcta
- Revisar logs para ver qué estrategias se están ejecutando
- Probar con búsquedas más simples

## 📝 Logging

El servicio incluye logging detallado:

```python
import logging

# Configurar nivel de logging
logging.basicConfig(level=logging.INFO)

# Los logs mostrarán:
# - Qué estrategia se está usando
# - Cuántos elementos se encuentran
# - Errores y warnings
# - Tiempo de ejecución
```

## 🔒 Consideraciones de Seguridad

- **Rate Limiting**: El servicio incluye delays para evitar sobrecargar el servidor
- **User-Agent**: Usa headers realistas para evitar bloqueos
- **Timeout**: Configurado para evitar conexiones colgadas
- **Error Handling**: Manejo robusto de excepciones

## 📈 Rendimiento

### Optimizaciones incluidas:
- **Headless Mode**: Chrome se ejecuta sin interfaz gráfica
- **Timeouts**: Configurados para evitar esperas innecesarias
- **Selectores CSS**: Optimizados para extracción rápida
- **Fallbacks**: Múltiples estrategias para máxima confiabilidad

### Tiempos esperados:
- **Selenium**: 15-30 segundos (primera vez), 5-15 segundos (subsiguientes)
- **BeautifulSoup**: 2-5 segundos
- **APIs**: 1-3 segundos

## 🤝 Contribuciones

Para contribuir al proyecto:

1. Fork el repositorio
2. Crear una rama para tu feature
3. Implementar cambios
4. Agregar tests
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

## 📞 Soporte

Si tienes problemas o preguntas:

1. Revisar este README
2. Verificar los logs del servicio
3. Probar con el script de test
4. Crear un issue en el repositorio

---

**¡Esperamos que este servicio te ayude a extraer datos de la Corte Constitucional de manera efectiva! 🎉**
