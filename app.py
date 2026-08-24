import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# Configuración de la página web
st.set_page_config(page_title="Simulador de Punto de Equilibrio", layout="wide", page_icon="📊")

# Título principal y descripción corta
st.title("📊 Simulador de Punto de Equilibrio Interactivo")
st.markdown("Ajustá los valores en la barra lateral para ver cuántas unidades necesitas vender para cubrir costos y ganar tu primer dólar.")

st.divider()

# --- BARRA LATERAL: ENTRADA DE DATOS ---
st.sidebar.header("⚙️ Parámetros del Negocio")

# Entradas numéricas con sliders e inputs directos
costos_fijos = st.sidebar.number_input(
    "Costos Fijos Totales ($)", 
    min_value=0.0, 
    value=1000.0, 
    step=50.0,
    help="Alquiler, sueldos, servicios fijos, etc. (Gastos que tenés sí o sí)."
)

precio_venta = st.sidebar.number_input(
    "Precio de Venta por Unidad ($)", 
    min_value=0.1, 
    value=50.0, 
    step=1.0,
    help="A cuánto vendés cada producto o servicio al público."
)

costo_variable = st.sidebar.number_input(
    "Costo Variable por Unidad ($)", 
    min_value=0.0, 
    value=20.0, 
    step=1.0,
    help="Cuánto te cuesta producir o adquirir cada unidad (materia prima, comisiones, etc.)."
)

# Validación crítica de negocio
if costo_variable >= precio_venta:
    st.error("⚠️ El costo variable no puede ser mayor o igual al precio de venta. ¡Estarías perdiendo dinero por cada unidad vendida!")
    st.stop()

# --- CÁLCULOS MATEMÁTICOS ---
# Margen de contribución unitario
margen_contribucion = precio_venta - costo_variable

# Punto de equilibrio exacto (Q = CF / Margen)
punto_equilibrio_exacto = costos_fijos / margen_contribucion

# Unidades para ganar exactamente $1 (Techo matemático del punto de equilibrio)
# Si da 33.3 unidades, necesitás vender 34 para estar en positivo.
unidades_ganar_uno = int(punto_equilibrio_exacto) + 1

# Ingresos necesarios para el punto de equilibrio
ingresos_equilibrio = punto_equilibrio_exacto * precio_venta

# --- MÉTRICAS CLAVE (KPIs) ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="🎯 Unidades para ganar > $0", 
        value=f"{unidades_ganar_uno} unidades",
        help="Cantidad entera de unidades que debés vender para superar el punto de equilibrio."
    )

with col2:
    st.metric(
        label="📈 Margen por Unidad", 
        value=f"${margen_contribucion:,.2f}",
        help="Lo que te queda limpio por cada venta para cubrir los costos fijos."
    )

with col3:
    st.metric(
        label="💰 Facturación de Equilibrio", 
        value=f"${ingresos_equilibrio:,.2f}",
        help="El dinero total que debe ingresar a tu caja para no ganar ni perder."
    )

st.divider()

# --- GENERACIÓN DE DATOS PARA EL GRÁFICO ---
# Definimos un rango dinámico de unidades para el eje X (hasta el doble del punto de equilibrio)
max_unidades = max(int(punto_equilibrio_exacto * 2), 10)
unidades_seq = list(range(0, max_unidades + 1))

# Cálculos de líneas
ingresos_totales = [u * precio_venta for u in unidades_seq]
costos_totales = [costos_fijos + (u * costo_variable) for u in unidades_seq]
utilidad = [ing - cos for ing, cos in zip(ingresos_totales, costos_totales)]

# Crear DataFrame para facilitar el manejo
df = pd.DataFrame({
    'Unidades': unidades_seq,
    'Ingresos': ingresos_totales,
    'Costos Totales': costos_totales,
    'Utilidad': utilidad
})

# --- GRÁFICO DINÁMICO CON PLOTLY ---
fig = go.Figure()

# Línea de Costos Fijos
fig.add_trace(go.Scatter(
    x=df['Unidades'], y=[costos_fijos]*len(unidades_seq),
    mode='lines', name='Costos Fijos',
    line=dict(color='orange', dash='dash')
))

# Línea de Costos Totales
fig.add_trace(go.Scatter(
    x=df['Unidades'], y=df['Costos Totales'],
    mode='lines', name='Costos Totales',
    line=dict(color='red')
))

# Línea de Ingresos Totales
fig.add_trace(go.Scatter(
    x=df['Unidades'], y=df['Ingresos'],
    mode='lines', name='Ingresos',
    line=dict(color='green')
))

# Punto de Equilibrio (Intersección)
fig.add_trace(go.Scatter(
    x=[punto_equilibrio_exacto], y=[ingresos_equilibrio],
    mode='markers+text', name='Punto de Equilibrio',
    text=[f"  PE ({punto_equilibrio_exacto:.1f} u)"],
    textposition="top left",
    marker=dict(color='black', size=12, symbol='x')
))

# Configuración de diseño del gráfico
fig.update_layout(
    title="Análisis Gráfico del Punto de Equilibrio",
    xaxis_title="Unidades Vendidas",
    yaxis_title="Dinero ($)",
    hovermode="x unified",
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    height=600
)

# Mostrar gráfico en la app
st.plotly_chart(fig, use_container_width=True)

# --- TABLA DE DATOS DE SOPORTE ---
with st.expander("📋 Ver tabla detallada de proyecciones"):
    st.dataframe(
        df.style.format({
            'Ingresos': '${:,.2f}',
            'Costos Totales': '${:,.2f}',
            'Utilidad': '${:,.2f}'
        }),
        use_container_width=True
    )
