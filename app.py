import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import io

# Configuración de la página web
st.set_page_config(page_title="Simulador de Punto de Equilibrio Pro", layout="wide", page_icon="📈")

# Título principal y descripción corta
st.title("📈 Simulador de Punto de Equilibrio Pro")
st.markdown("Ajustá los valores para calcular las unidades exactas a vender considerando impuestos y exportá tus proyecciones.")

st.divider()

# --- BARRA LATERAL: ENTRADA DE DATOS ---
st.sidebar.header("⚙️ Parámetros del Negocio")

# Entradas numéricas con inputs directos y tooltips
costos_fijos = st.sidebar.number_input(
    "Costos Fijos Totales ($)", 
    min_value=0.0, 
    value=1000.0, 
    step=50.0,
    help="Alquiler, sueldos, servicios fijos, etc. (Gastos mensuales recurrentes)."
)

precio_venta = st.sidebar.number_input(
    "Precio de Venta por Unidad ($)", 
    min_value=0.1, 
    value=50.0, 
    step=1.0,
    help="Precio final de cara al cliente antes de impuestos."
)

costo_variable = st.sidebar.number_input(
    "Costo Variable por Unidad ($)", 
    min_value=0.0, 
    value=20.0, 
    step=1.0,
    help="Materia prima, empaque, comisiones directas de venta, etc."
)

porcentaje_impuesto = st.sidebar.number_input(
    "Impuesto sobre Ventas / IVA (%)", 
    min_value=0.0, 
    max_value=100.0, 
    value=21.0, 
    step=0.5,
    help="Porcentaje impositivo que aplica sobre el precio de venta."
)

# --- CÁLCULOS MATEMÁTICOS AVANZADOS ---
# Margen de contribución unitario bruto
margen_contribucion_bruto = precio_venta - costo_variable

# Monto del impuesto por unidad vendida
impuesto_por_unidad = precio_venta * (porcentaje_impuesto / 100.0)

# Margen de contribución neto (restando el impuesto)
margen_contribucion_neto = margen_contribucion_bruto - impuesto_por_unidad

# Validación de viabilidad del negocio
if margen_contribucion_neto <= 0:
    st.error("⚠️ ¡Alerta de Viabilidad! El margen neto por unidad es menor o igual a cero. Ajustá tus costos, subí el precio o revisá la carga impositiva porque estás perdiendo dinero con cada venta.")
    st.stop()

# Punto de equilibrio exacto en unidades netas
punto_equilibrio_exacto = costos_fijos / margen_contribucion_neto

# Unidades enteras requeridas para ganar al menos $1 neto
unidades_ganar_uno = int(punto_equilibrio_exacto) + 1

# Facturación total bruta necesaria en el punto de equilibrio (incluye el impuesto recaudado)
ingresos_equilibrio_bruto = punto_equilibrio_exacto * precio_venta

# --- MÉTRICAS CLAVE (KPIs) ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="🎯 Ventas para ganar > $0", 
        value=f"{unidades_ganar_uno} unidades",
        help="Cantidad entera mínima de unidades para superar los costos y los impuestos."
    )

with col2:
    st.metric(
        label="💸 Margen Neto Unitario", 
        value=f"${margen_contribucion_neto:,.2f}",
        help="Dinero limpio por unidad que queda tras restar costos variables e impuestos."
    )

with col3:
    st.metric(
        label="🏦 Impuesto Recaudado/u", 
        value=f"${impuesto_por_unidad:,.2f}",
        help="Carga impositiva aplicada a cada unidad vendida."
    )

with col4:
    st.metric(
        label="💰 Facturación Mínima", 
        value=f"${ingresos_equilibrio_bruto:,.2f}",
        help="Ingresos brutos totales necesarios en caja para alcanzar el equilibrio."
    )

st.divider()

# --- GENERACIÓN DE DATOS PARA EL GRÁFICO ---
max_unidades = max(int(punto_equilibrio_exacto * 2), 10)
unidades_seq = list(range(0, max_unidades + 1))

ingresos_brutos = [u * precio_venta for u in unidades_seq]
impuestos_totales = [u * impuesto_por_unidad for u in unidades_seq]
costos_variables_totales = [u * costo_variable for u in unidades_seq]
costos_totales_con_impuestos = [costos_fijos + cv + imp for cv, imp in zip(costos_variables_totales, impuestos_totales)]
utilidad_neta = [ing - c_tot for ing, c_tot in zip(ingresos_brutos, costos_totales_con_impuestos)]

# Crear DataFrame estructurado
df = pd.DataFrame({
    'Unidades': unidades_seq,
    'Ingresos Brutos ($)': ingresos_brutos,
    'Costos Fijos ($)': [costos_fijos] * len(unidades_seq),
    'Costos Variables ($)': costos_variables_totales,
    'Impuestos Recaudados ($)': impuestos_totales,
    'Costos Totales + Impuestos ($)': costos_totales_con_impuestos,
    'Utilidad Neta ($)': utilidad_neta
})

# --- GRÁFICO DINÁMICO CON PLOTLY ---
fig = go.Figure()

# Línea de Costos Fijos
fig.add_trace(go.Scatter(
    x=df['Unidades'], y=df['Costos Fijos ($)'],
    mode='lines', name='Costos Fijos',
    line=dict(color='orange', dash='dash')
))

# Línea de Costos Totales + Impuestos
fig.add_trace(go.Scatter(
    x=df['Unidades'], y=df['Costos Totales + Impuestos ($)'],
    mode='lines', name='Costos Totales + Impuestos',
    line=dict(color='red')
))

# Línea de Ingresos Brutos
fig.add_trace(go.Scatter(
    x=df['Unidades'], y=df['Ingresos Brutos ($)'],
    mode='lines', name='Ingresos Brutos',
    line=dict(color='green')
))

# Punto de Equilibrio en el gráfico
fig.add_trace(go.Scatter(
    x=[punto_equilibrio_exacto], y=[ingresos_equilibrio_bruto],
    mode='markers+text', name='Punto de Equilibrio',
    text=[f" PE ({punto_equilibrio_exacto:.1f} u)"],
    textposition="top left",
    marker=dict(color='black', size=12, symbol='x')
))

fig.update_layout(
    title="Análisis Gráfico: Impacto de Costos e Impuestos en las Ventas",
    xaxis_title="Unidades Vendidas",
    yaxis_title="Dinero ($)",
    hovermode="x unified",
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    height=550
)

st.plotly_chart(fig, use_container_width=True)

# --- BOTONES DE EXPORTACIÓN Y TABLA ---
st.subheader("📋 Datos del Escenario y Exportación")

# Conversión a formato CSV e Excel en memoria
csv_data = df.to_csv(index=False).encode('utf-8')

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    df.to_excel(writer, index=False, sheet_name='Proyecciones')
excel_data = buffer.getvalue()

col_btn1, col_btn2, _ = st.columns([1, 1, 2])

with col_btn1:
    st.download_button(
        label="📥 Descargar CSV",
        data=csv_data,
        file_name="proyecciones_punto_equilibrio.csv",
        mime="text/csv"
    )

with col_btn2:
    st.download_button(
        label="📥 Descargar Excel",
        data=excel_data,
        file_name="proyecciones_punto_equilibrio.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Tabla interactiva formateada
st.dataframe(
    df.style.format({
        'Ingresos Brutos ($)': '${:,.2f}',
        'Costos Fijos ($)': '${:,.2f}',
        'Costos Variables ($)': '${:,.2f}',
        'Impuestos Recaudados ($)': '${:,.2f}',
        'Costos Totales + Impuestos ($)': '${:,.2f}',
        'Utilidad Neta ($)': '${:,.2f}'
    }),
    use_container_width=True
)
