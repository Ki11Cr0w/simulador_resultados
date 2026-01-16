# core/visualizaciones.py
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from .utils import formatear_monto

class VisualizadorResultados:
    """Clase para crear visualizaciones interactivas de resultados."""
    
    @staticmethod
    def crear_grafico_barras_apiladas(df_resultados):
        """Crea gráfico de barras apiladas de ventas vs compras por período."""
        if df_resultados.empty:
            return None
        
        fig = go.Figure()
        
        # Barras de ventas
        fig.add_trace(go.Bar(
            name='Ventas',
            x=df_resultados['Período'],
            y=df_resultados['Ventas'],
            marker_color='#2ecc71',
            hovertemplate='<b>%{x}</b><br>Ventas: %{y:$,.0f}<extra></extra>'
        ))
        
        # Barras de compras (negativas para comparación)
        fig.add_trace(go.Bar(
            name='Compras',
            x=df_resultados['Período'],
            y=df_resultados['Compras'],
            marker_color='#e74c3c',
            hovertemplate='<b>%{x}</b><br>Compras: %{y:$,.0f}<extra></extra>'
        ))
        
        fig.update_layout(
            title='📊 Ventas vs Compras por Período',
            barmode='group',
            xaxis_title='Período',
            yaxis_title='Monto ($)',
            hovermode='x unified',
            showlegend=True,
            height=400
        )
        
        return fig
    
    @staticmethod
    def crear_grafico_linea_resultado(df_resultados):
        """Crea gráfico de línea del resultado neto por período."""
        if df_resultados.empty:
            return None
        
        # Calcular resultado neto si no existe
        if 'Resultado' not in df_resultados.columns:
            df_resultados['Resultado'] = df_resultados['Ventas'] - df_resultados['Compras']
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_resultados['Período'],
            y=df_resultados['Resultado'],
            mode='lines+markers',
            name='Resultado Neto',
            line=dict(color='#3498db', width=3),
            marker=dict(size=8),
            hovertemplate='<b>%{x}</b><br>Resultado: %{y:$,.0f}<extra></extra>'
        ))
        
        # Línea en cero
        fig.add_hline(
            y=0, 
            line_dash="dash", 
            line_color="gray",
            opacity=0.5
        )
        
        fig.update_layout(
            title='📈 Evolución del Resultado Neto',
            xaxis_title='Período',
            yaxis_title='Resultado ($)',
            hovermode='x unified',
            height=350
        )
        
        return fig
    
    @staticmethod
    def crear_grafico_margen(df_resultados):
        """Crea gráfico de barras del margen porcentual."""
        if df_resultados.empty or 'Margen %' not in df_resultados.columns:
            return None
        
        # Calcular colores según margen
        colores = ['#e74c3c' if x < 0 else '#2ecc71' for x in df_resultados['Margen %']]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_resultados['Período'],
            y=df_resultados['Margen %'],
            marker_color=colores,
            hovertemplate='<b>%{x}</b><br>Margen: %{y:.1f}%<extra></extra>',
            text=df_resultados['Margen %'].apply(lambda x: f'{x:+.1f}%'),
            textposition='auto'
        ))
        
        # Línea en 0%
        fig.add_hline(
            y=0, 
            line_dash="dash", 
            line_color="gray",
            opacity=0.5
        )
        
        fig.update_layout(
            title='📊 Margen % por Período',
            xaxis_title='Período',
            yaxis_title='Margen (%)',
            height=350
        )
        
        return fig
    
    @staticmethod
    def crear_grafico_torta_totales(totales):
        """Crea gráfico de torta de la distribución total."""
        if not totales or totales['ventas_totales'] == 0:
            return None
        
        labels = ['Ventas', 'Compras', 'Resultado']
        valores = [
            totales['ventas_totales'],
            totales['compras_totales'],
            totales['resultado_total']
        ]
        
        colores = ['#2ecc71', '#e74c3c', '#3498db']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=valores,
            hole=.4,
            marker=dict(colors=colores),
            hovertemplate='<b>%{label}</b><br>%{value:$,.0f}<br>%{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title='🥧 Distribución Total',
            height=350,
            showlegend=True
        )
        
        return fig
    
    @staticmethod
    def crear_grafico_documentos(df_resultados):
        """Crea gráfico de documentos por período."""
        if df_resultados.empty or 'Docs V' not in df_resultados.columns:
            return None
        
        fig = go.Figure()
        
        # Documentos de ventas
        fig.add_trace(go.Bar(
            name='Docs Ventas',
            x=df_resultados['Período'],
            y=df_resultados['Docs V'],
            marker_color='#2ecc71',
            opacity=0.7,
            hovertemplate='<b>%{x}</b><br>Docs Ventas: %{y}<extra></extra>'
        ))
        
        # Documentos de compras
        fig.add_trace(go.Bar(
            name='Docs Compras',
            x=df_resultados['Período'],
            y=df_resultados['Docs C'],
            marker_color='#e74c3c',
            opacity=0.7,
            hovertemplate='<b>%{x}</b><br>Docs Compras: %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title='📄 Documentos por Período',
            barmode='stack',
            xaxis_title='Período',
            yaxis_title='Cantidad de Documentos',
            height=350
        )
        
        return fig
    
    @staticmethod
    def crear_heatmap_correlacion(df_resultados):
        """Crea heatmap de correlación entre variables."""
        if df_resultados.empty or len(df_resultados) < 3:
            return None
        
        # Seleccionar columnas numéricas
        columnas_numericas = df_resultados.select_dtypes(include=[np.number]).columns
        
        if len(columnas_numericas) < 2:
            return None
        
        # Calcular matriz de correlación
        correlacion = df_resultados[columnas_numericas].corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=correlacion.values,
            x=correlacion.columns,
            y=correlacion.index,
            colorscale='RdBu',
            zmid=0,
            text=correlacion.round(2).values,
            texttemplate='%{text}',
            textfont={"size": 10},
            hovertemplate='<b>%{y} vs %{x}</b><br>Correlación: %{z:.2f}<extra></extra>'
        ))
        
        fig.update_layout(
            title='🔥 Matriz de Correlación',
            height=400,
            xaxis_title='Variables',
            yaxis_title='Variables'
        )
        
        return fig
    
    @staticmethod
    def crear_grafico_evolucion_mensual(df_resultados):
        """Crea gráfico de evolución mensual comparativa."""
        if df_resultados.empty:
            return None
        
        # Extraer año y mes del período
        df_resultados['Año'] = df_resultados['Período'].str.split('-').str[0].astype(int)
        df_resultados['Mes'] = df_resultados['Período'].str.split('-').str[1].astype(int)
        
        # Ordenar por año y mes
        df_ordenado = df_resultados.sort_values(['Año', 'Mes'])
        
        fig = go.Figure()
        
        # Línea de ventas
        fig.add_trace(go.Scatter(
            x=df_ordenado['Período'],
            y=df_ordenado['Ventas'],
            mode='lines+markers',
            name='Ventas',
            line=dict(color='#2ecc71', width=2),
            hovertemplate='<b>%{x}</b><br>Ventas: %{y:$,.0f}<extra></extra>'
        ))
        
        # Línea de compras
        fig.add_trace(go.Scatter(
            x=df_ordenado['Período'],
            y=df_ordenado['Compras'],
            mode='lines+markers',
            name='Compras',
            line=dict(color='#e74c3c', width=2),
            hovertemplate='<b>%{x}</b><br>Compras: %{y:$,.0f}<extra></extra>'
        ))
        
        fig.update_layout(
            title='📈 Evolución Mensual Comparativa',
            xaxis_title='Período',
            yaxis_title='Monto ($)',
            hovermode='x unified',
            height=400,
            showlegend=True
        )
        
        return fig
    
    @staticmethod
    def crear_dashboard_completo(df_resultados, totales, estadisticas):
        """Crea un dashboard completo con múltiples visualizaciones."""
        figs = {}
        
        # 1. Gráfico principal de barras
        figs['barras_apiladas'] = VisualizadorResultados.crear_grafico_barras_apiladas(df_resultados)
        
        # 2. Gráfico de resultado neto
        figs['linea_resultado'] = VisualizadorResultados.crear_grafico_linea_resultado(df_resultados)
        
        # 3. Gráfico de margen
        figs['barras_margen'] = VisualizadorResultados.crear_grafico_margen(df_resultados)
        
        # 4. Gráfico de torta
        figs['torta_totales'] = VisualizadorResultados.crear_grafico_torta_totales(totales)
        
        # 5. Gráfico de documentos
        figs['barras_documentos'] = VisualizadorResultados.crear_grafico_documentos(df_resultados)
        
        # 6. Evolución mensual
        figs['evolucion_mensual'] = VisualizadorResultados.crear_grafico_evolucion_mensual(df_resultados)
        
        # 7. Heatmap de correlación (si hay suficientes datos)
        if len(df_resultados) >= 3:
            figs['heatmap_correlacion'] = VisualizadorResultados.crear_heatmap_correlacion(df_resultados)
        
        return figs
