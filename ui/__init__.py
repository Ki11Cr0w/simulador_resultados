# ui/__init__.py
from .componentes import (
    mostrar_metricas_principales,
    mostrar_tabla_resultados,
    crear_uploader_multiple,
    procesar_lote_archivos
)

from .vistas import (
    vista_carga_multiple_archivos,
    vista_resumen_compacto,
    vista_resultados
)

__all__ = [
    'vista_carga_multiple_archivos',
    'vista_resumen_compacto',
    'vista_resultados',
    'mostrar_metricas_principales',
    'mostrar_tabla_resultados',
    'crear_uploader_multiple',
    'procesar_lote_archivos'
]
