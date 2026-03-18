import streamlit as st
import pandas as pd
import plotly.express as px

# App de manejo de presupuesto e ingreso

# Configuracion inicial

st.set_page_config(page_title="Presupuesto e Ingreso", page_icon="💰", layout="wide")

# iniciamos memoria
if 'vista' not in st.session_state:
    st.session_state.vista = 'carga'

if 'df_limpio' not in st.session_state:
    st.session_state.df_limpio = None

# Funciones para cambiar de pantalla
def ir_al_tablero():
    st.session_state.vista = 'tablero'

def volver_a_carga():
    st.session_state.vista = 'carga'


# ==========================================
# PANTALLA 1: CARGA DE DATOS
# ==========================================
if st.session_state.vista == 'carga':
    st.title("📊 Control de Presupuesto e Ingresos")
    
    # --- DESCRIPCIÓN PRINCIPAL ---
    st.markdown("""
    Bienvenido a tu herramienta de análisis financiero. 
    
    Este tablero interactivo te permite:
    * 📈 **Monitorear** la evolución de tus ingresos frente a tu presupuesto.
    * 🎯 **Medir** el % de cumplimiento de tus metas financieras.
    * 📊 **Analizar** la distribución de tus ingresos por categoría con gráficos dinámicos.
    
    Para comenzar a explorar tu tablero, sube tu base de datos a continuación.
    """)
    
    st.info("💡 **Formato requerido:** Tu archivo CSV debe contener exactamente estas columnas: `id`, `category`, `descripcion`, `income`, `budget`, `date`.")
    st.write("---") 
    # ------------------------------

    # Carga de datos
    file = st.file_uploader("Sube tu archivo CSV con tus ingresos y gastos", type=["csv"])

    if file is not None:
        df = pd.read_csv(file)

        # columnas que esperas
        columnas_requeridas = ['id', 'category', 'descripcion', 'income', 'budget', 'date']

        # Validar que todas las columnas requeridas estén
        if set(columnas_requeridas).issubset(df.columns):
            st.success("¡Carga exitosa!")

            # 1. Limpiar el texto y convertir a número (float)
            columnas_moneda = ['income', 'budget']

            for col in columnas_moneda:
                df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).astype(float)

            df['date'] = pd.to_datetime(df['date'])

            # guardar dataset limpio
            st.session_state.df_limpio = df
                

            st.write("Vista previa de los datos:")
            st.dataframe(df.head())

            # Botón que cambia el estado para ir al tablero
            st.button("Siguiente: Ir al Tablero ➡️", on_click=ir_al_tablero, type="primary")


        else:
            st.error("El archivo debe contener estas columnas: id, category, descripcion, income, budget, date.")
    else:
        st.warning("Por favor, sube un archivo CSV para continuar.")

# ==========================================
# PANTALLA 2: TABLERO PRINCIPAL
# ==========================================

elif st.session_state.vista == 'tablero':

    # Botón para regresar
    st.button("⬅️ Volver a cargar datos", on_click=volver_a_carga)

    # Recuperamos los datos de la memoria
    df = st.session_state.df_limpio

    # Filtros laterales
    st.sidebar.header("Filtros")

    fecha_min = df['date'].min().date()
    fecha_max = df['date'].max().date()

    # Borrar la memoria del calendario
    def limpiar_fechas():

        # df original
        df_temp = st.session_state.df_limpio
        f_min = df_temp['date'].min().date()
        f_max = df_temp['date'].max().date()
        
        # En lugar de borrar la llave, la sobrescribimos con el rango completo
        st.session_state['calendario_key'] = (f_min, f_max)

    # botón encima del filtro para borrar
    st.sidebar.button("🔄 Restablecer fechas", on_click=limpiar_fechas)
    date_filter = st.sidebar.date_input(
        "Selecciona rango de fechas", 
        value=[fecha_min, fecha_max], 
        min_value=fecha_min, 
        max_value=fecha_max,
        key='calendario_key'
    )

    # Aplicar filtros fecha
    df_filtrado = df.copy()
    if len(date_filter) == 2:
        df_filtrado = df_filtrado[(df_filtrado['date'].dt.date >= date_filter[0]) & (df_filtrado['date'].dt.date <= date_filter[1])]

    # filtro categoria
    category_filter = st.sidebar.multiselect("Selecciona categorías",  list(df_filtrado['category'].unique()))
    if category_filter:
        df_filtrado = df_filtrado[df_filtrado['category'].isin(category_filter)]

    # --- MÉTRICAS PRINCIPALES (KPIs) ---
    st.subheader("Resumen de KPIs")
    
    # Cálculos base
    ingreso_total = df_filtrado['income'].sum()
    presupuesto_total = df_filtrado['budget'].sum()
    
    # cumplimiento
    if presupuesto_total > 0:
        cumplimiento_pct = (ingreso_total / presupuesto_total) * 100
    else:
        cumplimiento_pct = 0.0
        
    diferencia = ingreso_total - presupuesto_total
    
    # Cálculo de la Categoría Top
    if not df_filtrado.empty and ingreso_total > 0:
        categoria_top = df_filtrado.groupby('category')['income'].sum().idxmax()
        texto_top = f"{categoria_top}"
    else:
        texto_top = "Sin datos"

    # Renderizado de las 4 tarjetas
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Presupuesto", f"${presupuesto_total:,.0f}")
    col2.metric("Ingreso Total", f"${ingreso_total:,.0f}")
    
    # El parametro delta para mostrar flecha
    col3.metric(
        label="Cumplimiento", 
        value=f"{cumplimiento_pct:,.0f}%", 
        delta=f"${diferencia:,.0f}" 
    )
    
    col4.metric("Categoría Top (Ingresos)", texto_top)
    
    st.divider()

# --- VISUALIZACIÓN Y GRÁFICOS ---
    # st.header("Análisis Visual")

    col_graf_pie, col_graf_line = st.columns(2, gap="large")

    with col_graf_pie:
        st.subheader("Distribución de Ingresos")
        
        #Agrupacion y orden
        df_pie = df_filtrado.groupby('category')['income'].sum().reset_index()
        df_pie = df_pie.sort_values(by='income', ascending=False)
        

        if df_pie['income'].sum() > 0:
            
            # control interactivo para topN
            max_cat = len(df_pie)
            if max_cat > 1:
                top_n = st.slider("Mostrar Top N categorías:", min_value=1, max_value=max_cat, value=min(4, max_cat))
                
                # Seleccion primeras 'N' filas
                df_top = df_pie.iloc[:top_n].copy()
                
                # Seleccio resto de las filas
                df_resto = df_pie.iloc[top_n:]
                
                # Si hay filas restantes, sumar en una sola categoría "Otras"
                if not df_resto.empty:
                    suma_otras = df_resto['income'].sum()
                    fila_otras = pd.DataFrame([{'category': 'Otras', 'income': suma_otras}])
                    df_pie_final = pd.concat([df_top, fila_otras], ignore_index=True)
                else:
                    df_pie_final = df_top
            else:
                # Si solo hay 1 categoría mostrar tal cual
                df_pie_final = df_pie

            # graficar
            fig_pie = px.pie(
                df_pie_final, 
                values='income', 
                names='category',
                hole=0.4
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)

        else:
            st.info("No hay ingresos en el rango seleccionado para mostrar el gráfico.")

    with col_graf_line:
    # 1. Grafico de lineas
        st.subheader("Evolución en el tiempo")
        df_evolucion = df_filtrado.groupby('date')[['income', 'budget']].sum()
        st.line_chart(df_evolucion)


# --- TABLA DE DETALLES
    st.divider()
    
    # menu desplegable
    with st.expander("📄 Ver detalle de los registros"):
        st.write("Aquí puedes explorar todos los datos filtrados fila por fila:")
        
        st.dataframe(df_filtrado, use_container_width=True)

