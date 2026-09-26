import pyodbc


def conectar():
    """Crea y devuelve la conexión con SQL Server."""
    return pyodbc.connect(
        "Driver={ODBC Driver 18 for SQL Server};"
        "Server=localhost\\SQLEXPRESS01;"
        "Database=BibliotecaUniversitaria;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )


if __name__ == "__main__":
    try:
        conexion = conectar()
        cursor = conexion.cursor()

        cursor.execute("SELECT COUNT(*) FROM Usuario")
        total_usuarios = cursor.fetchone()[0]

        print("Conexión realizada correctamente.")
        print("Total de usuarios registrados:", total_usuarios)

        cursor.close()
        conexion.close()

    except pyodbc.Error as error:
        print("No se pudo conectar con la base de datos.")
        print("Detalle del error:", error)