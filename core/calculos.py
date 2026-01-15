# core/calculos.py
from collections import defaultdict
from .utils import formatear_monto

class CalculadoraResultados:
    """Clase para realizar cálculos de resultados."""
    
    @staticmethod
    def agrupar_por_periodo(documentos, periodos_asignados):
        """Agrupa documentos por período asignado."""
        resumen = defaultdict(lambda: {
            'ventas': 0,
            'compras': 0,
            'documentos_ventas': 0,
            'documentos_compras': 0
        })
        
        for doc in documentos:
            # Obtener período asignado para este documento
            archivo_key = doc['archivo_origen']
            periodo = periodos_asignados.get(archivo_key, "Sin_periodo")
            
            if doc['tipo'] == 'venta':
                resumen[periodo]['ventas'] += doc['monto']
                resumen[periodo]['documentos_ventas'] += 1
            else:
                resumen[periodo]['compras'] += doc['monto']
                resumen[periodo]['documentos_compras'] += 1
        
        return dict(resumen)
    
    @staticmethod
    def calcular_totales(resumen_periodos):
        """Calcula totales a partir del resumen por períodos."""
        total_ventas = sum(p['ventas'] for p in resumen_periodos.values())
        total_compras = sum(p['compras'] for p in resumen_periodos.values())
        total_resultado = total_ventas - total_compras
        
        total_docs_ventas = sum(p['documentos_ventas'] for p in resumen_periodos.values())
        total_docs_compras = sum(p['documentos_compras'] for p in resumen_periodos.values())
        total_documentos = total_docs_ventas + total_docs_compras
        
        return {
            'ventas_totales': total_ventas,
            'compras_totales': total_compras,
            'resultado_total': total_resultado,
            'documentos_ventas': total_docs_ventas,
            'documentos_compras': total_docs_compras,
            'documentos_totales': total_documentos
        }
    
    @staticmethod
    def generar_dataframe_resultados(resumen_periodos):
        """Genera lista de diccionarios con resultados por período."""
        periodos_ordenados = sorted(resumen_periodos.keys())
        
        datos = []
        for periodo in periodos_ordenados:
            datos_periodo = resumen_periodos[periodo]
            resultado = datos_periodo['ventas'] - datos_periodo['compras']
            margen = (resultado / datos_periodo['ventas'] * 100) if datos_periodo['ventas'] != 0 else 0
            
            datos.append({
                'Período': periodo,
                'Ventas': datos_periodo['ventas'],
                'Compras': datos_periodo['compras'],
                'Resultado': resultado,
                'Docs V': datos_periodo['documentos_ventas'],
                'Docs C': datos_periodo['documentos_compras'],
                'Margen %': margen
            })
        
        return datos
    
    @staticmethod
    def calcular_estadisticas(documentos):
        """Calcula estadísticas adicionales."""
        # Documentos tipo 61
        docs_61_ventas = len([d for d in documentos if d['tipo'] == 'venta' and d['tipo_doc'] == 61])
        docs_61_compras = len([d for d in documentos if d['tipo'] == 'compra' and d['tipo_doc'] == 61])
        
        # Promedios
        ventas = [d for d in documentos if d['tipo'] == 'venta']
        compras = [d for d in documentos if d['tipo'] == 'compra']
        
        promedio_venta = sum(d['monto'] for d in ventas) / len(ventas) if ventas else 0
        promedio_compra = sum(d['monto'] for d in compras) / len(compras) if compras else 0
        
        return {
            'notas_credito_ventas': docs_61_ventas,
            'notas_credito_compras': docs_61_compras,
            'promedio_venta': promedio_venta,
            'promedio_compra': promedio_compra,
            'total_ventas_count': len(ventas),
            'total_compras_count': len(compras)
        }
