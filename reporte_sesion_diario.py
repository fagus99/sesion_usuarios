import streamlit as st
import pandas as pd
from datetime import datetime

st.title("Análisis diario de acciones de usuarios")

uploaded_file = st.file_uploader("Subí el archivo Excel con los datos diarios", type=[".xlsx", ".xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Normalizar columnas
    df.columns = df.columns.str.strip().str.lower()

    # Convertir columnas de fecha
    for col in ['id', 'registration_date', 'last_login_date']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    df['fecha_id'] = df['id'].dt.date
    df['fecha_registro'] = df['registration_date'].dt.date

    # Total usuarios que iniciaron sesión
    usuarios_login = df[df['logged_in_day'].astype(str).str.lower() == 'yes']
    cant_login = usuarios_login['user_id'].nunique()

    # Total usuarios que apostaron
    usuarios_apostaron = df[df['have_bet'].astype(str).str.lower() == 'yes']
    cant_apostaron = usuarios_apostaron['user_id'].nunique()

    # Total usuarios que depositaron
    usuarios_depositaron = df[df['total_deposit_amount'] > 0]
    cant_depositaron = usuarios_depositaron['user_id'].nunique()

    # Total usuarios que retiraron
    usuarios_retiraron = df[df['total_withdrawal_amount'] > 0]
    cant_retiraron = usuarios_retiraron['user_id'].nunique()

    # Cruces
    login_sin_deposito = usuarios_login[~usuarios_login['user_id'].isin(usuarios_depositaron['user_id'])]['user_id'].nunique()
    login_sin_apuesta = usuarios_login[~usuarios_login['user_id'].isin(usuarios_apostaron['user_id'])]['user_id'].nunique()
    deposito_sin_apuesta = usuarios_depositaron[~usuarios_depositaron['user_id'].isin(usuarios_apostaron['user_id'])]['user_id'].nunique()

    # Activos con alguna acción
    activos = df[df['status'].astype(str).str.lower() == 'active']
    activos_con_accion = activos[activos['user_id'].isin(pd.concat([usuarios_apostaron, usuarios_depositaron])['user_id'])]['user_id'].nunique()

    # Usuarios nuevos (registro el mismo día del reporte)
    fecha_reporte = df['fecha_id'].iloc[0]
    nuevos = df[df['fecha_registro'] == fecha_reporte]

    nuevos_sin_apuesta = nuevos[nuevos['have_bet'].astype(str).str.lower() != 'yes']
    nuevos_con_bono = nuevos[nuevos['total_release_bonus_amount'] > 0]
    nuevos_con_login = nuevos[nuevos['logged_in_day'].astype(str).str.lower() == 'yes']
    nuevos_sin_login = nuevos[nuevos['logged_in_day'].astype(str).str.lower() != 'yes']

    st.subheader("Métricas Generales")
    st.write(f"Usuarios que iniciaron sesión: {cant_login}")
    st.write(f"Usuarios que apostaron: {cant_apostaron}")
    st.write(f"Usuarios que depositaron: {cant_depositaron}")
    st.write(f"Usuarios que retiraron: {cant_retiraron}")

    st.subheader("Cruces entre acciones")
    st.write(f"Iniciaron sesión pero no depositaron: {login_sin_deposito}")
    st.write(f"Iniciaron sesión pero no apostaron: {login_sin_apuesta}")
    st.write(f"Depositantes que no jugaron: {deposito_sin_apuesta}")

    st.subheader("Usuarios activos con alguna acción")
    st.write(f"Usuarios activos con alguna acción: {activos_con_accion}")

    st.subheader("Usuarios nuevos")
    if not nuevos.empty:
        st.write(f"Cantidad de nuevos usuarios: {nuevos['user_id'].nunique()}")
        st.write(f"Nuevos que no jugaron: {nuevos_sin_apuesta['user_id'].nunique()}")
        st.write(f"Nuevos que recibieron bono: {nuevos_con_bono['user_id'].nunique()}")
        st.write(f"Nuevos que iniciaron sesión: {nuevos_con_login['user_id'].nunique()}")
        st.write(f"Nuevos que no iniciaron sesión: {nuevos_sin_login['user_id'].nunique()}")

        st.subheader("Detalle de usuarios nuevos que no jugaron")
        st.dataframe(nuevos_sin_apuesta[['user_id', 'registration_date', 'logged_in_day', 'total_release_bonus_amount']])
    else:
        st.write("No se encontraron usuarios nuevos en la fecha del reporte.")
