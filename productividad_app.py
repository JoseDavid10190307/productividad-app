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
                umbral_superior = st.number_input("🔺 Productividad **mayor a** (alta productividad):", min_value=0.0, max_value=100.0, value=0.80)
            with col2:
                umbral_inferior = st.number_input("🔻 Productividad **menor a** (baja productividad):", min_value=0.0, max_value=100.0, value=0.40)
            
            numero_meses_por_debajo = st.number_input( 
                "🔻 Número mínimo de meses con baja productividad para considerar una persona como de baja productividad:",
                min_value=1, max_value=12, value=2
            )


            # Filtro por meses seleccionados
            df_filtrado = df[df["periodo"].isin(periodos_seleccionados)].copy()

            # Promedios globales
            promedio_general = df_filtrado.groupby("periodo")["productividad"].mean().mean()
            promedio_personas_mes = df_filtrado.groupby("periodo")["num_doc"].nunique().mean() 
            
            # Total personas únicas en todos los meses seleccionados
            total_general = df_filtrado["num_doc"].nunique()

            # === LÓGICA DE ALTA Y BAJA PRODUCTIVIDAD ===

            # 🔺 Alta productividad: promedio de productividad por persona > umbral
            promedios_persona = df_filtrado.groupby("num_doc")["productividad"].mean().reset_index()
            alta_general = promedios_persona[promedios_persona["productividad"] > umbral_superior]
            num_alta = len(alta_general)

            # 🔻 Baja productividad: personas con 2 o más registros por debajo del umbral
            bajas_individuales = df_filtrado[df_filtrado["productividad"] < umbral_inferior]
            bajas_contadas = bajas_individuales.groupby("num_doc").size()
            baja_general = bajas_contadas[bajas_contadas >= numero_meses_por_debajo].reset_index(name="conteo")
            num_baja = len(baja_general)

            # Porcentajes
            porcentaje_alta = (num_alta / total_general) * 100
            porcentaje_baja = (num_baja / total_general) * 100

            # === VISUALIZACIÓN ===
            st.subheader("📋 Resumen General (todos los meses seleccionados)")
            st.write(f"👥 Cantidad total de personas medidas: {total_general}")
            st.write(f"👥 Promedio de personas por mes: {promedio_personas_mes:.2f}")
            st.write(f"📈 Promedio de productividad general (por mes): **{promedio_general:.2f}**")

            st.markdown(f"""
            - 🔺 Alta productividad: {num_alta} personas ({porcentaje_alta:.2f}% del total)
            - 🔻 Baja productividad: {num_baja} personas ({porcentaje_baja:.2f}% del total)
            """)

            with st.expander("🔺 Ver detalles de Alta Productividad (general)"):
                alta_merge = pd.merge(alta_general, df_filtrado[["num_doc", "nombre"]].drop_duplicates(), on="num_doc", how="left")
                st.dataframe(alta_merge[["nombre", "num_doc", "productividad"]].sort_values("productividad", ascending=False))
            
            with st.expander("🔻 Ver detalles de Baja Productividad (general)"):
                # Filtrar registros solo de baja productividad de las personas que están en baja_general
                personas_baja = baja_general["num_doc"].unique()
                df_bajas = df_filtrado[df_filtrado["num_doc"].isin(personas_baja) & (df_filtrado["productividad"] < umbral_inferior)].copy()

                # Pivotear: una columna por periodo
                pivot = df_bajas.pivot_table(
                    index=["num_doc", "nombre"],
                    columns="periodo",
                    values="productividad",
                    aggfunc="mean"
                ).reset_index()

                # Agregar la columna 'conteo' (cuántos meses tuvo baja productividad)
                pivot = pd.merge(pivot, baja_general[["num_doc", "conteo"]], on="num_doc", how="left")

                # Reordenar columnas: nombre, num_doc, conteo, y luego las columnas de periodos
                cols_orden = ["nombre", "num_doc", "conteo"] + sorted([c for c in pivot.columns if c not in ["nombre", "num_doc", "conteo"]])
                pivot = pivot[cols_orden]

                # Mostrar la tabla ordenada por mayor conteo
                st.dataframe(pivot.sort_values("conteo", ascending=False))

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
