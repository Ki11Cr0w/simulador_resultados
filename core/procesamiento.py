# core/procesamiento.py
import pandas as pd
from collections import defaultdict
from datetime import datetime
from .utils import normalizar_columnas, parsear_fecha, convertir_monto

class ProcesadorArchivos:
    """Clase para procesar archivos de ventas y compras."""
    
    @staticmethod
    def detectar_año_mes_predominante(fechas):
        """Detecta el año-mes que predomina en las fechas."""
        if not fechas:
            return None, None, 0
        
        # Contar por año-mes
        contador = defaultdict(int)
        
        for fecha in fechas:
            año_mes = f"{fecha.year}-{fecha.month:02d}"
            contador[año_mes] += 1
        
        # Encontrar el año-mes más común
        if not contador:
            return None, None, 0
        
        año_mes_comun, cantidad = max(contador.items(), key=lambda x: x[1])
        
        # Extraer año y mes
        año_str, mes_str = año_mes_comun.split('-')
        return int(año_str), int(mes_str), cantidad
    
    @staticmethod
    def procesar_archivo(archivo, tipo_archivo):
        """Procesa un archivo y extrae la información."""
        try:
            # Leer archivo según extensión
            if archivo.name.endswith('.csv'):
                df = pd.read_csv(archivo, sep=';', decimal=',')
            else:
                df = pd.read_excel(archivo)
            
            df = normalizar_columnas(df)
            
            # Verificar columnas requeridas
            columnas_requeridas = ['fecha_docto', 'tipo_documento', 'monto_total']
            columnas_faltantes = [c for c in columnas_requeridas if c not in df.columns]
            
            if columnas_faltantes:
                raise ValueError(f"Faltan columnas: {columnas_faltantes}")
            
            # Procesar documentos
            documentos = []
            fechas_validas = []
            
            for _, fila in df.iterrows():
                # Tipo de documento
                try:
                    tipo_doc_val = fila.get('tipo_documento', 0)
                    if pd.isna(tipo_doc_val):
                        tipo_doc = 0
                    else:
                        tipo_doc = int(float(tipo_doc_val))
                except:
                    tipo_doc = 0
                
                factor = -1 if tipo_doc == 61 else 1
                
                # Monto total
                monto_raw = fila.get('monto_total', 0)
                monto_total = convertir_monto(monto_raw)
                
                # Fecha
                fecha_raw = fila.get('fecha_docto', '')
                fecha_dt = parsear_fecha(fecha_raw)
                
                if fecha_dt:
                    documentos.append({
                        'fecha': fecha_dt,
                        'monto': monto_total * factor,
                        'tipo': tipo_archivo,
                        'tipo_doc': tipo_doc,
                        'archivo_origen': archivo.name
                    })
                    fechas_validas.append(fecha_dt)
            
            if not documentos:
                raise ValueError("No se encontraron documentos con fecha válida")
            
            # Detectar año-mes predominante
            año_pred, mes_pred, cantidad = ProcesadorArchivos.detectar_año_mes_predominante(fechas_validas)
            
            # Calcular estadísticas
            fecha_min = min(fechas_validas)
            fecha_max = max(fechas_validas)
            total_monto = sum(d['monto'] for d in documentos)
            
            return {
                'documentos': documentos,
                'fechas_validas': fechas_validas,
                'año_predominante': año_pred,
                'mes_predominante': mes_pred,
                'cantidad_predominante': cantidad,
                'fecha_minima': fecha_min,
                'fecha_maxima': fecha_max,
                'total_monto': total_monto,
                'nombre_archivo': archivo.name,
                'tipo_archivo': tipo_archivo,
                'documentos_count': len(documentos)
            }
            
        except Exception as e:
            raise Exception(f"Error procesando archivo {archivo.name}: {str(e)}")
