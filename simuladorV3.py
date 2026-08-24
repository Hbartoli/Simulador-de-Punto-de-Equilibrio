import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import io

# Configuración de la página web
st.set_config = st.set_page_config(page_title="Simulador de Punto de Equilibrio Pro", layout="wide", page_icon="📊")

# Título principal y descripción corta
st.title("📊 Simulador de Punto de Equilibrio & Metas Financieras")
st.markdown("Analizá tu estructura de costos, calculá el punto de equilibrio y descubrí cuántas unidades necesitas vender para alcanzar tu meta de ganancias.")

st.divider()

# --- BARRA LATERAL: ENTRADA DE DATOS ---
st.sidebar.header("⚙️ Parámetros del Negocio")

costos_fijos = st.sidebar.number_input(
    "Costos Fijos Totales ($)", 
    min_value=0.0, value=1000.0, step=50.0,
    help="Gastos mensuales recurrentes (Alquiler, sueldos, servicios fijos, etc.)."
)

precio_venta = st.sidebar.number_input(
    "Precio de Venta por Unidad ($)", 
    min_value=0.1, value=50.0, step=1.0,
    help="Precio final de cara al cliente antes de impuestos."
)

costo_variable = st.sidebar.number_input(
    "Costo Variable por Unidad ($)", 
    min_value=0.0, value=20.0, step=1.0,
    help="Materia prima, empaque, comisiones directas de venta, etc."
)

porcentaje_impuesto = st.sidebar.number_input(
    "Impuesto sobre Ventas / IVA (%)", 
    min_value=0.0, max_value=100.0, value=21.0, step=0.5,
    help="Porcentaje impositivo que aplica sobre el precio de venta."
)

st.sidebar.header("🎯 Meta Mensual")
meta_ganancia = st.sidebar.number_input(
    "Ganancia Neta Deseada ($)", 
    min_value=0.0, value=500.0, step=50.0,
    help="Cuánto dinero limpio querés ganar al mes después de costos e impuestos."
)

# --- CÁLCULOS MATEMÁTICOS ---
margen_contribucion_bruto = precio_venta - costo_variable
impuesto_por_unidad = precio_venta * (porcentaje_impuesto / 100.0)
margen_contribucion_neto = margen_contribucion_bruto - impuesto_por_unidad

# Validación de viabilidad operativa
if margen_contribucion_neto <= 0:
    st.error("⚠️ ¡Alerta de Viabilidad! El margen neto por unidad es menor o igual a cero. Ajustá tus costos, subí el precio o revisá la carga impositiva porque estás perdiendo dinero con cada venta.")
    st.stop()

# Cálculos de Punto de Equilibrio
punto_equilibrio_exacto = costos_fijos / margen_contribucion_neto
unidades_equilibrio = int(punto_equilibrio_exacto) + 1
ingresos_equilibrio_bruto = punto_equilibrio_exacto * precio_venta

# Cálculos de Meta de Ganancias
unidades_meta_exactas = (costos_fijos + meta_ganancia) / margen_contribucion_neto
unidades_meta = int(unidades_meta_exactas) + 1
ingresos_meta_bruto = unidades_meta_exactas * precio_venta

# --- MÉTRICAS CLAVE (KPIs) ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="🎯 Unidades para Punto de Equilibrio", 
        value=f"{unidades_equilibrio} u",
        help="Cantidad de unidades a vender para cubrir costos fijos, variables e impuestos sin perder dinero."
    )

with col2:
    st.metric(
        label="🏆 Unidades para Alcanzar Meta", 
        value=f"{unidades_meta} u",
        help=f"Cantidad de unidades necesarias para cubrir la estructura de costos y además ganar ${meta_ganancia:,.2f} limpios."
    )

with col3:
    st.metric(
        label="💰 Facturación Bruta Requerida (Meta)", 
        value=f"${ingresos_meta_bruto:,.2f}",
        help="Caja total que debe ingresar a tu negocio (incluyendo el IVA recaudado) para lograr tu objetivo."
    )

st.divider()

# --- GENERACIÓN DE DATOS PARA EL GRÁFICO ---
max_unidades = max(int(unidades_meta_exactas * 1.5), 10)
unidades_seq = list(range(0, max_unidades + 1))

ingresos_brutos = [u * precio_venta for u in unidades_seq]
impuestos_totales = [u * impuesto_por_unidad for u in unidades_seq]
costos_variables_totales = [u * costo_variable for u in unidades_seq]
costos_totales_con_impuestos = [costos_fijos + cv + imp for cv, imp in zip(costos_variables_totales, impuestos_totales)]
utilidad_neta = [ing - c_tot for ing, c_tot in zip(ingresos_brutos, costos_totales_con_impuestos)]

df = pd.DataFrame({
    'Unidades': unidades_seq,
    'Ingresos Brutos ($)': ingresos_brutos,
    'Costos Fijos ($)': [costos_fijos] * len(unidades_seq),
    'Costos Variables ($)': costos_variables_totales,
    'Impuestos Recaudados ($)': impuestos_totales,
    'Costos Totales + Impuestos ($)': costos_totales_con_impuestos,
    'Utilidad Neta ($)': utilidad_neta
})

# --- SECCIÓN DE GRÁFICOS CON PESTAÑAS (TABS) ---
tab1, tab2 = st.tabs(["📈 Análisis Clínico del Punto de Equilibrio", "📊 Desglose Visual de Costos"])

with tab1:
    fig1 = go.Figure()
    
    # Líneas tradicionales
    fig1.add_trace(go.Scatter(x=df['Unidades'], y=df['Costos Fijos ($)'], mode='lines', name='Costos Fijos', line=dict(color='orange', dash='dash')))
    fig1.add_trace(go.Scatter(x=df['Unidades'], y=df['Costos Totales + Impuestos ($)'], mode='lines', name='Costos Totales + Impuestos', line=dict(color='red')))
    fig1.add_trace(go.Scatter(x=df['Unidades'], y=df['Ingresos Brutos ($)'], mode='lines', name='Ingresos Brutos', line=dict(color='green')))
    
    # Marcador Punto de Equilibrio
    fig1.add_trace(go.Scatter(
        x=[punto_equilibrio_exacto], y=[ingresos_equilibrio_bruto], mode='markers+text', name='Punto de Equilibrio',
        text=[f" PE ({punto_equilibrio_exacto:.1f} u)"], textposition="top left", marker=dict(color='black', size=12, symbol='x')
    ))
    
    # Marcador Meta de Ganancia
    fig1.add_trace(go.Scatter(
        x=[unidades_meta_exactas], y=[ingresos_meta_bruto], mode='markers+text', name='Meta Deseada',
        text=[f" Meta ({unidades_meta_exactas:.1f} u)"], textposition="top left", marker=dict(color='gold', size=12, symbol='star')
    ))

    fig1.update_layout(title="Líneas de Equilibrio y Cumplimiento de Metas", xaxis_title="Unidades Vendidas", yaxis_title="Dinero ($)", hovermode="x unified", height=500)
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    fig2 = go.Figure()
    
    # Barras apiladas para auditar costos de forma clara
    fig2.add_trace(go.Bar(x=df['Unidades'], y=df['Costos Fijos ($)'], name='Costos Fijos', marker_color='orange'))
    fig2.add_trace(go.Bar(x=df['Unidades'], y=df['Costos Variables ($)'], name='Costos Variables', marker_color='firebrick'))
    fig2.add_trace(go.Bar(x=df['Unidades'], y=df['Impuestos Recaudados ($)'], name='Impuestos Recaudados', marker_color='crimson'))

    fig2.update_layout(barmode='stack', title="Composición Estructural de los Egresos por Volumen de Venta", xaxis_title="Unidades Vendidas", yaxis_title="Egresos Acumulados ($)", height=500)
    st.plotly_chart(fig2, use_container_width=True)

# --- BOTONES DE EXPORTACIÓN Y TABLA ---
st.subheader("📋 Datos del Escenario y Exportación")

csv_data = df.to_csv(index=False).encode('utf-8')
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    df.to_excel(writer, index=False, sheet_name='Proyecciones')
excel_data = buffer.getvalue()

col_btn1, col_btn2, _ = st.columns([1, 1, 4])
with col_btn1:
    st.download_button(label="📥 Descargar CSV", data=csv_data, file_name="proyecciones_punto_equilibrio.csv", mime="text/csv")
with col_btn2:
    st.download_button(label="📥 Descargar Excel", data=excel_data, file_name="proyecciones_punto_equilibrio.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.dataframe(
    df.style.format({
        'Ingresos Brutos ($)': '${:,.2f}', 'Costos Fijos ($)': '${:,.2f}', 'Costos Variables ($)': '${:,.2f}',
        'Impuestos Recaudados ($)': '${:,.2f}', 'Costos Totales + Impuestos ($)': '${:,.2f}', 'Utilidad Neta ($)': '${:,.2f}'
    }), use_container_width=True
)
