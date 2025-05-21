import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Reporte Diario de Usuarios", layout="wide")
st.title("📊 Reporte Diario de Actividad de Usuarios")

# Cargar archivo Excel
uploaded_file = st.file_uploader("Subí el archivo Excel con el resumen diario de usuarios", type=[".xlsx", ".xls"])

if uploaded_file:
    if st.button("Iniciar procesamiento"):
        progress_bar = st.progress(0, text="Procesando archivo...")

        df = pd.read_excel(uploaded_file)
        df.columns = [col.lower() for col in df.columns]  # Estandarizar nombres de columnas

        progress_bar.progress(10, text="Limpiando columnas de fecha...")
        # Procesar fecha del ID
        df['id'] = df['id'].astype(str).str.extract(r'(\d{4}-\d{1,2}-\d{1,2})')
        df['id'] = pd.to_datetime(df['id'], errors='coerce').dt.date
        fecha_reporte = df['id'].iloc[0]

        # Procesar fecha de registro
        df['registration_date'] = pd.to_datetime(df['registration_date'], errors='coerce').dt.date

        progress_bar.progress(30, text="Calculando métricas generales...")
        usuarios_login = df[df['logged_in_day'] > 0]
        usuarios_apostaron = df[df['have_bet'].str.lower() == 'yes']
        usuarios_depositaron = df[df['total_deposit_amount'] > 0]
        usuarios_retiraron = df[df['total_withdrawal_amount'] < 0]  # valor negativo = retiro

        usuarios_sesion_sin_deposito = usuarios_login[~usuarios_login['customer_id'].isin(usuarios_depositaron['customer_id'])]
        usuarios_sesion_sin_apuesta = usuarios_login[~usuarios_login['customer_id'].isin(usuarios_apostaron['customer_id'])]
        usuarios_depositaron_no_jugaron = usuarios_depositaron[~usuarios_depositaron['customer_id'].isin(usuarios_apostaron['customer_id'])]

        usuarios_activos = df[df['status'].str.lower() == 'active']
        usuarios_activos_con_accion = usuarios_activos[(usuarios_activos['total_deposit_amount'] > 0) | (usuarios_activos['have_bet'].str.lower() == 'yes')]

        progress_bar.progress(60, text="Detectando usuarios nuevos...")
        nuevos_usuarios = df[df['registration_date'] == fecha_reporte]
        nuevos_no_jugaron = nuevos_usuarios[nuevos_usuarios['have_bet'].str.lower() != 'yes']
        nuevos_recibieron_bono = nuevos_usuarios[nuevos_usuarios['total_release_bonus_amount'] > 0]
        nuevos_login = nuevos_usuarios[nuevos_usuarios['logged_in_day'] > 0]
        nuevos_sin_login = nuevos_usuarios[nuevos_usuarios['logged_in_day'] == 0]

        progress_bar.progress(80, text="Preparando visualización...")
        st.subheader("📌 Métricas Generales")
        st.write(f"Usuarios que iniciaron sesión: {len(usuarios_login)}")
        st.write(f"Usuarios que apostaron: {len(usuarios_apostaron)}")
        st.write(f"Usuarios que depositaron: {len(usuarios_depositaron)}")
        st.write(f"Usuarios que retiraron: {len(usuarios_retiraron)}")

        st.subheader("🔀 Cruces entre acciones")
        st.write(f"Iniciaron sesión pero no depositaron: {len(usuarios_sesion_sin_deposito)}")
        st.write(f"Iniciaron sesión pero no apostaron: {len(usuarios_sesion_sin_apuesta)}")
        st.write(f"Depositantes que no jugaron: {len(usuarios_depositaron_no_jugaron)}")
        st.write(f"Usuarios activos con alguna acción: {len(usuarios_activos_con_accion)}")

        st.subheader("📈 Porcentajes sobre usuarios que iniciaron sesión")
        total_login = len(usuarios_login)
        st.write(f"% que apostaron: {len(usuarios_apostaron[usuarios_apostaron['customer_id'].isin(usuarios_login['customer_id'])]) / total_login:.2%}")
        st.write(f"% que depositaron: {len(usuarios_depositaron[usuarios_depositaron['customer_id'].isin(usuarios_login['customer_id'])]) / total_login:.2%}")
        st.write(f"% que no apostaron: {len(usuarios_sesion_sin_apuesta) / total_login:.2%}")
        st.write(f"% que no depositaron: {len(usuarios_sesion_sin_deposito) / total_login:.2%}")

        st.subheader("🆕 Nuevos usuarios registrados el día del reporte: {fecha_reporte}")
        if not nuevos_usuarios.empty:
            nuevos_usuarios_info = nuevos_usuarios[['user_id', 'login', 'have_bet', 'total_release_bonus_amount', 'logged_in_day']]
            nuevos_usuarios_info.columns = ['User ID', 'Login', '¿Jugó?', 'Monto Bono Recibido', '¿Inició sesión?']
            st.dataframe(nuevos_usuarios_info)
        else:
            st.write("No se encontraron usuarios nuevos en la fecha del reporte.")

        progress_bar.progress(100, text="✅ Proceso completado")
