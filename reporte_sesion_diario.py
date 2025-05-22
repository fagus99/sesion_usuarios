import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Reporte Diario de Usuarios", layout="wide")
st.title("📊 Reporte Diario de Actividad de Usuarios")

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Nuevos Usuarios')
        # NO hacer writer.save() acá, con 'with' es automático
    processed_data = output.getvalue()
    return processed_data

uploaded_file = st.file_uploader("Subí el archivo Excel con el resumen diario de usuarios", type=[".xlsx", ".xls"])

if uploaded_file:
    if st.button("Iniciar procesamiento"):
        progress_bar = st.progress(0, text="Procesando archivo...")

        df = pd.read_excel(uploaded_file)
        # Estandarizo columnas a minúsculas
        df.columns = [col.lower() for col in df.columns]

        progress_bar.progress(10, text="Limpiando columnas de fecha...")
        # Extraer fecha del campo 'id'
        df['id'] = df['id'].astype(str).str.extract(r'(\d{4}-\d{1,2}-\d{1,2})')
        df['id'] = pd.to_datetime(df['id'], errors='coerce').dt.date
        fecha_reporte = df['id'].iloc[0]

        # Fecha registro
        df['registration_date'] = pd.to_datetime(df['registration_date'], errors='coerce').dt.date

        progress_bar.progress(30, text="Calculando métricas generales...")

        # Filtrar usuarios que iniciaron sesión
        usuarios_login = df[df['logged_in_day'].str.lower() == 'yes']

        # Asegurar que columnas numéricas no tengan NaN
        df['total_deposit_amount'] = pd.to_numeric(df['total_deposit_amount'], errors='coerce').fillna(0)
        df['total_withdrawal_amount'] = pd.to_numeric(df['total_withdrawal_amount'], errors='coerce').fillna(0)

        # Usuarios que depositaron (total_deposit_amount > 0)
        usuarios_depositaron = df[df['total_deposit_amount'] > 0]

        # Usuarios que retiraron (total_withdrawal_amount < 0)
        usuarios_retiraron = df[df['total_withdrawal_amount'] < 0]

        # Usuarios que apostaron (have_bet == 'yes')
        usuarios_apostaron = df[df['have_bet'].str.lower() == 'yes']

        # Cruces importantes
        usuarios_sesion_sin_deposito = usuarios_login[~usuarios_login['customer_id'].isin(usuarios_depositaron['customer_id'])]
        usuarios_sesion_sin_apuesta = usuarios_login[~usuarios_login['customer_id'].isin(usuarios_apostaron['customer_id'])]
        usuarios_depositaron_no_jugaron = usuarios_depositaron[~usuarios_depositaron['customer_id'].isin(usuarios_apostaron['customer_id'])]

        # Usuarios activos con alguna acción
        usuarios_activos = df[df['status'].str.lower() == 'active']
        usuarios_activos_con_accion = usuarios_activos[
            (usuarios_activos['total_deposit_amount'] > 0) | (usuarios_activos['have_bet'].str.lower() == 'yes')
        ]

        progress_bar.progress(60, text="Detectando usuarios nuevos...")
        nuevos_usuarios = df[df['registration_date'] == fecha_reporte]
        nuevos_no_jugaron = nuevos_usuarios[nuevos_usuarios['have_bet'].str.lower() != 'yes']
        nuevos_recibieron_bono = nuevos_usuarios[nuevos_usuarios['total_release_bonus_amount'] > 0]
        nuevos_login = nuevos_usuarios[nuevos_usuarios['logged_in_day'].str.lower() == 'yes']
        nuevos_sin_login = nuevos_usuarios[nuevos_usuarios['logged_in_day'].str.lower() != 'yes']

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

        # Métricas adicionales de cruces
        login_con_apuesta = usuarios_login[usuarios_login['have_bet'].str.lower() == 'yes']
        login_sin_apuesta = usuarios_login[usuarios_login['have_bet'].str.lower() != 'yes']

        depositaron_con_apuesta = usuarios_depositaron[usuarios_depositaron['have_bet'].str.lower() == 'yes']
        depositaron_sin_apuesta = usuarios_depositaron[usuarios_depositaron['have_bet'].str.lower() != 'yes']

        st.write(f"Usuarios que iniciaron sesión y apostaron: {len(login_con_apuesta)}")
        st.write(f"Usuarios que iniciaron sesión y NO apostaron: {len(login_sin_apuesta)}")
        st.write(f"Usuarios que depositaron y apostaron: {len(depositaron_con_apuesta)}")
        st.write(f"Usuarios que depositaron y NO apostaron: {len(depositaron_sin_apuesta)}")

        st.subheader("📈 Porcentajes sobre usuarios que iniciaron sesión")
        total_login = len(usuarios_login)
        if total_login > 0:
            st.write(f"% que apostaron: {len(login_con_apuesta) / total_login:.2%}")
            st.write(f"% que depositaron: {len(usuarios_depositaron[usuarios_depositaron['customer_id'].isin(usuarios_login['customer_id'])]) / total_login:.2%}")
            st.write(f"% que no apostaron: {len(login_sin_apuesta) / total_login:.2%}")
            st.write(f"% que no depositaron: {len(usuarios_sesion_sin_deposito) / total_login:.2%}")
        else:
            st.warning("⚠️ No se registraron sesiones de usuario.")

        st.subheader(f"🆕 Nuevos usuarios registrados el día del reporte: {fecha_reporte}")
        if not nuevos_usuarios.empty:
            nuevos_usuarios_info = nuevos_usuarios[['user_id', 'login', 'have_bet', 'total_release_bonus_amount', 'logged_in_day']]
            nuevos_usuarios_info.columns = ['User ID', 'Login', '¿Jugó?', 'Monto Bono Recibido', '¿Inició sesión?']
            st.dataframe(nuevos_usuarios_info)

            st.session_state["nuevos_usuarios_df"] = nuevos_usuarios_info
            st.session_state["nuevos_usuarios_excel"] = to_excel(nuevos_usuarios_info)

        else:
            st.write("No se encontraron usuarios nuevos en la fecha del reporte.")

        progress_bar.progress(100, text="✅ Proceso completado")

if "nuevos_usuarios_excel" in st.session_state:
    st.download_button("📥 Descargar tabla de nuevos usuarios",
                       data=st.session_state["nuevos_usuarios_excel"],
                       file_name="nuevos_usuarios.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
