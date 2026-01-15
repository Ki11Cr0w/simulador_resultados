# ui/__init__.py
from .componentes import (
    mostrar_metricas_principales,
    mostrar_tabla_resultados,
    crear_uploader_columnas,
    procesar_archivo_compacto
)

from .vistas import (
    vista_carga_archivos_compacta,
    vista_resumen_compacto,
    vista_resultados
)

__all__ = [
    'vista_carga_archivos_compacta',
    'vista_resumen_compacto',
    'vista_resultados',
    'mostrar_metricas_principales',
    'mostrar_tabla_resultados',
    'crear_uploader_columnas',
    'procesar_archivo_compacto'
]
