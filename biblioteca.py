import pyodbc
from tabulate import tabulate
from conexionBD import conectar


TABLAS = [
    "Politica_Prestamo",
    "Usuario",
    "Estudiante",
    "Docente",
    "Categoria",
    "Libro",
    "Autor",
    "Libro_Autor",
    "Prestamo",
    "Detalle_Prestamo",
    "Sancion"
]


def mostrar_menu():
    print("\n" + "=" * 55)
    print("SISTEMA DE GESTIÓN DE BIBLIOTECA UNIVERSITARIA")
    print("=" * 55)
    print("1. Visualizar todas las tablas")
    print("2. Insertar un registro")
    print("3. Eliminar un registro")
    print("4. Actualizar un registro")
    print("5. Consultas avanzadas")
    print("6. Consultar historial de préstamos (VIEW)")
    print("7. Salir")
    print("=" * 55)


def mostrar_tabla(cursor, nombre_tabla):
    consulta = f"SELECT * FROM dbo.{nombre_tabla}"
    cursor.execute(consulta)

    filas = cursor.fetchall()
    columnas = [columna[0] for columna in cursor.description]

    print("\n" + "=" * 20)
    print(f"TABLA: {nombre_tabla}")
    print("=" * 20)

    if filas:
        datos = [list(fila) for fila in filas]
        print(tabulate(datos, headers=columnas, tablefmt="grid"))
    else:
        print("La tabla no contiene registros.")


def visualizar_todas_las_tablas(conexion):
    cursor = conexion.cursor()

    try:
        for tabla in TABLAS:
            mostrar_tabla(cursor, tabla)

        print("\nVisualización completada correctamente.")

    except pyodbc.Error as error:
        print("No se pudieron visualizar las tablas.")
        print("Detalle del error:", error)

    finally:
        cursor.close()

def seleccionar_tabla():
    print("\nTABLAS DISPONIBLES")

    for numero, tabla in enumerate(TABLAS, start=1):
        print(f"{numero}. {tabla}")

    print("0. Cancelar")

    opcion = input("Seleccione una tabla: ").strip()

    if opcion == "0":
        return None

    if not opcion.isdigit():
        print("Debe ingresar un número.")
        return None

    posicion = int(opcion) - 1

    if posicion < 0 or posicion >= len(TABLAS):
        print("La tabla seleccionada no existe.")
        return None

    return TABLAS[posicion]


def obtener_columnas_insertables(cursor, nombre_tabla):
    consulta = """
        SELECT
            C.name AS columna,
            TYPE_NAME(C.user_type_id) AS tipo,
            C.is_nullable
        FROM sys.columns AS C
        WHERE C.object_id = OBJECT_ID(?)
          AND C.is_identity = 0
          AND C.is_computed = 0
        ORDER BY C.column_id;
    """

    cursor.execute(consulta, f"dbo.{nombre_tabla}")
    return cursor.fetchall()


def insertar_registro(conexion):
    nombre_tabla = seleccionar_tabla()

    if nombre_tabla is None:
        print("Inserción cancelada.")
        return

    cursor = conexion.cursor()

    try:
        print("\nCONTENIDO ANTES DE LA INSERCIÓN")
        mostrar_tabla(cursor, nombre_tabla)

        columnas = obtener_columnas_insertables(cursor, nombre_tabla)

        nombres_columnas = []
        valores = []

        print(f"\nIngrese los datos para la tabla {nombre_tabla}:")

        for columna, tipo, permite_nulo in columnas:
            condicion = "opcional" if permite_nulo else "obligatorio"

            while True:
                valor = input(
                    f"{columna} - {tipo} ({condicion}): "
                ).strip()

                if valor == "" and permite_nulo:
                    valor = None
                    break

                if valor == "" and not permite_nulo:
                    print("Este campo es obligatorio.")
                    continue

                break

            nombres_columnas.append(f"[{columna}]")
            valores.append(valor)

        columnas_sql = ", ".join(nombres_columnas)
        parametros_sql = ", ".join(["?"] * len(valores))

        consulta = (
            f"INSERT INTO dbo.{nombre_tabla} "
            f"({columnas_sql}) VALUES ({parametros_sql})"
        )

        cursor.execute(consulta, valores)
        conexion.commit()

        print("\nRegistro insertado correctamente.")
        print("\nCONTENIDO DESPUÉS DE LA INSERCIÓN")
        mostrar_tabla(cursor, nombre_tabla)

    except pyodbc.Error as error:
        conexion.rollback()
        print("\nNo se pudo insertar el registro.")
        print("Revise los valores obligatorios, únicos y las relaciones.")
        print("Detalle del error:", error)

    finally:
        cursor.close()
def obtener_claves_primarias(cursor, nombre_tabla):
    consulta = """
        SELECT KCU.COLUMN_NAME
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS TC
        INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KCU
            ON TC.CONSTRAINT_NAME = KCU.CONSTRAINT_NAME
           AND TC.TABLE_SCHEMA = KCU.TABLE_SCHEMA
        WHERE TC.TABLE_SCHEMA = 'dbo'
          AND TC.TABLE_NAME = ?
          AND TC.CONSTRAINT_TYPE = 'PRIMARY KEY'
        ORDER BY KCU.ORDINAL_POSITION;
    """

    cursor.execute(consulta, nombre_tabla)
    return [fila[0] for fila in cursor.fetchall()]


def actualizar_registro(conexion):
    nombre_tabla = seleccionar_tabla()

    if nombre_tabla is None:
        print("Actualización cancelada.")
        return

    cursor = conexion.cursor()

    try:
        print("\nCONTENIDO ANTES DE LA ACTUALIZACIÓN")
        mostrar_tabla(cursor, nombre_tabla)

        claves_primarias = obtener_claves_primarias(
            cursor, nombre_tabla
        )

        if not claves_primarias:
            print("No se encontró la clave primaria de la tabla.")
            return

        valores_clave = []

        for clave in claves_primarias:
            valor = input(f"Ingrese el valor de {clave}: ").strip()
            valores_clave.append(valor)

        columnas = obtener_columnas_insertables(
            cursor, nombre_tabla
        )

        columnas_editables = [
            columna
            for columna, tipo, permite_nulo in columnas
            if columna not in claves_primarias
        ]

        print("\nCOLUMNAS QUE SE PUEDEN ACTUALIZAR")

        for numero, columna in enumerate(
            columnas_editables, start=1
        ):
            print(f"{numero}. {columna}")

        opcion = input("Seleccione una columna: ").strip()

        if not opcion.isdigit():
            print("Selección no válida.")
            return

        posicion = int(opcion) - 1

        if posicion < 0 or posicion >= len(columnas_editables):
            print("La columna seleccionada no existe.")
            return

        columna_elegida = columnas_editables[posicion]
        nuevo_valor = input(
            f"Ingrese el nuevo valor para {columna_elegida}: "
        ).strip()

        condiciones = " AND ".join(
            [f"[{clave}] = ?" for clave in claves_primarias]
        )

        consulta = (
            f"UPDATE dbo.{nombre_tabla} "
            f"SET [{columna_elegida}] = ? "
            f"WHERE {condiciones}"
        )

        parametros = [nuevo_valor] + valores_clave
        cursor.execute(consulta, parametros)

        if cursor.rowcount == 0:
            conexion.rollback()
            print("No se encontró el registro indicado.")
            return

        conexion.commit()

        print("\nRegistro actualizado correctamente.")
        print("\nCONTENIDO DESPUÉS DE LA ACTUALIZACIÓN")
        mostrar_tabla(cursor, nombre_tabla)

    except pyodbc.Error as error:
        conexion.rollback()
        print("\nNo se pudo actualizar el registro.")
        print("Detalle del error:", error)

    finally:
        cursor.close()
def eliminar_registro(conexion):
    nombre_tabla = seleccionar_tabla()

    if nombre_tabla is None:
        print("Eliminación cancelada.")
        return

    cursor = conexion.cursor()

    try:
        print("\nCONTENIDO ANTES DE LA ELIMINACIÓN")
        mostrar_tabla(cursor, nombre_tabla)

        claves_primarias = obtener_claves_primarias(
            cursor, nombre_tabla
        )

        if not claves_primarias:
            print("No se encontró la clave primaria de la tabla.")
            return

        valores_clave = []

        for clave in claves_primarias:
            valor = input(f"Ingrese el valor de {clave}: ").strip()
            valores_clave.append(valor)

        condiciones = " AND ".join(
            [f"[{clave}] = ?" for clave in claves_primarias]
        )

        confirmacion = input(
            "¿Confirma que desea eliminar el registro? (S/N): "
        ).strip().upper()

        if confirmacion != "S":
            print("Eliminación cancelada por el usuario.")
            return

        consulta = (
            f"DELETE FROM dbo.{nombre_tabla} "
            f"WHERE {condiciones}"
        )

        cursor.execute(consulta, valores_clave)

        if cursor.rowcount == 0:
            conexion.rollback()
            print("No se encontró el registro indicado.")
            return

        conexion.commit()

        print("\nRegistro eliminado correctamente.")
        print("\nCONTENIDO DESPUÉS DE LA ELIMINACIÓN")
        mostrar_tabla(cursor, nombre_tabla)

    except pyodbc.IntegrityError as error:
        conexion.rollback()
        print("\nNo se puede eliminar el registro.")
        print(
            "El registro está relacionado con información "
            "de otra tabla mediante una clave foránea."
        )
        print("Detalle del error:", error)

    except pyodbc.Error as error:
        conexion.rollback()
        print("\nOcurrió un error durante la eliminación.")
        print("Detalle del error:", error)

    finally:
        cursor.close()

def consultar_historial_vista(conexion):
    cursor = conexion.cursor()

    try:
        consulta = """
            SELECT
                id_prestamo AS ID,
                nombre_usuario AS Usuario,
                tipo_usuario AS Tipo,
                libro AS Libro,
                fecha_prestamo AS Fecha,
                estado_prestamo AS Estado,
                sancion AS Sancion
            FROM dbo.vw_HistorialPrestamos
            ORDER BY id_prestamo;
        """

        cursor.execute(consulta)

        filas = cursor.fetchall()
        columnas = [
            columna[0] for columna in cursor.description
        ]

        print("\n" + "=" * 55)
        print("HISTORIAL GENERAL DE PRÉSTAMOS")
        print("=" * 55)

        if filas:
            datos = [list(fila) for fila in filas]

            print(
                tabulate(
                    datos,
                    headers=columnas,
                    tablefmt="grid"
                )
            )
        else:
            print("La vista no contiene información.")

        print("\nVista consultada correctamente.")

    except pyodbc.Error as error:
        print("No fue posible consultar la vista.")
        print("Detalle del error:", error)

    finally:
        cursor.close()

def mostrar_resultado_consulta(cursor, titulo, consulta):
    cursor.execute(consulta)

    filas = cursor.fetchall()
    columnas = [columna[0] for columna in cursor.description]

    print("\n" + "=" * 60)
    print(titulo)
    print("=" * 60)

    if filas:
        datos = [list(fila) for fila in filas]

        print(
            tabulate(
                datos,
                headers=columnas,
                tablefmt="grid"
            )
        )
    else:
        print("No se encontraron resultados.")


def consultas_avanzadas(conexion):
    cursor = conexion.cursor()

    try:
        while True:
            print("\n" + "=" * 60)
            print("CONSULTAS AVANZADAS")
            print("=" * 60)
            print("1. Top 3 usuarios con más préstamos (CTE)")
            print("2. Libros ordenados según su demanda")
            print("3. Préstamos realizados en enero y mayo")
            print("4. Resumen de sanciones")
            print("5. Volver al menú principal")
            print("=" * 60)

            opcion = input(
                "Seleccione una consulta: "
            ).strip()

            if opcion == "1":
                consulta = """
                    ;WITH PrestamosPorUsuario AS
                    (
                        SELECT
                            U.id_usuario,
                            CONCAT(
                                U.nombres, ' ', U.apellidos
                            ) AS Usuario,
                            U.tipo_usuario AS Tipo,
                            COUNT(
                                P.id_prestamo
                            ) AS TotalPrestamos
                        FROM Usuario AS U
                        LEFT JOIN Prestamo AS P
                            ON U.id_usuario = P.id_usuario
                        GROUP BY
                            U.id_usuario,
                            U.nombres,
                            U.apellidos,
                            U.tipo_usuario
                    )
                    SELECT TOP 3
                        id_usuario AS ID,
                        Usuario,
                        Tipo,
                        TotalPrestamos AS Prestamos
                    FROM PrestamosPorUsuario
                    ORDER BY
                        TotalPrestamos DESC,
                        id_usuario ASC;
                """

                mostrar_resultado_consulta(
                    cursor,
                    "TOP 3 USUARIOS CON MÁS PRÉSTAMOS",
                    consulta
                )

            elif opcion == "2":
                consulta = """
                    SELECT
                        L.id_libro AS ID,
                        L.titulo AS Libro,
                        ISNULL(
                            SUM(DP.cantidad), 0
                        ) AS Demanda
                    FROM Libro AS L
                    LEFT JOIN Detalle_Prestamo AS DP
                        ON L.id_libro = DP.id_libro
                    GROUP BY
                        L.id_libro,
                        L.titulo
                    ORDER BY
                        Demanda DESC,
                        L.titulo ASC;
                """

                mostrar_resultado_consulta(
                    cursor,
                    "LIBROS ORDENADOS SEGÚN SU DEMANDA",
                    consulta
                )

            elif opcion == "3":
                consulta = """
                    SELECT
                        P.id_prestamo AS ID,
                        CONCAT(
                            U.nombres, ' ', U.apellidos
                        ) AS Usuario,
                        L.titulo AS Libro,
                        P.fecha_prestamo AS Fecha
                    FROM Prestamo AS P
                    INNER JOIN Usuario AS U
                        ON P.id_usuario = U.id_usuario
                    INNER JOIN Detalle_Prestamo AS DP
                        ON P.id_prestamo = DP.id_prestamo
                    INNER JOIN Libro AS L
                        ON DP.id_libro = L.id_libro
                    WHERE MONTH(P.fecha_prestamo) IN (1, 5)
                    ORDER BY P.fecha_prestamo;
                """

                mostrar_resultado_consulta(
                    cursor,
                    "PRÉSTAMOS REALIZADOS EN ENERO Y MAYO",
                    consulta
                )

            elif opcion == "4":
                consulta = """
                    SELECT
                        tipo_sancion AS Tipo,
                        COUNT(*) AS Cantidad,
                        SUM(monto) AS MontoTotal,
                        AVG(monto) AS MontoPromedio
                    FROM Sancion
                    GROUP BY tipo_sancion
                    ORDER BY
                        Cantidad DESC,
                        MontoTotal DESC;
                """

                mostrar_resultado_consulta(
                    cursor,
                    "RESUMEN DE SANCIONES",
                    consulta
                )

            elif opcion == "5":
                print(
                    "Regresando al menú principal..."
                )
                break

            else:
                print(
                    "Opción no válida. Intente nuevamente."
                )

    except pyodbc.Error as error:
        print("No fue posible ejecutar la consulta.")
        print("Detalle del error:", error)

    finally:
        cursor.close()

def main():
    try:
        conexion = conectar()
        print("Conexión con BibliotecaUniversitaria establecida.")

        while True:
            mostrar_menu()
            opcion = input("Seleccione una opción: ").strip()

            if opcion == "1":
                visualizar_todas_las_tablas(conexion)

            elif opcion == "2":
                insertar_registro(conexion)

            elif opcion == "3":
                eliminar_registro(conexion)

            elif opcion == "4":
                actualizar_registro(conexion)
            elif opcion == "5":
                consultas_avanzadas(conexion)

            elif opcion == "6":
                consultar_historial_vista(conexion)
            elif opcion == "7":
                print("Cerrando el sistema...")
                break

            else:
                print("Opción no válida. Intente nuevamente.")

        conexion.close()

    except pyodbc.Error as error:
        print("No fue posible conectar con la base de datos.")
        print("Detalle del error:", error)


if __name__ == "__main__":
    main()