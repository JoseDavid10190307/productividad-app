import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt

st.set_page_config(page_title="Análisis de Productividad", layout="wide")
st.title("📊 Sistema de Análisis de Productividad del Equipo")

# --- Subir archivo ---
archivo = st.file_uploader("🔼 Carga el archivo Excel con los datos de productividad", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)

    # Verifica columnas requeridas
    columnas_requeridas = {"nombre", "num_doc", "productividad", "periodo"}
    if not columnas_requeridas.issubset(set(df.columns)):
        st.error(f"❌ El archivo debe tener las siguientes columnas: {', '.join(columnas_requeridas)}")
    else:
        # Selección múltiple de periodos
        periodos_disponibles = sorted(df["periodo"].dropna().unique())
        periodos_seleccionados = st.multiselect("📅 Selecciona uno o varios meses a analizar", periodos_disponibles)

        if not periodos_seleccionados:
            st.info("👈 Por favor selecciona al menos un mes para iniciar el análisis.")
        else:
            # Umbrales
            col1, col2 = st.columns(2)
            with col1:
                umbral_superior = st.number_input("🔺 Productividad **mayor a** (alta productividad):", min_value=0.0, max_value=100.0, value=80.0)
            with col2:
                umbral_inferior = st.number_input("🔻 Productividad **menor a** (baja productividad):", min_value=0.0, max_value=100.0, value=40.0)

            # Filtro general
            df_filtrado = df[df["periodo"].isin(periodos_seleccionados)].copy()
            total_general = df_filtrado["num_doc"].nunique()
            promedio_general = df_filtrado["productividad"].mean()

            st.subheader("📋 Resumen General (todos los meses seleccionados)")

            alta_general = df_filtrado[df_filtrado["productividad"] > umbral_superior]
            baja_general = df_filtrado[df_filtrado["productividad"] < umbral_inferior]

            st.write(f"👥 Total personas analizadas: {total_general}")
            st.write(f"📈 Promedio de productividad general: **{promedio_general:.2f}**")
            st.markdown(f"""
            - 🔺 Alta productividad: {len(alta_general)} personas ({(len(alta_general)/total_general)*100:.2f}%)  
            - 🔻 Baja productividad: {len(baja_general)} personas ({(len(baja_general)/total_general)*100:.2f}%)
            """)

            with st.expander("🔺 Ver detalles de Alta Productividad (general)"):
                st.dataframe(alta_general[["nombre", "num_doc", "periodo", "productividad"]])

            with st.expander("🔻 Ver detalles de Baja Productividad (general)"):
                st.dataframe(baja_general[["nombre", "num_doc", "periodo", "productividad"]])

            # Descargar resultados como Excel
            def convertir_a_excel(df_dict):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    for nombre_hoja, dataframe in df_dict.items():
                        dataframe.to_excel(writer, sheet_name=nombre_hoja, index=False)
                return output.getvalue()

            st.download_button(
                label="📥 Descargar Excel - Alta Productividad",
                data=convertir_a_excel({"Alta_Productividad": alta_general}),
                file_name="alta_productividad.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.download_button(
                label="📥 Descargar Excel - Baja Productividad",
                data=convertir_a_excel({"Baja_Productividad": baja_general}),
                file_name="baja_productividad.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.divider()
            st.subheader("📆 Análisis por Mes")

            for periodo in periodos_seleccionados:
                st.markdown(f"### 📅 Periodo: {periodo}")
                df_mes = df_filtrado[df_filtrado["periodo"] == periodo]

                total_mes = df_mes["num_doc"].nunique()
                promedio_mes = df_mes["productividad"].mean()
                alta_mes = df_mes[df_mes["productividad"] > umbral_superior]
                baja_mes = df_mes[df_mes["productividad"] < umbral_inferior]
                intermedia_mes = df_mes[(df_mes["productividad"] <= umbral_superior) & (df_mes["productividad"] >= umbral_inferior)]

                st.write(f"👥 Total personas en el mes: {total_mes}")
                st.write(f"📈 Promedio de productividad en el mes: **{promedio_mes:.2f}**")
                st.markdown(f"""
                - 🔺 Alta productividad: {len(alta_mes)} personas ({(len(alta_mes)/total_mes)*100:.2f}%)  
                - 🔻 Baja productividad: {len(baja_mes)} personas ({(len(baja_mes)/total_mes)*100:.2f}%)  
                - ➖ Intermedia: {len(intermedia_mes)} personas ({(len(intermedia_mes)/total_mes)*100:.2f}%)
                """)

                with st.expander("🔺 Ver detalles de Alta Productividad"):
                    st.dataframe(alta_mes[["nombre", "num_doc", "productividad"]])

                with st.expander("🔻 Ver detalles de Baja Productividad"):
                    st.dataframe(baja_mes[["nombre", "num_doc", "productividad"]])

                # Gráfica
                fig, ax = plt.subplots()
                ax.bar(["Alta", "Intermedia", "Baja"], [len(alta_mes), len(intermedia_mes), len(baja_mes)],
                        color=["green", "gray", "red"])
                ax.set_ylabel("Cantidad de personas")
                ax.set_title(f"Distribución de productividad - {periodo}")
                st.pyplot(fig)

                st.divider()
