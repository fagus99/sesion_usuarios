import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Reporte Diario de Usuarios", layout="wide")
st.title("📊 Reporte Diario de Actividad de Usuarios")

uploaded_file = st.file_uploader("Subí el archivo Excel con el resumen diario de usuarios", type=[".xlsx", ".xls"])

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    return output.getvalue()

if uploaded_file:
    if st.button("Iniciar procesamiento"):
        progress_bar = st.progress(0, text="Procesando archivo...")

        df = pd.read_excel(uploaded_file)

        # Mapeo de columnas del archivo (español) a los nombres internos usados en el código
        column_map = {
            'ID': 'id',
            'ID del Cliente': 'client_id',
            'ID de Usuario': 'user_id',
            'Nombre de Usuario': 'login',
            'Fecha': 'fecha',
            'Fecha de Registro': 'registration_date',
            'Último Acceso': 'last_login_date',
            'Acceso en el día': 'logged_in_day',
            'Ha Apostado': 'have_bet',
            'Estado': 'status',
            'Total Depositado': 'total_deposit_amount',
            'Total Retirado': 'total_withdrawal_amount',
            'Bonos Liberados': 'total_release_bonus_amount',
            'Número de Sesiones': 'session_number',
            'Tiempo de Sesión (Minutos)': 'session_time_minutes',
            'Última Recarga': 'last_deposit_date',
        }

        df.rename(columns=column_map, inplace=True)
        df.columns = [col.lower().strip() for col in df.columns]

        progress_bar.progress(10, text="Procesando fechas...")

        df['id'] = df['id'].astype(str).str.extract(r'(\d{4}-\d{1,2}-\d{1,2})')
        df['id'] = pd.to_datetime(df['id'], errors='coerce').dt.date
        fecha_reporte = df['id'].iloc[0]

        df['registration_date'] = pd.to_datetime(df['registration_date'], errors='coerce').dt.date
        df['last_login_date'] = pd.to_datetime(df['last_login_date'], errors='coerce')
        df['last_deposit_date'] = pd.to_datetime(df['last_deposit_date'], errors='coerce')

        progress_bar.progress(30, text="Calculando métricas...")

        df['logged_in_day'] = df['logged_in_day'].astype(str).str.lower().fillna("no")
        df['have_bet'] = df['have_bet'].astype(str).str.lower().fillna("no")

        usuarios_login = df[df['logged_in_day'] == 'yes']
        usuarios_apostaron = df[df['have_bet'] == 'yes']
        usuarios_depositaron = df[df['total_deposit_amount'] > 0]
        usuarios_retiraron = df[df['total_withdrawal_amount'] < 0]

        login_sin_deposito = df[(df['logged_in_day'] == 'yes') & (df['total_deposit_amount'] <= 0)]
        login_sin_apuesta = df[(df['logged_in_day'] == 'yes') & (df['have_bet'] != 'yes')]
        deposito_sin_apuesta = df[(df['total_deposit_amount'] > 0) & (df['have_bet'] != 'yes')]

        usuarios_activos = df[df['status'].astype(str).str.upper() == 'ACTIVE']
        usuarios_activos_con_accion = usuarios_activos[
            (usuarios_activos['total_deposit_amount'] > 0) | (usuarios_activos['have_bet'] == 'yes')
        ]

        login_con_apuesta = df[(df['logged_in_day'] == 'yes') & (df['have_bet'] == 'yes')]
        deposito_con_apuesta = df[(df['total_deposit_amount'] > 0) & (df['have_bet'] == 'yes')]

        progress_bar.progress(60, text="Detectando nuevos usuarios...")

        nuevos_usuarios = df[df['registration_date'] == fecha_reporte]
        nuevos_no_jugaron = nuevos_usuarios[nuevos_usuarios['have_bet'] != 'yes']
        nuevos_recibieron_bono = nuevos_usuarios[nuevos_usuarios['total_release_bonus_amount'] > 0]
        nuevos_login = nuevos_usuarios[nuevos_usuarios['logged_in_day'] == 'yes']
        nuevos_sin_login = nuevos_usuarios[nuevos_usuarios['logged_in_day'] != 'yes']

        recibieron_bono_jugaron = df[(df['total_release_bonus_amount'] > 0) & (df['have_bet'] == 'yes')]
        recibieron_bono_no_jugaron = df[(df['total_release_bonus_amount'] > 0) & (df['have_bet'] != 'yes')]

        progress_bar.progress(80, text="Visualizando resultados...")

        st.subheader("📌 Métricas Generales")
        st.write(f"Usuarios que iniciaron sesión: {len(usuarios_login)}")
        st.write(f"Usuarios que apostaron: {len(usuarios_apostaron)}")
        st.write(f"Usuarios que depositaron: {len(usuarios_depositaron)}")
        st.write(f"Usuarios que retiraron: {len(usuarios_retiraron)}")

        st.subheader("🔀 Cruces entre acciones")
        st.write(f"Iniciaron sesión pero no depositaron: {len(login_sin_deposito)}")
        st.write(f"Iniciaron sesión pero no apostaron: {len(login_sin_apuesta)}")
        st.write(f"Iniciaron sesión y apostaron: {len(login_con_apuesta)}")
        st.write(f"Depositantes que no jugaron: {len(deposito_sin_apuesta)}")
        st.write(f"Depositantes que apostaron: {len(deposito_con_apuesta)}")
        st.write(f"Usuarios activos con alguna acción: {len(usuarios_activos_con_accion)}")
        st.write(f"Recibieron bono y jugaron: {len(recibieron_bono_jugaron)}")
        st.write(f"Recibieron bono y no jugaron: {len(recibieron_bono_no_jugaron)}")

        st.subheader("📈 Porcentajes sobre usuarios que iniciaron sesión")
        total_login = len(usuarios_login)
        if total_login > 0:
            st.write(f"% que apostaron: {(len(login_con_apuesta) / total_login):.2%}")
            st.write(f"% que depositaron: {(len(usuarios_depositaron[usuarios_depositaron['logged_in_day'] == 'yes']) / total_login):.2%}")
            st.write(f"% que no apostaron: {len(login_sin_apuesta) / total_login:.2%}")
            st.write(f"% que no depositaron: {len(login_sin_deposito) / total_login:.2%}")
        else:
            st.warning("⚠️ No se registraron sesiones de usuario.")

        st.subheader(f"🆕 Nuevos usuarios registrados el día del reporte: {fecha_reporte}")
        if not nuevos_usuarios.empty:
            nuevos_usuarios_info = nuevos_usuarios[['user_id', 'login', 'have_bet', 'total_release_bonus_amount', 'logged_in_day']]
            nuevos_usuarios_info = nuevos_usuarios_info.copy()
            nuevos_usuarios_info.columns = ['User ID', 'Login', '¿Jugó?', 'Monto Bono Recibido', '¿Inició sesión?']
            st.dataframe(nuevos_usuarios_info)
            st.session_state["nuevos_usuarios_df"] = nuevos_usuarios_info
            st.session_state["nuevos_usuarios_excel"] = to_excel(nuevos_usuarios_info)

            st.download_button("📥 Descargar tabla de nuevos usuarios",
                               data=st.session_state["nuevos_usuarios_excel"],
                               file_name="nuevos_usuarios.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.write("No se encontraron usuarios nuevos en la fecha del reporte.")

        st.subheader("👀 Usuarios que iniciaron sesión pero NO jugaron (solo si fue el día del reporte)")
        if not login_sin_apuesta.empty:
            login_sin_apuesta = login_sin_apuesta.copy()
            login_sin_apuesta['hora_login'] = login_sin_apuesta['last_login_date'].dt.strftime('%H:%M:%S')
            login_sin_apuesta_dia = login_sin_apuesta[login_sin_apuesta['last_login_date'].dt.date == fecha_reporte]

            columnas = ['user_id', 'login', 'hora_login', 'session_number', 'session_time_minutes',
                        'total_release_bonus_amount', 'logged_in_day', 'have_bet']
            tabla_login_no_jugaron = login_sin_apuesta_dia[columnas].copy()
            tabla_login_no_jugaron.columns = ['User ID', 'Login', 'Hora Login', 'Cantidad de Sesiones',
                                              'Duración de Sesión (min)', 'Monto Bono Recibido',
                                              '¿Inició sesión?', '¿Jugó?']

            st.dataframe(tabla_login_no_jugaron)

            st.session_state["login_no_jugaron_excel"] = to_excel(tabla_login_no_jugaron)
            st.download_button(
                "📥 Descargar tabla de usuarios que iniciaron sesión pero NO jugaron",
                data=st.session_state["login_no_jugaron_excel"],
                file_name="usuarios_login_no_jugaron.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.subheader("💰 Usuarios que depositaron pero NO jugaron")
        st.caption("Ordenados por hora de depósito. Los que depositaron cerca de las 00:00 hs pueden haber jugado pasada la medianoche.")
        if not deposito_sin_apuesta.empty:
            dep_no_jugaron = deposito_sin_apuesta.copy()
            dep_no_jugaron['hora_deposito'] = dep_no_jugaron['last_deposit_date'].dt.strftime('%H:%M:%S')
            dep_no_jugaron['alerta_medianoche'] = dep_no_jugaron['last_deposit_date'].apply(
                lambda x: '⚠️ Depósito tardío' if pd.notna(x) and x.hour >= 22 else ''
            )
            dep_no_jugaron = dep_no_jugaron.sort_values('last_deposit_date', ascending=False)

            tabla_dep_no_jugaron = dep_no_jugaron[[
                'user_id', 'login', 'hora_deposito', 'alerta_medianoche',
                'total_deposit_amount', 'session_number', 'total_release_bonus_amount'
            ]].copy()
            tabla_dep_no_jugaron.columns = [
                'User ID', 'Login', 'Hora Depósito', 'Alerta',
                'Monto Depositado', 'Cant. Sesiones', 'Bono Recibido'
            ]

            st.dataframe(tabla_dep_no_jugaron, use_container_width=True)

            tardios = dep_no_jugaron[dep_no_jugaron['last_deposit_date'].apply(
                lambda x: pd.notna(x) and x.hour >= 22
            )]
            if len(tardios) > 0:
                st.info(f"⚠️ {len(tardios)} usuario(s) depositaron después de las 22:00 hs — es posible que hayan jugado pasada la medianoche.")

            st.session_state["dep_no_jugaron_excel"] = to_excel(tabla_dep_no_jugaron)
            st.download_button(
                "📥 Descargar tabla de depositantes que no jugaron",
                data=st.session_state["dep_no_jugaron_excel"],
                file_name="depositantes_no_jugaron.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.write("Todos los usuarios que depositaron también jugaron.")

        progress_bar.progress(100, text="✅ Proceso completado")
