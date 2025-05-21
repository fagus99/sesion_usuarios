import streamlit as st
import pandas as pd

st.set_page_config(page_title="Análisis de Usuarios - Casino", layout="wide")
st.title("Análisis Diario de Usuarios")

uploaded_file = st.file_uploader("Subí el archivo Excel", type=[".xls", ".xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Asegurar formato de fecha
    df['ID'] = pd.to_datetime(df['ID'], errors='coerce')
    df['REGISTRATION_DATE'] = pd.to_datetime(df['REGISTRATION_DATE'], errors='coerce')

    # Métricas principales
    iniciaron_sesion = df[df['SESSION_NUMBER'] > 0]
    apostaron = df[df['TOTAL_PLAYED_AMOUNT'] > 0]
    depositaron = df[df['TOTAL_DEPOSIT_AMOUNT'] > 0]
    retiraron = df[df['TOTAL_WITHDRAWAL_AMOUNT'] > 0]

    st.subheader("Métricas Generales")
    st.markdown(f"- **Usuarios que iniciaron sesión:** {iniciaron_sesion['USER_ID'].nunique()}")
    st.markdown(f"- **Usuarios que apostaron:** {apostaron['USER_ID'].nunique()}")
    st.markdown(f"- **Usuarios que depositaron:** {depositaron['USER_ID'].nunique()}")
    st.markdown(f"- **Usuarios que retiraron:** {retiraron['USER_ID'].nunique()}")

    # Cruces de acciones
    sesion_sin_deposito = iniciaron_sesion[~iniciaron_sesion['USER_ID'].isin(depositaron['USER_ID'])]
    sesion_sin_apuesta = iniciaron_sesion[~iniciaron_sesion['USER_ID'].isin(apostaron['USER_ID'])]
    deposito_sin_juego = depositaron[~depositaron['USER_ID'].isin(apostaron['USER_ID'])]

    st.subheader("Cruces entre acciones")
    st.markdown(f"- **Iniciaron sesión pero no depositaron:** {sesion_sin_deposito['USER_ID'].nunique()}")
    st.markdown(f"- **Iniciaron sesión pero no apostaron:** {sesion_sin_apuesta['USER_ID'].nunique()}")
    st.markdown(f"- **Depositantes que no jugaron:** {deposito_sin_juego['USER_ID'].nunique()}")

    # Usuarios activos con actividad
    activos = df[df['STATUS'] == 'ACTIVE']
    activos_con_actividad = activos[
        (activos['TOTAL_PLAYED_AMOUNT'] > 0) |
        (activos['TOTAL_DEPOSIT_AMOUNT'] > 0) |
        (activos['SESSION_NUMBER'] > 0)
    ]
    st.subheader("Usuarios activos con actividad")
    st.markdown(f"- **Usuarios activos con alguna acción:** {activos_con_actividad['USER_ID'].nunique()}")

    # Usuarios nuevos del día
    usuarios_nuevos = df[df['ID'].dt.date == df['REGISTRATION_DATE'].dt.date]
    if not usuarios_nuevos.empty:
        st.subheader("Usuarios Nuevos del Día")

        no_jugaron = usuarios_nuevos[usuarios_nuevos['TOTAL_PLAYED_AMOUNT'] == 0]
        recibieron_bono = usuarios_nuevos[usuarios_nuevos['TOTAL_RELEASE_BONUS_AMOUNT'] > 0]
        iniciaron_sesion = usuarios_nuevos[usuarios_nuevos['SESSION_NUMBER'] > 0]
        no_iniciaron_sesion = usuarios_nuevos[usuarios_nuevos['SESSION_NUMBER'] == 0]

        st.markdown(f"- **Usuarios nuevos que no jugaron:** {no_jugaron['USER_ID'].nunique()}")
        st.markdown(f"- **Usuarios nuevos que recibieron bono:** {recibieron_bono['USER_ID'].nunique()}")
        st.markdown(f"- **Usuarios nuevos que iniciaron sesión:** {iniciaron_sesion['USER_ID'].nunique()}")
        st.markdown(f"- **Usuarios nuevos que NO iniciaron sesión:** {no_iniciaron_sesion['USER_ID'].nunique()}")

        with st.expander("Ver listado de usuarios nuevos que no jugaron"):
            st.dataframe(no_jugaron[['USER_ID', 'REGISTRATION_DATE', 'SESSION_NUMBER', 'TOTAL_RELEASE_BONUS_AMOUNT']])

        with st.expander("Ver listado de usuarios nuevos que iniciaron sesión"):
            st.dataframe(iniciaron_sesion[['USER_ID', 'REGISTRATION_DATE', 'SESSION_NUMBER']])
    else:
        st.info("No se encontraron usuarios nuevos en la fecha del reporte.")
