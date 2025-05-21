import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Análisis de Actividad de Usuarios", layout="wide")
st.title("Resumen Diario de Acciones de Usuarios")

uploaded_file = st.file_uploader("Subí el archivo Excel con los datos de usuarios", type=[".xls", ".xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Normalizar nombres de columnas
    df.columns = df.columns.str.lower().str.strip()

    # Convertir columnas necesarias a minúsculas para contenido también
    df['status'] = df['status'].str.lower()
    if 'have_bet' in df.columns:
        df['have_bet'] = df['have_bet'].str.lower()

    # Asegurar que las fechas estén bien formateadas
    df['registration_date'] = pd.to_datetime(df['registration_date']).dt.date
    df['id'] = pd.to_datetime(df['id']).dt.date

    # Usuarios que iniciaron sesión
    usuarios_login = df[df['logged_in_day'] > 0]['user_id'].nunique()

    # Usuarios que apostaron
    usuarios_apostaron = df[df['have_bet'] == 'yes']['user_id'].nunique()

    # Usuarios que depositaron
    usuarios_depositaron = df[df['total_deposit_amount'] > 0]['user_id'].nunique()

    # Usuarios que retiraron
    usuarios_retiraron = df[df['total_withdrawal_amount'] > 0]['user_id'].nunique()

    # Iniciaron sesión pero no depositaron
    login_sin_deposito = df[(df['logged_in_day'] > 0) & (df['total_deposit_amount'] == 0)]['user_id'].nunique()

    # Iniciaron sesión pero no apostaron
    login_sin_apuesta = df[(df['logged_in_day'] > 0) & (df['have_bet'] != 'yes')]['user_id'].nunique()

    # Depositantes que no jugaron
    deposito_sin_apuesta = df[(df['total_deposit_amount'] > 0) & (df['have_bet'] != 'yes')]['user_id'].nunique()

    # Usuarios activos con alguna acción (apuesta o depósito)
    activos_accion = df[(df['status'] == 'active') & ((df['have_bet'] == 'yes') | (df['total_deposit_amount'] > 0))]['user_id'].nunique()

    # Mostrar métricas
    st.subheader("Métricas Generales")
    st.markdown(f"- **Usuarios que iniciaron sesión:** {usuarios_login}")
    st.markdown(f"- **Usuarios que apostaron:** {usuarios_apostaron}")
    st.markdown(f"- **Usuarios que depositaron:** {usuarios_depositaron}")
    st.markdown(f"- **Usuarios que retiraron:** {usuarios_retiraron}")

    st.subheader("Cruces entre acciones")
    st.markdown(f"- **Iniciaron sesión pero no depositaron:** {login_sin_deposito}")
    st.markdown(f"- **Iniciaron sesión pero no apostaron:** {login_sin_apuesta}")
    st.markdown(f"- **Depositantes que no jugaron:** {deposito_sin_apuesta}")
    st.markdown(f"- **Usuarios activos con alguna acción:** {activos_accion}")

    # Usuarios nuevos en la fecha del reporte
    fecha_reporte = df['id'].iloc[0]  # asumimos que todo el archivo es del mismo día
    nuevos_usuarios = df[df['registration_date'] == fecha_reporte]

    if not nuevos_usuarios.empty:
        st.subheader("Usuarios Nuevos en la Fecha del Reporte")

        nuevos_sin_apuesta = nuevos_usuarios[nuevos_usuarios['have_bet'] != 'yes']
        nuevos_con_bono = nuevos_usuarios[nuevos_usuarios['total_release_bonus_amount'] > 0]
        nuevos_con_login = nuevos_usuarios[nuevos_usuarios['logged_in_day'] > 0]
        nuevos_sin_login = nuevos_usuarios[nuevos_usuarios['logged_in_day'] == 0]

        st.markdown(f"- **Usuarios nuevos que no jugaron:** {nuevos_sin_apuesta.shape[0]}")
        st.markdown(f"- **Usuarios nuevos que recibieron bono:** {nuevos_con_bono.shape[0]}")
        st.markdown(f"- **Usuarios nuevos que iniciaron sesión:** {nuevos_con_login.shape[0]}")
        st.markdown(f"- **Usuarios nuevos que no iniciaron sesión:** {nuevos_sin_login.shape[0]}")

        with st.expander("Ver detalle de nuevos usuarios"):
            st.dataframe(nuevos_usuarios[['user_id', 'registration_date', 'have_bet', 'total_release_bonus_amount', 'logged_in_day']])
    else:
        st.info("No se encontraron usuarios nuevos en la fecha del reporte.")
