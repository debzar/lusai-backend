#!/bin/bash

# 🚀 Script de instalación automática para el servicio de scraping
# Corte Constitucional de Colombia

set -e  # Salir si hay algún error

echo "🚀 INICIANDO INSTALACIÓN DEL SERVICIO DE SCRAPING"
echo "=================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir con colores
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detectar sistema operativo
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            OS="debian"
        elif [ -f /etc/redhat-release ]; then
            OS="redhat"
        else
            OS="linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
    else
        OS="unknown"
    fi
    echo "Sistema operativo detectado: $OS"
}

# Verificar si Python está instalado
check_python() {
    print_status "Verificando instalación de Python..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1)
        print_success "Python encontrado: $PYTHON_VERSION"
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version 2>&1)
        print_success "Python encontrado: $PYTHON_VERSION"
        PYTHON_CMD="python"
    else
        print_error "Python no está instalado. Por favor instala Python 3.7+ primero."
        exit 1
    fi
    
    # Verificar versión mínima
    PYTHON_MAJOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.major)")
    PYTHON_MINOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.minor)")
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 7 ]); then
        print_error "Se requiere Python 3.7 o superior. Versión actual: $PYTHON_MAJOR.$PYTHON_MINOR"
        exit 1
    fi
}

# Verificar si pip está instalado
check_pip() {
    print_status "Verificando instalación de pip..."
    
    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        print_error "pip no está instalado. Por favor instala pip primero."
        exit 1
    fi
    
    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
    else
        PIP_CMD="pip"
    fi
    
    print_success "pip encontrado: $($PIP_CMD --version)"
}

# Instalar dependencias de Python
install_python_deps() {
    print_status "Instalando dependencias de Python..."
    
    if [ -f "requirements.txt" ]; then
        $PIP_CMD install -r requirements.txt
        print_success "Dependencias de Python instaladas correctamente"
    else
        print_warning "requirements.txt no encontrado, instalando dependencias básicas..."
        $PIP_CMD install selenium==4.15.2 beautifulsoup4==4.12.2 requests==2.31.0 lxml==4.9.3
        print_success "Dependencias básicas instaladas"
    fi
}

# Instalar Chrome y ChromeDriver en Ubuntu/Debian
install_chrome_debian() {
    print_status "Instalando Google Chrome y ChromeDriver en Ubuntu/Debian..."
    
    # Agregar repositorio de Google Chrome
    if ! command -v google-chrome &> /dev/null; then
        print_status "Instalando Google Chrome..."
        wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
        echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
        sudo apt update
        sudo apt install -y google-chrome-stable
        print_success "Google Chrome instalado"
    else
        print_success "Google Chrome ya está instalado"
    fi
    
    # Instalar ChromeDriver
    if ! command -v chromedriver &> /dev/null; then
        print_status "Instalando ChromeDriver..."
        sudo apt install -y chromium-chromedriver
        print_success "ChromeDriver instalado"
    else
        print_success "ChromeDriver ya está instalado"
    fi
}

# Instalar Chrome y ChromeDriver en macOS
install_chrome_macos() {
    print_status "Instalando Google Chrome y ChromeDriver en macOS..."
    
    if ! command -v brew &> /dev/null; then
        print_error "Homebrew no está instalado. Por favor instala Homebrew primero:"
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    # Instalar Chrome
    if ! command -v google-chrome &> /dev/null; then
        print_status "Instalando Google Chrome..."
        brew install --cask google-chrome
        print_success "Google Chrome instalado"
    else
        print_success "Google Chrome ya está instalado"
    fi
    
    # Instalar ChromeDriver
    if ! command -v chromedriver &> /dev/null; then
        print_status "Instalando ChromeDriver..."
        brew install --cask chromedriver
        print_success "ChromeDriver instalado"
    else
        print_success "ChromeDriver ya está instalado"
    fi
}

# Instalar Chrome y ChromeDriver en Windows (usando Chocolatey)
install_chrome_windows() {
    print_status "Instalando Google Chrome y ChromeDriver en Windows..."
    
    if ! command -v choco &> /dev/null; then
        print_error "Chocolatey no está instalado. Por favor instala Chocolatey primero:"
        echo "  Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
        exit 1
    fi
    
    # Instalar Chrome
    if ! command -v google-chrome &> /dev/null; then
        print_status "Instalando Google Chrome..."
        choco install googlechrome -y
        print_success "Google Chrome instalado"
    else
        print_success "Google Chrome ya está instalado"
    fi
    
    # Instalar ChromeDriver
    if ! command -v chromedriver &> /dev/null; then
        print_status "Instalando ChromeDriver..."
        choco install chromedriver -y
        print_success "ChromeDriver instalado"
    else
        print_success "ChromeDriver ya está instalado"
    fi
}

# Verificar instalación de Chrome y ChromeDriver
verify_chrome_installation() {
    print_status "Verificando instalación de Chrome y ChromeDriver..."
    
    if command -v google-chrome &> /dev/null; then
        CHROME_VERSION=$(google-chrome --version)
        print_success "Google Chrome: $CHROME_VERSION"
    else
        print_warning "Google Chrome no encontrado en PATH"
    fi
    
    if command -v chromedriver &> /dev/null; then
        CHROMEDRIVER_VERSION=$(chromedriver --version)
        print_success "ChromeDriver: $CHROMEDRIVER_VERSION"
    else
        print_warning "ChromeDriver no encontrado en PATH"
    fi
}

# Probar el servicio
test_service() {
    print_status "Probando el servicio de scraping..."
    
    if [ -f "test_scraping_mejorado.py" ]; then
        print_status "Ejecutando script de prueba..."
        $PYTHON_CMD test_scraping_mejorado.py
        print_success "Prueba completada"
    else
        print_warning "Script de prueba no encontrado"
    fi
}

# Función principal
main() {
    echo
    print_status "Iniciando instalación del servicio de scraping..."
    echo
    
    # Detectar sistema operativo
    detect_os
    
    # Verificar Python
    check_python
    
    # Verificar pip
    check_pip
    
    # Instalar dependencias de Python
    install_python_deps
    
    # Instalar Chrome y ChromeDriver según el sistema operativo
    case $OS in
        "debian"|"ubuntu")
            install_chrome_debian
            ;;
        "macos")
            install_chrome_macos
            ;;
        "windows")
            install_chrome_windows
            ;;
        *)
            print_warning "Sistema operativo no soportado: $OS"
            print_warning "Por favor instala Chrome y ChromeDriver manualmente"
            ;;
    esac
    
    # Verificar instalación
    verify_chrome_installation
    
    # Probar el servicio
    test_service
    
    echo
    print_success "¡Instalación completada exitosamente! 🎉"
    echo
    print_status "Para usar el servicio:"
    echo "  python test_scraping_mejorado.py"
    echo
    print_status "Para más información, consulta:"
    echo "  README_SCRAPING.md"
    echo
}

# Ejecutar función principal
main "$@"
