from enum import Enum

class TipoRelevo(str, Enum):
    SUBIDA = "Subida"
    DESCIDA = "Descida"
    PLANO = "Plano"
class ColorByRelevo(str, Enum):
    SUBIDA = "#E74C3C"    
    DESCIDA = "#2ECC71"  
    PLANO = "#3498DB"      