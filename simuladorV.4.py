import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import io

# Configuración de la página web
st.set_page_config(page_title="Simulador Financiero Corporativo", layout="wide", page_icon="🏦")

# --- INICIALIZACIÓN DE LA MEMORIA DE SESIÓN (HISTORIAL) ---
if 'historial_simulaciones' not in st.session_state:
    st.session_state['historial_simulaciones'] = {}

# Título y descripción
st.title("🏦 Simulador Financiero Corporativo: Multi-Producto y Escenarios")
st.markdown("Herramienta avanzada para calcular el punto de equilibrio ponderado, proyectar escenarios de sensibilidad y comparar configuraciones de negocio.")

st.divider()

# --- BARRA LATERAL: ENTRADA DE DATOS GLOBALES ---
st.sidebar.header("⚙️ Costos Fijos y Metas")
costos_fijos = st.sidebar.number_input(
    "Costos Fijos Totales ($)", 
    min_value=0.0, value=2000.0, step=100.0,
    help="Gastos fijos de la empresa (Alquiler, sueldos base, infraestructura)."
)

meta_ganancia = st.sidebar.number_input(
    "Meta de Ganancia Neta ($)", 
    min_value=0.0, value=1500.0, step=100.0,
    help="Utilidad mensual neta que deseás obtener."
)

porcentaje_impuesto = st.sidebar.number_input(
    "Impuesto / IVA (%)", 
    min_value=0.0, max_value=100.0, value=21.0, step=0.5,
    help="Carga impositiva uniforme aplicada sobre las ventas de todos los productos."
)

# --- CONFIGURACIÓN DE MULTI-PRODUCTOS (MEZCLA DE VENTAS) ---
st.subheader("📦 Configuración de Productos (Mezcla de Ventas)")
st.caption("Definí el precio, costo variable y la proporción de ventas correspondiente a cada producto. La suma del Share de Ventas debe dar exactamente 100%.")

# Base de datos inicial de productos en memoria para la edición
if 'df_productos' not in st.session_state:
    st.session_state.df_productos = pd.DataFrame([
        {"Producto": "Producto Premium", "Precio Venta ($)": 150.0, "Costo Variable ($)": 60.0, "Share de Ventas (%)": 30.0},
        {"Producto": "Producto Estándar", "Precio Venta ($)": 80.0, "Costo Variable ($)": 30.0, "Share de Ventas (%)": 50.0},
        {"Producto": "Producto Económico", "Precio Venta ($)": 40.0, "Costo Variable ($)": 20.0, "Share de Ventas (%)": 20.0}
    ])

# Editor de tabla interactivo
df_editado = st.data_editor(
    st.session_state.df_productos, 
    num_rows="dynamic", 
    use_container_width=True,
    key="editor_tabla_productos"
)

# Validaciones críticas de la mezcla de ventas
total_share = df_editado["Share de Ventas (%)"].sum()
if abs(total_share - 100.0) > 0.01:
    st.warning(f"⚠️ La suma del Share de Ventas actual es **{total_share:.1f}%**. Debe ser exactamente **100%** para procesar los cálculos.")
    st.stop()

# --- CÁLCULOS INTEGRADOS DE LA MEZCLA DE VENTAS ---
df_editado["Margen Bruto ($)"] = df_editado["Precio Venta ($)"] - df_editado["Costo Variable ($)"]
df_editado["Impuesto ($)"] = df_editado["Precio Venta ($)"] * (porcentaje_impuesto / 100.0)
df_editado["Margen Neto ($)"] = df_editado["Margen Bruto ($)"] - df_editado["Impuesto ($)"]

# Verificar si algún producto destruye valor
if (df_editado["Margen Neto ($)"] <= 0).any():
    st.error("⚠️ Uno o más productos tienen un margen neto menor o igual a cero con la carga impositiva. Ajustá sus precios o costos.")
    st.stop()

# Ponderación matemática según el Share de Ventas
df_editado["Share Decimal"] = df_editado["Share de Ventas (%)"] / 100.0
margen_neto_ponderado = (df_editado["Margen Neto ($)"] * df_editado["Share Decimal"]).sum()
precio_ponderado = (df_editado["Precio Venta ($)"] * df_editado["Share Decimal"]).sum()

# Cálculo del Punto de Equilibrio de la Empresa (Global)
pe_unidades_global = costos_fijos / margen_neto_ponderado
meta_unidades_global = (costos_fijos + meta_ganancia) / margen_neto_ponderado

# --- SECCIÓN DE GUARDADO Y COMPARACIÓN ---
st.sidebar.divider()
st.sidebar.header("💾 Guardar Escenario Actual")
nombre_simulacion = st.sidebar.text_input("Nombre de la simulación", value="Simulación Alfa")

if st.sidebar.button("💾 Guardar Configuración"):
    st.session_state['historial_simulaciones'][nombre_simulacion] = {
        "costos_fijos": costos_fijos,
        "meta_ganancia": meta_ganancia,
        "pe_unidades": pe_unidades_global,
        "meta_unidades": meta_unidades_global,
        "precio_ponderado": precio_ponderado,
        "tabla": df_editado.copy()
    }
    st.sidebar.success(f"¡'{nombre_simulacion}' guardado!")

if st.session_state['historial_simulaciones']:
    st.sidebar.subheader("🔄 Comparador Rápido")
    seleccionados = st.sidebar.multiselect(
        "Elegí escenarios para comparar:", 
        options=list(st.session_state['historial_simulaciones'].keys())
    )
    if seleccionados:
        datos_comp = []
        for s in seleccionados:
            sc = st.session_state['historial_simulaciones'][s]
            datos_comp.append({
                "Escenario": s,
                "Costos Fijos": f"${sc['costos_fijos']:,.2f}",
                "Meta Ganancia": f"${sc['meta_ganancia']:,.2f}",
                "PE Total (u)": f"{int(sc['pe_unidades'])+1} u",
                "Meta Total (u)": f"{int(sc['meta_unidades'])+1} u"
            })
        st.sidebar.dataframe(pd.DataFrame(datos_comp), hide_index=True)

# --- ANÁLISIS DE SENSIBILIDAD AUTOMÁTICO ---
st.divider()
st.subheader("⚡ Análisis de Sensibilidad Automático (Impacto en Volumen)")

# Definición de factores de estrés de escenarios corporativos
escenarios = {
    "📉 Pesimista (-15% precio, +10% costos fijos)": {"fact_precio": 0.85, "fact_cf": 1.10},
    "⚖️ Esperado (Base Actual)": {"fact_precio": 1.00, "fact_cf": 1.00},
    "📈 Optimista (+10% precio, -5% costos fijos)": {"fact_precio": 1.10, "fact_cf": 0.95}
}

filas_sensibilidad = []
for nom, variables in escenarios.items():
    cf_stresado = costos_fijos * variables["fact_cf"]
    
    # Recalcular márgenes con precios alterados por el escenario
    precios_alt = df_editado["Precio Venta ($)"] * variables["fact_precio"]
    impuestos_alt = precios_alt * (porcentaje_impuesto / 100.0)
    margen_neto_alt = precios_alt - df_editado["Costo Variable ($)"] - impuestos_alt
    margen_ponderado_alt = (margen_neto_alt * df_editado["Share Decimal"]).sum()
    
    if margen_ponderado_alt > 0:
        pe_u = cf_stresado / margen_ponderado_alt
        meta_u = (cf_stresado + meta_ganancia) / margen_ponderado_alt
        fact_equilibrio = pe_u * (precios_alt * df_editado["Share Decimal"]).sum()
    else:
        pe_u = meta_u = fact_equilibrio = float('inf')
        
    filas_sensibilidad.append({
        "Escenario": nom,
        "Costos Fijos Ajustados": cf_stresado,
        "PE Global Mínimo": int(pe_u) + 1 if pe_u != float('inf') else "Inviable",
        "Ventas para Meta": int(meta_u) + 1 if meta_u != float('inf') else "Inviable",
        "Facturación de Equilibrio": fact_equilibrio
    })

df_sensibilidad = pd.DataFrame(filas_sensibilidad)

# Render de la tabla de sensibilidad analítica
st.dataframe(
    df_sensibilidad.style.format({
        "Costos Fijos Ajustados": "${:,.2f}",
        "Facturación de Equilibrio": "${:,.2f}"
    }),
    use_container_width=True,
    hide_index=True
)

# --- DESGLOSE DE DISTRIBUCIÓN ESPECÍFICA ---
st.divider()
st.subheader("📊 Distribución Comercial en Punto de Equilibrio Real")
st.markdown("Unidades exactas de **cada producto** que componen tu mix comercial para cubrir costos:")

col_kpis = st.columns(len(df_editado))
for idx, row in df_editado.iterrows():
    u_prod_pe = (pe_unidades_global * row["Share Decimal"])
    u_prod_meta = (meta_unidades_global * row["Share Decimal"])
    with col_kpis[idx]:
        st.markdown(f"### 📦 {row['Producto']}")
        st.metric("Punto de Equilibrio", f"{int(u_prod_pe) + 1} unidades")
        st.metric("Volumen Objetivo (Meta)", f"{int(u_prod_meta) + 1} unidades")

# --- RENDERS GRÁFICOS DINÁMICOS ---
st.divider()
tab1, tab2 = st.tabs(["📈 Curva de Operación Mix Comercial", "📊 Desglose de Egresos por Escenario"])

# Construcción de rangos de simulación comercial
max_unidades_grafico = max(int(meta_unidades_global * 1.5), 10)
unidades_seq = list(range(0, max_unidades_grafico + 1))

ingresos_mix = [u * precio_ponderado for u in unidades_seq]
costos_mix = [costos_fijos + (u * (df_editado["Costo Variable ($)"] * df_editado["Share Decimal"]).sum()) + (u * (df_editado["Impuesto ($)"] * df_editado["Share Decimal"]).sum()) for u in unidades_seq]
utilidades_mix = [ing - cos for ing, cos in zip(ingresos_mix, costos_mix)]

with tab1:
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=unidades_seq, y=[costos_fijos]*len(unidades_seq), mode='lines', name='Costos Fijos Corporativos', line=dict(color='orange', dash='dash')))
    fig1.add_trace(go.Scatter(x=unidades_seq, y=costos_mix, mode='lines', name='Costos Totales + Impuestos', line=dict(color='red')))
    fig1.add_trace(go.Scatter(x=unidades_seq, y=ingresos_mix, mode='lines', name='Ingresos Totales Combinados', line=dict(color='green')))
    
    fig1.add_trace(go.Scatter(x=[pe_unidades_global], y=[pe_unidades_global * precio_ponderado], mode='markers+text', name='PE Global', text=[f" PE ({pe_unidades_global:.1f} u)"], textposition="top left", marker=dict(color='black', size=12, symbol='x')))
    fig1.add_trace(go.Scatter(x=[meta_unidades_global], y=[meta_unidades_global * precio_ponderado], mode='markers+text', name='Meta de Negocio', text=[f" Meta ({meta_unidades_global:.1f} u)"], textposition="top left", marker=dict(color='gold', size=12, symbol='star')))
    
    fig1.update_layout(title="Curva de Equilibrio Basada en Margen Ponderado", xaxis_title="Unidades Totales del Mix", yaxis_title="Dinero ($)", hovermode="x unified", height=500)
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=df_sensibilidad["Escenario"], y=df_sensibilidad["Costos Fijos Ajustados"], name="Costos Fijos Estresados", marker_color='orange'))
