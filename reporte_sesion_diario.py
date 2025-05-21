import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Reporte Diario de Sesión de Usuarios", layout="wide")
st.title("📊 Reporte Diario de Sesión de Usuarios")

uploaded_file = st.file_uploader("Subí el archivo Excel del día", type=[".xlsx", ".xls"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Normalizar nombres de columnas a minúsculas para evitar problemas de mayúsculas
        df.columns = df.columns.str.lower()

        # Extraer fecha del campo 'id'
        df['fecha_reporte'] = df['id'].astype(str).str.extract(r'(\d{4}-\d{1,2}-\d{1,2})')[0]
        df['fecha_reporte'] = pd.to_datetime(df['fecha_reporte'], errors='coerce')

        # Asegurar que registration_date sea datetime (sin la hora)
        df['registration_date'] = pd.to_datetime(df['registration_date'], errors='coerce').dt.date

        # Obtener fecha del reporte (asumimos que es la fecha más frecuente)
        fecha_reporte = df['fecha_reporte'].dropna().mode()[0].date() if not df['fecha_reporte'].dropna().empty else None

        # Usuarios que realizaron acciones
        usuarios_login = df[df['logged_in_day'].astype(str).str.lower() == 'yes']
        usuarios_con_apuesta = df[df['have_bet'].astype(str).str.lower() == 'yes']
        usuarios_con_deposito = df[df['total_deposit_amount'] > 0]
        usuarios_con_retiro = df[df['total_withdrawal_amount'] < 0]

        # Métricas generales
        st.subheader("Métricas Generales")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Usuarios que iniciaron sesión", usuarios_login['user_id'].nunique())
        col2.metric("Usuarios que apostaron", usuarios_con_apuesta['user_id'].nunique())
        col3.metric("Usuarios que depositaron", usuarios_con_deposito['user_id'].nunique())
        col4.metric("Usuarios que retiraron", usuarios_con_retiro['user_id'].nunique())

        # Cruces
        st.subheader("Cruces entre acciones")
        user_ids_login = set(usuarios_login['user_id'])
        user_ids_deposito = set(usuarios_con_deposito['user_id'])
        user_ids_apuesta = set(usuarios_con_apuesta['user_id'])

        login_sin_deposito = user_ids_login - user_ids_deposito
        login_sin_apuesta = user_ids_login - user_ids_apuesta
        deposito_sin_apuesta = user_ids_deposito - user_ids_apuesta

        usuarios_activos = df[df['status'].astype(str).str.lower() == 'active']
        activos_con_accion = usuarios_activos[
            (usuarios_activos['total_deposit_amount'] > 0) | (usuarios_activos['have_bet'].astype(str).str.lower() == 'yes')
        ]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Iniciaron sesión pero no depositaron", len(login_sin_deposito))
        col2.metric("Iniciaron sesión pero no apostaron", len(login_sin_apuesta))
        col3.metric("Depositantes que no jugaron", len(deposito_sin_apuesta))
        col4.metric("Usuarios activos con acción", activos_con_accion['user_id'].nunique())

        # Usuarios nuevos
        st.subheader("Usuarios nuevos el día del reporte")
        nuevos = df[df['registration_date'] == fecha_reporte]

        if nuevos.empty:
            st.info("No se encontraron usuarios nuevos en la fecha del reporte.")
        else:
            sin_apuestas = nuevos[nuevos['have_bet'].astype(str).str.lower() != 'yes']
            con_bono = nuevos[nuevos['total_release_bonus_amount'] > 0]
            con_sesion = nuevos[nuevos['logged_in_day'].astype(str).str.lower() == 'yes']
            sin_sesion = nuevos[nuevos['logged_in_day'].astype(str).str.lower() != 'yes']

            st.write(f"Total usuarios nuevos: {nuevos['user_id'].nunique()}")
            st.write(f"Usuarios nuevos sin apuestas: {sin_apuestas['user_id'].nunique()}")
            st.write(f"Usuarios nuevos con bono: {con_bono['user_id'].nunique()}")
            st.write(f"Usuarios nuevos que iniciaron sesión: {con_sesion['user_id'].nunique()}")
            st.write(f"Usuarios nuevos que NO iniciaron sesión: {sin_sesion['user_id'].nunique()}")

            with st.expander("Ver detalle de usuarios nuevos"):
                st.dataframe(nuevos[['user_id', 'registration_date', 'logged_in_day', 'have_bet', 'total_release_bonus_amount']])

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {str(e)}")
