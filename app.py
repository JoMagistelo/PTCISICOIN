import streamlit as st
import pandas as pd
import plotly.express as px
import gdown
import numpy as np

#================================================== CONFIGURACIÓN INICIAL DE LA PÁGINA ======================================================================================
st.set_page_config(page_title="Sistema Control Interno", layout="wide", page_icon="📊")


###########################################################
###########################################################
###########################################################
# DESCARGA Y CONSOLIDACIÓN DE INFORMACIÓN PARA LA APP
###########################################################
###########################################################
###########################################################



#==================================== DESCARGA ARCHIVOS A PARTIR DE LOS LINKS DE GOOGLE DRIVE ================================================
ARCHIVOS = {
    "PTAR.xlsx": "1U2vlwj4cVRiMUc9v9WECXZQ1cYVby0mr",      # PTAR BASE
    "ACTRI.xlsx": "1Ix69LpGafKmqfmePZaaWcQ9dsmURiRfT",     # ACTRI BASE
    "PTCI.xlsx": "1FTsOOyJqIYZf-6n6Mz0yPbPW49IM5aup",      # PTCI BASE
    "AMTRI.xlsx": "1fRoHNDgNYMyckXaKidVcRcpD9LAymX3-"      # AMTRI BASE
}


#============================================ CACHEADA PARA DESCARGA Y CARGA DE DATOS================================================
@st.cache_resource(ttl="1h", show_spinner="Descargando datos actualizados...")  # <--- MAGIA AQUÍ
def descargar_y_cargar_datos():
    # Descarga archivos desde Google Drive
    for nombre_archivo, id in ARCHIVOS.items():
        gdown.download(f"https://drive.google.com/uc?id={id}", nombre_archivo, quiet=True)

    # Carga los DataFrames
    return {
        "PTAR": pd.read_excel("PTAR.xlsx"),
        "ACTRI": pd.read_excel("ACTRI.xlsx"),
        "PTCI": pd.read_excel("PTCI.xlsx"),
        "AMTRI": pd.read_excel("AMTRI.xlsx")
    }


#================================================== CACHEADA PARA LIMPIEZA DE DATOS ===========================================================================================
@st.cache_data(show_spinner=False)  # <--- Optimización adicional
def limpiar_datos(df):
    df.columns = df.columns.str.strip()                                          # Normaliza nombres de las columnas
    if 'Año' in df.columns:
        df = df[df['Año'] != 'Año']                                              # Elimina filas duplicadas con encabezados
        df['Año'] = pd.to_numeric(df['Año'], errors='coerce')                    # Normaliza Año y convierte a Número
    if 'Institución' in df.columns:
        df['Institución'] = df['Institución'].astype(str).str.strip()            # Normaliza Institución y convierte a Texto
    if 'Sector' in df.columns:
        df['Sector'] = df['Sector'].astype(str).str.strip()                      # Normaliza Institución y convierte a Texto
    return df


#================================================== CARGA PRINCIPAL DE LOS DATOS EN LA APP ======================================================================================
try:
    # Paso 1: Descarga y carga de datos (solo en primer uso)
    datos_crudos = descargar_y_cargar_datos()  # <--- Aquí se descargan los archivos

    # Paso 2: Limpieza de datos
    datos_limpios = {nombre: limpiar_datos(df) for nombre, df in datos_crudos.items()}

    # Asignación a variables
    df1 = datos_limpios["PTAR"]
    df2 = datos_limpios["ACTRI"]
    df3 = datos_limpios["PTCI"]
    df4 = datos_limpios["AMTRI"]

except Exception as e:
    st.error(f"Error crítico: {str(e)}")
    st.stop()
#=======================================FIN DE LA DESCARGA Y CONSOLIDACIÓN DE INFORMACIÓN PARA LA APP ======================================================================================
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





###########################################################
###########################################################
###########################################################
# CABECERA DE LA APP Y CONFIGURACIÓN DE FILTROS PRINCIPALES
###########################################################
###########################################################
###########################################################





#============================================ CABECERA ESTÁTICA CON LOS TÍTULOS PRINCIPALES ======================================================================================
st.markdown("""
<div style='background-color:#621132; padding:30px; border-radius:8px; margin-bottom:20px;'>
  <h1 style='text-align:center; color:white; margin:0; font-size:28px;'>SISTEMA DE CONTROL INTERNO INSTITUCIONAL 2025</h1>
  <h3 style='text-align:center; color:white; margin:0; margin-top:10px; font-size:20px;'>RIESGOS Y AVANCE DE LAS ACCIONES DE CONTROL</h3>
</div>
""", unsafe_allow_html=True)


#====================================== LISTAS DE FILTROS PARTE 1 - PRE CÁLCULO PARA OPTIMIZAR RENDIMIENTO ==============================================
@st.cache_data(show_spinner=False)
def precompute_filter_lists(df):
    # Lista de instituciones y sectores
    inst_list = sorted(df['Institución'].dropna().unique().tolist())
    sector_list = sorted(df['Sector'].dropna().unique().tolist())

    # Precomputar años disponibles por institución
    years_by_institucion = {}
    for inst in inst_list:
        years = sorted(df[df['Institución'] == inst]['Año'].dropna().unique().tolist())
        years_by_institucion[inst] = years

    # Precomputar años disponibles por sector
    years_by_sector = {}
    for sec in sector_list:
        years = sorted(df[df['Sector'] == sec]['Año'].dropna().unique().tolist())
        years_by_sector[sec] = years

    return inst_list, sector_list, years_by_institucion, years_by_sector

#===================================== LISTAS DE FILTROS PARTE 2 - OBTENCIÓN DE LISTA DE FILTROS PRECOMPUTADAS ==============================================
inst_list, sector_list, years_by_inst, years_by_sector = precompute_filter_lists(df1)  # Obtener listas de filtros precomputadas (se calcula una única vez por sesión)

# Callback para reiniciar sector a "Todas" al cambiar la institución
def reset_sector():
    st.session_state['sector'] = "Todas"

col1, col2, col3 = st.columns(3)  # Guardar filtros
with col1:
    institucion = st.selectbox("Seleccione la Institución", inst_list, key="institucion", on_change=reset_sector)
with col2:
    sector = st.selectbox("Seleccione el Sector", ["Todas"] + sector_list, key="sector")
with col3:
    # Se seleccionan los años basados en la opción de sector o institución
    if sector != "Todas":
        available_years = years_by_sector.get(sector, [])
    else:
        available_years = years_by_inst.get(institucion, [])
    year = st.selectbox("Seleccione el Año", available_years)



#======================================= FIN DE LA CABECERA DE LA APP Y CONFIGURACIÓN DE FILTROS PRINCIPALES =========================================================
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



###########################################################
###########################################################
###########################################################
# 1. PESTAÑA PTAR
###########################################################
###########################################################
###########################################################



#====================================== PREPARACIÓN DE DATOS ANTES DE MOSTRAR RESULTADOS EN LA PESTAÑA PTAR =====================================================================
#------------------------------------------------------------------------------------------------------------------------------------------------------------------


#================================== SE OBTIENE UNA LISTA CON LOS NOMBRES DE LAS VARIABLES PARA EL REPORTE PTAR =====================================================
risk_cols = ['Sustantivo','Administrativo','Financiero','Presupuestal','Servicios', 'Seguridad','Obra_Pública','Recursos_Humanos','Imagen','TICs','Salud', 'Otro','Corrupción','Legal']
cuadrante_cols = ['I','II','III','IV']
estrategia_cols = ['Evitar','Reducir','Asumir','Transferir','Compartir']
estados = ['Sin_Avances', 'En_Proceso', 'Concluidas', 'Cumplimiento']
trimestres = ['1', '2', '3', '4']


#================================== FUNCIÓN PARA OBTENER INSTITUCION, SECTOR Y SIGLAS FILTRADOS (Header) ==============================================
#=================================== OBTIENE TAMBIÉN EL DATASET PARA LAS TABLAS SEGUN SEA EL CASO (data) ==============================================
#========================= OBTIENE TAMBIEN LOS INDICADORES PRINCIPALES DE ACCIONES DE CONTROL Y RIESGOS (Stats) ==============================================
#==================================== OBTIENE TAMBIEN LAS TABLAS: RIESGOS, CUADRANTE Y ESTRATEGIA ==============================================

def generate_dashboard(institucion, year, sector):
  #----- Parte 1 de la función: Calcula data para reportes -----#
    if sector != "Todas":                                       # -------------------- # Caso 1: Sector != "Todas"
        filtered = df1[(df1['Sector'] == sector) & (df1['Año'] == year)]               # Filtra PTAR o df1 por Sector y Año y lo guarda en filtered
        instituciones_list = "<ul style='margin:0; padding-left:20px;'>" + "".join(
          f"<li>{inst}</li>" for inst in filtered['Institución'].unique()) + "</ul>"   # Crea lista desordenada de HTML con las instituciones del sector seleccionado y los imprime
        header = f"""
        <div style='background-color:#f8f9fa; padding:15px; border-radius:10px; margin-bottom:20px; box-shadow:0 2px 4px rgba(0,0,0,0.1);'>
          <h3 style='color:#621132; margin:0; font-size:14px;'>
            Sector: {sector}<br>
            Instituciones: {instituciones_list}
          </h3>
        </div>
        """
                                                                                # COMENTARIO: VARIABLE CUMPLIMIENTO - Se guarda en data, el cumplimeinto promedio por trimestre del sector seleccionado para posterior uso
        data = filtered.sum(numeric_only=True).to_dict()                                # Obtiene los acumulados de filtered (dfi filtrada) y los guarda en data (acumulados por que es un sector) #serie a diccionario para posterior uso en reportes
        for t in trimestres:                                                            # En el Caso 1, el Cumplimiento por Sector se obtendrá en promedio- aqui recorre la lista de trimestres
            key = f"{t}Cumplimiento"                                                    # Se interpola la cadena del trimestre con % y se guarda en key
            if key in filtered.columns:                                                 # Revisa si existe Key (nCumplimiento) como columna en filtered (que es df1 filtrado por Sector y Año)
                avg_value = pd.to_numeric(filtered[key], errors='coerce').fillna(0).mean()  # Filtra key en filtered, convierte a número, cambia NaN por 0 y obtiene el promedio - finalmente guarda el dataframe
                data[key] = round(avg_value, 2)                                             # Guarda los promedios de Cumplimiento en data, con dos decimales

    else:                                                     # ------------------------ # Caso 2: sector = "Todas"    (Filtro por Institucipon y Año)
        filtered = df1[(df1['Institución'] == institucion) & (df1['Año'] == year)]       # En este caso se usa iloc[0] por que filtered nadamas tiene un registro (ya que se filtro por institución)
        header = f"""
        <div style='background-color:#f8f9fa; padding:15px; border-radius:10px; margin-bottom:20px; box-shadow:0 2px 4px rgba(0,0,0,0.1);'>
          <h3 style='color:#621132; margin:0; font-size:14px;'>
            Institución: {institucion}<br>
            Sector: {filtered['Sector'].iloc[0]}<br>
            Siglas: {filtered['Siglas'].iloc[0]}
          </h3>
        </div>
        """
        data = filtered.iloc[0].to_dict()     # Se obtiene un diccionario con los datos filtrados por Institucion y Año para los posteriores reportes

  #---- Parte 2 de la función: Se limpia el data obtenido - se cambian NaN por 0 -----#
    for key in data:
        if pd.isna(data[key]):
            data[key] = 0
        elif isinstance(data[key], (int, float)) and not str(key).endswith("Cumplimiento"):
            data[key] = int(round(data[key]))

  #---- Parte 3 de la función: Obtenido data, se obtienen los indicadores principales de la pestaña PTAR - Total de AC_Total y Riesgos ----#
    stats = f"""
    <div style='background-color:#f8f9fa; padding:20px; border-radius:10px; margin-bottom:20px; box-shadow:0 2px 4px rgba(0,0,0,0.1);'>
      <h2 style='text-align:center; color:#2e86c1; margin:0;'>
        Total de Acciones de Control: <span style='color:#621132;'>{data['AC_Total']}</span><br>
        Total de Riesgos: <span style='color:#621132;'>{data['Riesgos_Totales']}</span>
      </h2>
    </div>
    """

  #---- Parte 4 de la función: Obtención de tablas principales ----#

                             # ------------------------ Tabla de Clasificación de Riesgos ------------------------- #
    risk_html = """
    <div style='overflow-x:auto; margin-bottom:20px;'>
      <table style='width:100%; border-collapse:collapse;'>
        <tr style='background-color:#621132; color:white;'>
    """
    for col in risk_cols:
        risk_html += f"<th style='padding:12px; text-align:center; border:1px solid #ddd;'>{col}</th>"    # Titulos de la tabla
    risk_html += "</tr><tr>"
    for col in risk_cols:                                                                                 # Valores de la tabla
        risk_html += f"<td style='padding:12px; text-align:center; border:1px solid #ddd; font-weight:500;'>{data[col]}</td>"
    risk_html += "</tr></table></div>"

                             # ------------------------------- Tabla de Cuadrante ---------------------------------- #
    cuadrante_html = """
    <div style='overflow-x:auto; margin-bottom:20px;'>
      <table style='width:100%; border-collapse:collapse;'>
        <tr style='background-color:#621132; color:white;'>
    """
    colors = ['#dc3545', '#ffc107', '#28a745', '#007bff']                                                                              # Guarda los colores de cada riesgo
    for col, color in zip(cuadrante_cols, colors):
        cuadrante_html += f"<th style='background-color:{color}; padding:12px; text-align:center; border:1px solid #ddd;'>{col}</th>"
    cuadrante_html += "</tr><tr>"
    for col in cuadrante_cols:
        cuadrante_html += f"<td style='padding:12px; text-align:center; border:1px solid #ddd; font-weight:500;'>{data[col]}</td>"
    cuadrante_html += "</tr></table></div>"

                             # ------------------------------- Tabla de Estrategia ---------------------------------- #
    estrategia_html = """
    <div style='overflow-x:auto; margin-bottom:20px;'>
      <table style='width:100%; border-collapse:collapse;'>
        <tr style='background-color:#621132; color:white;'>
    """
    for col in estrategia_cols:
        estrategia_html += f"<th style='padding:12px; text-align:center; border:1px solid #ddd;'>{col}</th>"
    estrategia_html += "</tr><tr>"
    for col in estrategia_cols:
        estrategia_html += f"<td style='padding:12px; text-align:center; border:1px solid #ddd; font-weight:500;'>{data[col]}</td>"
    estrategia_html += "</tr></table></div>"

  #---- Parte 5 de la función (Final): Retorna resultados ----#
    return header, stats, risk_html, cuadrante_html, estrategia_html, data
#============================================================== FIN DE LA FUNCIÓN =======================================================================



#============================================== DESEMPAQUETADO DE VALORES QUE DEVUELVE LA FUNCIÓN ==============================================
header, stats, risk_html, cuadrante_html, estrategia_html, data = generate_dashboard(institucion, year, sector)


#================================== MOSTRAR INSTITUCIONES, SIGLAS Y  SECTOR FILTRADOS (Header) ==============================================
st.markdown(header, unsafe_allow_html=True)                                                     #Se muestran fuera de las pestañas pues son datos globales
#--------------------------------------------------------------------------------------------------------------------------------------------------

#================================================== CREACIÓN DE PESTAÑAS PTAR, PTCI Y REPORTES =========================================================
tabs = st.tabs(["PTAR", "PTCI", "REPORTES"])


#===================================================== MOSTRAR RESULTADOS EN LA PESTAÑA PTAR ==============================================
#===================================================== MOSTRAR RESULTADOS EN LA PESTAÑA PTAR ==============================================
#===================================================== MOSTRAR RESULTADOS EN LA PESTAÑA PTAR ==============================================

#---- Pestaña PTAR
with tabs[0]:

  #---- Parte 1 del with: Se muestran los Indicadores Principales (Stats) ----#
    st.markdown(stats, unsafe_allow_html=True)


#============================================= SE ABRE LA SECCIÓN 1 - "Clasificación de Riesgos" ==============================================
#--------------------------------------------------------------------------------------------------------------------------------------------------
    st.markdown("""
      <div style='background-color:#621132; color:white; padding:10px; border-radius:5px; margin-bottom:20px; text-align:center;'>
        Clasificación de Riesgos
      </div>
    """, unsafe_allow_html=True)
                                        # ------ Se muestra la Tabla de Clasificación de Riesgos ----#
    st.markdown(risk_html, unsafe_allow_html=True)
    col1, col2 = st.columns(2)

                                #-------------- Se muestra la Tabla de Cuadrante (En columna 1) ------------#
    with col1:
        st.markdown("""
          <div style='background-color:#621132; color:white; padding:10px; border-radius:5px; margin-bottom:20px; text-align:center;'>
            Cuadrante
          </div>
        """, unsafe_allow_html=True)
        st.markdown(cuadrante_html, unsafe_allow_html=True)

                                #-------------- Se muestra la Tabla de Estrategia (En columna 2) ------------#
    with col2:
        st.markdown("""
          <div style='background-color:#621132; color:white; padding:10px; border-radius:5px; margin-bottom:20px; text-align:center;'>
            Estrategia
          </div>
        """, unsafe_allow_html=True)
        st.markdown(estrategia_html, unsafe_allow_html=True)



#====================================== SE ABRE LA SECCIÓN 2 - "Seguimiento de las Acciones de Control" ==============================================
#--------------------------------------------------------------------------------------------------------------------------------------------------
    st.markdown("""
      <div style='background-color:#621132; color:white; padding:10px; border-radius:5px; margin-bottom:20px; text-align:center;'>
        Seguimiento de las Acciones de Control
      </div>
    """, unsafe_allow_html=True)

                       #-------------- Parte 1: Se crea y muestra la Tabla para el estado de las Acciones de Control ------------#
    # (Se agregan "%" en Cumplimiento)
    st.markdown("""
      <div style='overflow-x:auto; margin-top:20px; margin-bottom:20px;'>
        <table style='width:100%; border-collapse:collapse;'>
          <tr style='background-color:#621132; color:white; text-align:center;'>
            <th>Estatdo de las Acciones de Control</th>
            <th>Primero</th>
            <th>Segundo</th>
            <th>Tercero</th>
            <th>Cuarto</th>
          </tr>
          <tr>
            <th style='background-color:#621132; color:white;'>Sin Avances</th>
            <td style='text-align:center; border:1px solid #ddd;'>{0}</td>
            <td style='text-align:center; border:1px solid #ddd;'>{1}</td>
            <td style='text-align:center; border:1px solid #ddd;'>{2}</td>
            <td style='text-align:center; border:1px solid #ddd;'>{3}</td>
          </tr>
          <tr>
            <th style='background-color:#621132; color:white;'>En Proceso</th>
            <td style='text-align:center; border:1px solid #ddd;'>{4}</td>
            <td style='text-align:center; border:1px solid #ddd;'>{5}</td>
            <td style='text-align:center; border:1px solid #ddd;'>{6}</td>
            <td style='text-align:center; border:1px solid #ddd;'>{7}</td>
          </tr>
          <tr>
            <th style='background-color:#621132; color:white;'>Concluidas</th>
            <td style='text-align:center; border:1px solid #ddd;'>{8}</td>
            <td style='text-align:center; border:1px solid #ddd;'>{9}</td>
            <td style='text-align:center; border:1px solid #ddd;'>{10}</td>
            <td style='text-align:center; border:1px solid #ddd;'>{11}</td>
          </tr>
          <tr>
            <th style='background-color:#621132; color:white;'>% de Cumplimiento</th>
            <td style='text-align:center; border:1px solid #ddd;'>{12}%</td>
            <td style='text-align:center; border:1px solid #ddd;'>{13}%</td>
            <td style='text-align:center; border:1px solid #ddd;'>{14}%</td>
            <td style='text-align:center; border:1px solid #ddd;'>{15}%</td>
          </tr>
        </table>
      </div>
    """.format(
      data.get("1Sin_Avances",0), data.get("2Sin_Avances",0), data.get("3Sin_Avances",0), data.get("4Sin_Avances",0),
      data.get("1En_Proceso",0), data.get("2En_Proceso",0), data.get("3En_Proceso",0), data.get("4En_Proceso",0),
      data.get("1Concluidas",0), data.get("2Concluidas",0), data.get("3Concluidas",0), data.get("4Concluidas",0),
      data.get("1Cumplimiento",0), data.get("2Cumplimiento",0), data.get("3Cumplimiento",0), data.get("4Cumplimiento",0)
    ), unsafe_allow_html=True)

                           #-------------- Parte 2: Se crea el gráfico de barras para el estado de las AC ------------#
           #----------------- Para ello primero crea lista de diccionarios que contenga los datos para el gráfico -----------------#

    plot_data = []
    for t in trimestres:
        for estado in estados:
            plot_data.append({'Trimestre': f' {t}', 'Estado': estado, 'Cantidad': data.get(f"{t}{estado}", 0)})

                #-------------- Convierte a dataframe la información obtenida y crea la gráfica (fig)  ------------------------#
    fig = px.bar(pd.DataFrame(plot_data), x='Trimestre', y='Cantidad', color='Estado',
                 barmode='group', height=400,
                 color_discrete_map={'Sin_Avances': '#dc3545', 'En_Proceso': '#ffc107',
                                     'Concluidas': '#28a745', 'Cumplimiento': '#6610f2'})

                                       #--------------  Da el formato a a la gráfica  ------------------#
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#333'),
        xaxis=dict(title=None, gridcolor='#f0f0f0'),
        yaxis=dict(title=None, gridcolor='#f0f0f0'),
        legend=dict(title=None),
        margin=dict(l=20, r=20, t=50, b=20)
    )
     #--------------  Agrega la etiqueta de porcentaje en las barras de Cumplimiento (ya que este valor es porcentaje) -----------------#
    for trace in fig.data:
        if trace.name == "Cumplimiento":
            trace.text = [f"{y}%" for y in trace.y]
            trace.textposition = 'outside'

                                #-------------- Muestra el gráfico de barras para el estado de las AC ------------#
    st.plotly_chart(fig, use_container_width=True)



#================================= SE ABRE LA SECCIÓN 3 - "Descripción de los Riesgos y las Acciones de Control" ==============================================
#--------------------------------------------------------------------------------------------------------------------------------------------------
    st.markdown("""
          <div style='background-color:#621132; color:white; padding:10px; border-radius:5px; margin-top:30px; margin-bottom:30px; text-align:center;'>
        Descripción de los Riesgos y las Acciones de Control
      </div>
    """, unsafe_allow_html=True)

                        #------------------ Para el contenido de esta sección se utilizará df2 (ACTRI) --------------#

                    #--------------Primero:  Se crea un dataframe (filtered_df2) según el filtro seleccionado ------------#
                    #---------------Esto se hace por que estamos usando otra base, pero con los mismos filtros ------------#

    if sector != "Todas":
        filtered_df2 = df2[(df2['Sector'] == sector) & (df2['Año'] == year)]
    else:
        filtered_df2 = df2[(df2['Institución'] == institucion) & (df2['Año'] == year)]


            #-------------- Segundo: Se verifica si (data['AC_Total']) coincide con el número de filas en filtered_df2 ------------#
    if int(data['AC_Total']) != len(filtered_df2):
        st.markdown("""
          <p style='color:red; font-weight:bold; text-align:center;'>
            Las acciones de control registradas en el PTAR no coinciden con las Acciones de Control Registradas
          </p>
        """, unsafe_allow_html=True)

                  #------------------ Tercero: Se crean los encabezados para la tabla principal de esta sección --------------#
    table_html = """
      <div style='overflow-x:auto;'>
        <table style='width:100%; border-collapse:collapse; margin-bottom:20px;'>
          <tr style='background-color:#621132; color:white;'>
            <th style='padding:12px; text-align:center; border:1px solid #ddd;'>Año</th>
            <th style='padding:12px; text-align:center; border:1px solid #ddd;'>Siglas</th>
            <th style='padding:12px; text-align:center; border:1px solid #ddd;'>Riesgo</th>
            <th style='padding:12px; text-align:center; border:1px solid #ddd;'>Descripción del Riesgo</th>
            <th style='padding:12px; text-align:center; border:1px solid #ddd;'>No. de AC</th>
            <th style='padding:12px; text-align:center; border:1px solid #ddd;'>Descripción</th>
            <th style='padding:12px; text-align:center; border:1px solid #ddd;'>Avance Institución</th>
            <th style='padding:12px; text-align:center; border:1px solid #ddd;'>Avance OIC</th>
          </tr>
    """

                               #------------------ Cuarto: Se llenan los datos de la tabla principal --------------#
        # Primero muestra los valores de Avance como porcentaje
    for _, row in filtered_df2.iterrows():
        avance_inst = f"{round(row['Avance_Institución'], 2)}%" if pd.notna(row['Avance_Institución']) else ""
        avance_oic = f"{round(row['Avance_OIC'], 2)}%" if pd.notna(row['Avance_OIC']) else ""
        # Crea la tabla de html con los datos correspondientes
        table_html += "<tr>"
        table_html += f"<td style='padding:12px; text-align:center; border:1px solid #ddd;'>{row.get('Año','')}</td>"
        table_html += f"<td style='padding:12px; text-align:center; border:1px solid #ddd;'>{row.get('Siglas','')}</td>"
        table_html += f"<td style='padding:12px; text-align:center; border:1px solid #ddd;'>{row.get('Riesgo','')}</td>"
        table_html += f"<td style='padding:12px; text-align:center; border:1px solid #ddd;'>{row.get('Descripción_del_Riesgo','')}</td>"
        table_html += f"<td style='padding:12px; text-align:center; border:1px solid #ddd;'>{row.get('AC','')}</td>"
        table_html += f"<td style='padding:12px; text-align:justify; border:1px solid #ddd;'>{row.get('Descripcion','')}</td>"
        table_html += f"<td style='padding:12px; text-align:center; border:1px solid #ddd;'>{avance_inst}</td>"
        table_html += f"<td style='padding:12px; text-align:center; border:1px solid #ddd;'>{avance_oic}</td>"
        table_html += "</tr>"
    table_html += "</table></div>" #cierra la tabla fuera del for

                              #------------------ Quinto: Se muestra la tabla principal de la sección--------------#
    st.markdown(table_html, unsafe_allow_html=True)


#============================================= PIE DE PÁGINA DE LA SECCION PTAR - FUENTE SICOIN ==============================================
    st.markdown("""
      <div style='text-align:right; font-size:12px; color:#666; margin-top:20px;'>
        Fuente: Sistema de Control Interno (SICOIN)
      </div>
    """, unsafe_allow_html=True)

#================================= FIN DE LA SECCIÓN 3 - "Descripción de los Riesgos y las Acciones de Control" ==============================================
#--------------------------------------------------------------------------------------------------------------------------------------------------





###########################################################
###########################################################
###########################################################
# 2. PESTAÑA PTCI
###########################################################
###########################################################
###########################################################


#====================================== PREPARACIÓN DE DATOS ANTES DE MOSTRAR RESULTADOS EN LA PESTAÑA PTCI =====================================================================
#------------------------------------------------------------------------------------------------------------------------------------------------------------------


                        #------------------ Para el contenido de esta sección se utilizará df2, df3 y df4 --------------#

               #--------------Primero:  Se crean los dataframes (filtro_ptci y filtro_ptci_df4) según el filtro seleccionado ------------#
                    #---------------Esto se hace por que estamos usando otras bases, pero con los mismos filtros ------------#


#---- Pestaña PTCI
with tabs[1]:
    # Filtrar df3 y df4 con los mismos filtros
    if sector != "Todas":
        filtro_ptci = (df3['Sector'] == sector) & (df3['Año'] == year)
        filtro_ptci_df4 = (df4['Sector'] == sector) & (df4['Año'] == year)
    else:
        filtro_ptci = (df3['Institución'] == institucion) & (df3['Año'] == year)
        filtro_ptci_df4 = (df4['Institución'] == institucion) & (df4['Año'] == year)
    df_ptci = df3[filtro_ptci]
    df_ptci_df4 = df4[filtro_ptci_df4]

                           #--------------- Segundo: Revisa si el DataFrame filtrado df_ptci está vacío ------------#
      #---------------Esto se hace por que vamos a tomar un indicador similar a header pero lo imprimiremos directamente ------------#

    if df_ptci.empty:
        st.markdown("No hay datos para PTCI con los filtros seleccionados.")
    else:

      #---------------------- Obtiene el Cumplimiento en % según el sector (Este es el indicador que necesitamos) -------------------#
        if sector != "Todas":
            # Nuestro indicador será el promedio para sector (ya que son varias instituciones)
            cum_ngci = df_ptci['Cumplimiento_General_de_las_NGCI'].mean().round(2)
            cum_ngci_str = f"{cum_ngci}%"
        else:
            #  Nuestro indicador será el valor directo para institución (ya que solo es una)
            cum_ngci = df_ptci['Cumplimiento_General_de_las_NGCI'].iloc[0]
            cum_ngci_str = f"{round(cum_ngci, 2)}%"
      #---------------------- Una vez preparados nuestros datos, estamos listos para mostrarlos en la pestaña PTCI -------------------#
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------




#===================================================== MOSTRAR RESULTADOS EN LA PESTAÑA PTCI ==============================================
#===================================================== MOSTRAR RESULTADOS EN LA PESTAÑA PTCI ==============================================
#===================================================== MOSTRAR RESULTADOS EN LA PESTAÑA PTCI ==============================================




#================================== MOSTRAR INDICADOR PRINCIPAL DE LA PESTAÑA PTCI (Cumplimiento General de las NGCI) ==============================================
        st.markdown(f"""
          <div style='background-color:#f8f9fa; padding:20px; border-radius:10px; margin-bottom:20px; box-shadow:0 2px 4px rgba(0,0,0,0.1); text-align:center;'>
            <h2 style='color:#2e86c1; margin:0;'>
              Cumplimiento General de las NGCI: <span style='color:#621132;'>{cum_ngci_str}</span>
            </h2>
          </div>
        """, unsafe_allow_html=True)

#============================================= SE ABRE LA SECCIÓN 1 - "Programa de Trabajo de Control Interno" ==============================================
#------------------------------------------------------------------------------------------------------------------------------------------------------------
        st.markdown("""
            <div style='background-color:#621132; color:white; padding:10px; border-radius:5px; margin-bottom:20px; text-align:center;'>
                Programa de Trabajo de Control Interno
            </div>
        """, unsafe_allow_html=True)

          #-------------- Parte 1: En esta primera parte se utilizará un condicional, ya que los indicadores principales (headers de PTCI) ------------#
                        #-----------------que se van a mostrar, dependerán de la condición sobre el sector -----------------#
                    #-----------------  Estos se mostraran como una tabla (Ya que tenemos mas de dos indicadores)-----------------#
                    #-----------------  Mapearemos nombres amigables pare entender mejor las variables en la appp-----------------#

        # Mapeo de nombres amigables
        friendly_names = {
            "Acciones_de_Mejora_Programa_Original": "Programa Original de Acciones de Mejora",
            "Se_Actualizó_el_Programa": "Se Actualizó el Programa",
            "No_Se_Actualizó_el_Programa": "No Se Actualizó el Programa",
            "TotalAcciones_de_Mejora_Programa_Actualizado": "Programa Actualizado de Acciones de Mejora"
        }

                #----------------- Guardaremos las columnas de nuestros indicadores a mostrar según la condición sobre el sector-----------------#
        if sector == "Todas":
            ptci_cols = [
                "Acciones_de_Mejora_Programa_Original",
                "Se_Actualizó_el_Programa",
                "No_Se_Actualizó_el_Programa",
                "TotalAcciones_de_Mejora_Programa_Actualizado"
            ]
        else:
            ptci_cols = [
                "Acciones_de_Mejora_Programa_Original",
                "TotalAcciones_de_Mejora_Programa_Actualizado"
            ]

                #-----------------Creamos el inicio de la tabla HTML que vamos a mostrar en PTCI-----------------#
        ptci_table = "<div style='overflow-x:auto; margin-bottom:20px;'><table style='width:100%; border-collapse:collapse;'>"
        ptci_table += "<tr style='background-color:#621132; color:white;'>"

                  #----------------- Creamos los headers con nombres amigables para la tabla -----------------#
        for col in ptci_cols:
            header_name = friendly_names.get(col, col)
            ptci_table += f"<th style='padding:12px; text-align:center; border:1px solid #ddd;'>{header_name}</th>"
        ptci_table += "</tr><tr>"

                #-------------- Parte 2: Llenamos los valores de nuestra tabla según la condición sobre el sector ------------#
        for col in ptci_cols:
            if sector == "Todas" and col in ["Se_Actualizó_el_Programa", "No_Se_Actualizó_el_Programa"]:
                cell_value = df_ptci[col].iloc[0] if not df_ptci.empty and col in df_ptci.columns else "N/A"
            else:
                numeric_value = pd.to_numeric(df_ptci[col], errors='coerce').fillna(0).sum() if col in df_ptci.columns else 0
                cell_value = int(round(numeric_value))
            ptci_table += f"<td style='padding:12px; text-align:center; border:1px solid #ddd; font-weight:500;'>{cell_value}</td>"
        ptci_table += "</tr></table></div>"

                #-------------- Parte 3: Finalmente mostramos la tabla con nuestros indicadores para el PTCI ------------#
        st.markdown(ptci_table, unsafe_allow_html=True)


#============================================= SE ABRE LA SECCIÓN 2 - "Programa de Trabajo de Control Interno - Desglose por Institución" =============================================
#------------------------------------------------------------------------------------------------------------------------------------------------------------#---------------------------------------------------------------------------------------

        # Condición para mostrar la Sección 2
        if sector != "Todas":
            st.markdown("""
              <div style='background-color:#621132; color:white; padding:10px; border-radius:5px; margin-bottom:10px; text-align:center;'>
                Desglose por Institución
              </div>
            """, unsafe_allow_html=True)

            #------------- Filtro por Institución --------------
            selected_institucion = st.selectbox("Filtrar por Institución", options=sorted(df_ptci["Institución"].unique()))

            #----------------- Desglose de las variables a mostrar -----------------#
            desglose = df_ptci[["Año", "Institución", "Cumplimiento_General_de_las_NGCI", "Informe_Anual_Finalizado", "SUBIO_ARCHIVO",
                                "Se_Actualizó_el_Programa", "No_Se_Actualizó_el_Programa",
                                "Acciones_de_Mejora_Programa_Original", "TotalAcciones_de_Mejora_Programa_Actualizado"]]

            # Filtrar el DataFrame según la institución seleccionada
            desglose = desglose[desglose["Institución"] == selected_institucion]

            #------------- Diccionario de etiquetas amigables --------------
            friendly_labels = {
                "Año": "Año",
                "Institución": "Institución",
                "Cumplimiento_General_de_las_NGCI": "Cumplimiento General NGCI",
                "Informe_Anual_Finalizado": "Informe Anual Finalizado",
                "SUBIO_ARCHIVO": "Subió Archivo",
                "Se_Actualizó_el_Programa": "Programa Actualizado",
                "No_Se_Actualizó_el_Programa": "Programa No Actualizado",
                "Acciones_de_Mejora_Programa_Original": "Acciones Mejora (Original)",
                "TotalAcciones_de_Mejora_Programa_Actualizado": "Acciones Mejora (Actualizado)"
            }

            #----------------- Creando las columnas de la Tabla HTML para el desglose -----------------#
            desglose_html = "<div style='overflow-x:auto; margin-bottom:20px; font-size:12px; padding:5px;'><table style='width:100%; border-collapse:collapse;'>"
            desglose_html += "<tr style='background-color:#621132; color:white;'>"

            #----------------- Llenado de tabla (cabeceras con etiquetas amigables) -----------------#
            for col in desglose.columns:
                friendly_name = friendly_labels.get(col, col)
                desglose_html += f"<th style='padding:5px; text-align:center; border:1px solid #ddd;'>{friendly_name}</th>"
            desglose_html += "</tr>"

            for _, row in desglose.iterrows():
                desglose_html += "<tr>"
                for col in desglose.columns:
                    value = row.get(col, '')
                    if col == "Cumplimiento_General_de_las_NGCI":
                        value = f"{int(value)}%" if pd.notna(value) else ""
                    desglose_html += f"<td style='padding:5px; text-align:center; border:1px solid #ddd;'>{value}</td>"
                desglose_html += "</tr>"
            desglose_html += "</table></div>"

            #-------------- Parte 2: Mostramos la tabla del programa de trabajo desglosado por institución --------------#
            st.markdown(desglose_html, unsafe_allow_html=True)



#============================================= SE ABRE LA SECCIÓN 3 - "Detalle de las Acciones de Mejora"================================= ==============================================
#------------------------------------------------------------------------------------------------------------------------------------------------------------
        st.markdown("""
          <div style='background-color:#621132; color:white; padding:10px; border-radius:5px; margin-bottom:20px; text-align:center;'>
            Detalle de las Acciones de Mejora
          </div>
        """, unsafe_allow_html=True)


          #-------------- Parte 1:  Esta tabla será para el detalle de las Acciones de Mejora------------#
                        #----------------- Creamos columnas con las variables a mostrar  -----------------#

        detalle_cols = ["Registradas", "Localizadas", "No_localizadas", "Suficientes", "Parcielmente_Suficientes", "Insuficientes"]
        detalle_table = "<div style='overflow-x:auto; margin-bottom:20px;'><table style='width:100%; border-collapse:collapse;'>"
        detalle_table += "<tr style='background-color:#621132; color:white;'>"

    #----------------- Llenamos la tabla -----------------#
        for col in detalle_cols:
            detalle_table += f"<th style='padding:12px; text-align:center; border:1px solid #ddd;'>{col}</th>"
        detalle_table += "</tr><tr>"
        for col in detalle_cols:
            value = pd.to_numeric(df_ptci_df4[col], errors='coerce').fillna(0).sum() if col in df_ptci_df4.columns else 0
            detalle_table += f"<td style='padding:12px; text-align:center; border:1px solid #ddd; font-weight:500;'>{int(round(value))}</td>"
        detalle_table += "</tr></table></div>"

          #-------------- Parte 2: Mostramos la tabla -----------#
        st.markdown(detalle_table, unsafe_allow_html=True)





#============================================= SE ABRE LA SECCIÓN 4 - "Seguimiento de las Acciones de Mejora"================================= ==============================================
#------------------------------------------------------------------------------------------------------------------------------------------------------------
        st.markdown("""
          <div style='background-color:#621132; color:white; padding:10px; border-radius:5px; margin-bottom:20px; text-align:center;'>
            Seguimiento de las Acciones de Mejora
          </div>
        """, unsafe_allow_html=True)



          #-------------- Parte 1:  Creamos la tabla que muestra el seguimiento de las acciones de mejora (usamos el estatus y los trimestres)------------#
                        #----------------- Aqui el cumplimiento es porcentaje entonces calculamos el promedio para el caso del Sector diferente de "Todas" -----------------#


        # --- MODIFICACIÓN: Usar promedio para Cumplimiento en caso de sector diferente de "Todas"
        data_ptci_dict = {}
        for t in trimestres:
            for estado in estados:
                key = f"{t}{estado}"
                if key in df_ptci.columns:
                    if estado == "Cumplimiento" and sector != "Todas":
                        value = pd.to_numeric(df_ptci[key], errors='coerce').fillna(0).mean()
                    else:
                        value = pd.to_numeric(df_ptci[key], errors='coerce').fillna(0).sum()
                else:
                    value = 0
                data_ptci_dict[key] = int(round(value))


          #-------------- Parte 2: Mostrar tabla con formato------------#
        st.markdown("""
          <div style='overflow-x:auto; margin-bottom:20px;'>
            <table style='width:100%; border-collapse:collapse;'>
              <tr style='background-color:#621132; color:white; text-align:center;'>
                <th>Estatus de las Acciones de Mejora</th>
                <th>Primero</th>
                <th>Segundo</th>
                <th>Tercero</th>
                <th>Cuarto</th>
              </tr>
              <tr>
                <th style='background-color:#621132; color:white;'>Sin Avances</th>
                <td style='text-align:center; border:1px solid #ddd;'>{0}</td>
                <td style='text-align:center; border:1px solid #ddd;'>{1}</td>
                <td style='text-align:center; border:1px solid #ddd;'>{2}</td>
                <td style='text-align:center; border:1px solid #ddd;'>{3}</td>
              </tr>
              <tr>
                <th style='background-color:#621132; color:white;'>En Proceso</th>
                <td style='text-align:center; border:1px solid #ddd;'>{4}</td>
                <td style='text-align:center; border:1px solid #ddd;'>{5}</td>
                <td style='text-align:center; border:1px solid #ddd;'>{6}</td>
                <td style='text-align:center; border:1px solid #ddd;'>{7}</td>
              </tr>
              <tr>
                <th style='background-color:#621132; color:white;'>Concluidas</th>
                <td style='text-align:center; border:1px solid #ddd;'>{8}</td>
                <td style='text-align:center; border:1px solid #ddd;'>{9}</td>
                <td style='text-align:center; border:1px solid #ddd;'>{10}</td>
                <td style='text-align:center; border:1px solid #ddd;'>{11}</td>
              </tr>
              <tr>
                <th style='background-color:#621132; color:white;'>% de Cumplimiento</th>
                <td style='text-align:center; border:1px solid #ddd;'>{12}%</td>
                <td style='text-align:center; border:1px solid #ddd;'>{13}%</td>
                <td style='text-align:center; border:1px solid #ddd;'>{14}%</td>
                <td style='text-align:center; border:1px solid #ddd;'>{15}%</td>
              </tr>
            </table>
          </div>
        """.format(
          data_ptci_dict.get("1Sin_Avances",0), data_ptci_dict.get("2Sin_Avances",0), data_ptci_dict.get("3Sin_Avances",0), data_ptci_dict.get("4Sin_Avances",0),
          data_ptci_dict.get("1En_Proceso",0), data_ptci_dict.get("2En_Proceso",0), data_ptci_dict.get("3En_Proceso",0), data_ptci_dict.get("4En_Proceso",0),
          data_ptci_dict.get("1Concluidas",0), data_ptci_dict.get("2Concluidas",0), data_ptci_dict.get("3Concluidas",0), data_ptci_dict.get("4Concluidas",0),
          data_ptci_dict.get("1Cumplimiento",0), data_ptci_dict.get("2Cumplimiento",0), data_ptci_dict.get("3Cumplimiento",0), data_ptci_dict.get("4Cumplimiento",0)
        ), unsafe_allow_html=True)


              #-------------- Parte 3: Se crea el gráfico de barras para el seguimiento de las acciones de mejora ------------#
           #----------------- Para ello primero crea lista de diccionarios que contenga los datos para el gráfico -----------------#

        plot_data_ptci = []
        for t in trimestres:
            for estado in estados:
                key = f"{t}{estado}"
                plot_data_ptci.append({'Trimestre': f' {t}', 'Estado': estado, 'Cantidad': data_ptci_dict.get(key, 0)})             #cambio de T por Trimestre

                #-------------- Convierte a dataframe la información obtenida y crea la gráfica (fig)  ------------------------#
        fig_ptci = px.bar(pd.DataFrame(plot_data_ptci), x='Trimestre', y='Cantidad', color='Estado',
                          barmode='group', height=400,
                          color_discrete_map={'Sin_Avances': '#dc3545', 'En_Proceso': '#ffc107',
                                              'Concluidas': '#28a745', 'Cumplimiento': '#6610f2'})

                    #----------------- Da formato final -----------------#
        fig_ptci.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(color='#333'),
            xaxis=dict(title=None, gridcolor='#f0f0f0'),
            yaxis=dict(title=None, gridcolor='#f0f0f0'),
            legend=dict(title=None),
            margin=dict(l=20, r=20, t=50, b=20)
        )

     #--------------  Agrega la etiqueta de porcentaje en las barras de Cumplimiento (ya que este valor es porcentaje) -----------------#
        for trace in fig_ptci.data:
            if trace.name == "Cumplimiento":
                trace.text = [f"{y}%" for y in trace.y]
                trace.textposition = 'outside'

          #-------------- Parte 4: Mostramos la tabla -----------#
        st.plotly_chart(fig_ptci, use_container_width=True)



#============================================= SE ABRE LA SECCIÓN 5 - "Descripción de los Procesos y Acciones de Mejora" =============================================
#------------------------------------------------------------------------------------------------------------------------------------------------------------
        st.markdown("""
          <div style='background-color:#621132; color:white; padding:10px; border-radius:5px; margin-top:30px; margin-bottom:30px; text-align:center;'>
            Descripción de los Procesos y las Acciones de Mejora
          </div>
        """, unsafe_allow_html=True)

        #------------- Filtros --------------
        col1, col2 = st.columns(2)
        with col1:
            selected_trimester = st.selectbox("Filtrar por Trimestre", options=sorted(df_ptci_df4["Trimestre"].unique()))
        with col2:
            selected_siglas = st.selectbox("Filtrar por Siglas", options=sorted(df_ptci_df4["Siglas"].unique()))

        # Filtrar el DataFrame según los filtros seleccionados
        filtered_df = df_ptci_df4[
            (df_ptci_df4["Trimestre"] == selected_trimester) &
            (df_ptci_df4["Siglas"] == selected_siglas)
        ]

        #-------------- Parte 1: Creamos la tabla que muestra la descripción de los Procesos y Acciones de Mejora ------------#
        headers_ptci = ["Año", "Trimestre", "Siglas", "Procesos", "AM", "Descripcion", "Fecha_Inicio", "Fecha_Termino",
                        "Avance_Institución", "Avance_OIC", "¿Evaluado?", "¿Favorable?", "¿AM_Congruete?", "¿Contribuye?"]

        desc_ptci_html = "<div style='overflow-x:auto;'><table style='width:100%; border-collapse:collapse; margin-bottom:20px;'>"
        desc_ptci_html += "<tr style='background-color:#621132; color:white;'>"

        for h in headers_ptci:
            desc_ptci_html += f"<th style='padding:12px; text-align:center; border:1px solid #ddd;'>{h}</th>"
        desc_ptci_html += "</tr>"

        #-------------- Llenamos la tabla ------------#
        for _, row in filtered_df.iterrows():
            desc_ptci_html += "<tr>"
            for h in headers_ptci:
                cell = row.get(h, "")
                if h in ["Avance_Institución", "Avance_OIC"]:
                    try:
                        cell = f"{int(float(cell))}%"
                    except:
                        cell = cell
                desc_ptci_html += f"<td style='padding:12px; text-align:center; border:1px solid #ddd;'>{cell}</td>"
            desc_ptci_html += "</tr>"
        desc_ptci_html += "</table></div>"

        #-------------- Parte 2: Imprimimos la tabla ------------#
        st.markdown(desc_ptci_html, unsafe_allow_html=True)







#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#============================================= PIE DE PÁGINA DE LA SECCION PTCI - FUENTE SICOIN ==============================================

    st.markdown("""
      <div style='text-align:right; font-size:12px; color:#666; margin-top:20px;'>
        Fuente: Sistema de Control Interno (SICOIN)
      </div>
    """, unsafe_allow_html=True)

#================================= FIN DE LA SECCIÓN 5 - "Descripción de los Procesos y Acciones de Mejora" ==============================================
#--------------------------------------------------------------------------------------------------------------------------------------------------




###########################################################
###########################################################
###########################################################
# PESTAÑA REPORTES
###########################################################
###########################################################
###########################################################




with tabs[2]:
    st.markdown("<h2>REPORTES</h2><p>Información Actualizada al 19/03/2025.</p>", unsafe_allow_html=True)

#CORREGIDO V 2.1.1
