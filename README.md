# Sistema de Información – Parqueadero Autos Colombia

## Manuela Tangarife Zapata

## Sobre el proyecto

Autos Colombia es un proyecto que consiste en el desarrollo de un sistema de información para la administración de un parqueadero que presta servicio mensual. Su propósito es facilitar el registro, control y seguimiento de las operaciones del establecimiento, además de mantener organizada la información de los vehículos, usuarios, movimientos y celdas de parqueo.

El proyecto se desarrolla por etapas, incorporando nuevas funcionalidades y mejoras que permiten ampliar las capacidades del sistema de acuerdo con los requerimientos planteados en cada evidencia de aprendizaje.

---

# Evidencia de Aprendizaje 1 – Diseño del Sistema de Información: Iteración 1

## Descripción

En esta primera etapa desarrollé las funcionalidades principales para gestionar las operaciones de entrada y salida de los vehículos del parqueadero.

## Tecnologías utilizadas

Para el desarrollo del proyecto utilicé las siguientes tecnologías:

- **Python:** lenguaje de programación utilizado para construir la aplicación.
- **Flask:** framework empleado para gestionar las rutas y funcionalidades del sistema.
- **PostgreSQL:** sistema gestor de bases de datos encargado de almacenar la información.
- **HTML:** utilizado para presentar las interfaces de la aplicación.
- **CSS:** utilizado para definir el diseño y la apariencia visual del aplicativo.
- **psycopg:** biblioteca que permite la conexión entre Python y PostgreSQL.
- **python-dotenv:** herramienta utilizada para cargar la configuración local desde variables de entorno.

## Funcionalidades principales

El sistema cuenta con las siguientes funcionalidades:

- Registro de vehículos y sus datos básicos.
- Registro de entradas con asignación automática de una celda disponible.
- Registro de salidas y liberación de la celda ocupada.
- Registro de novedades asociadas a los movimientos de los vehículos.
- Consulta del historial de entradas, salidas y novedades.
- Visualización del estado general del parqueadero, incluyendo las celdas disponibles y ocupadas.

## Estructura del proyecto

El proyecto está organizado en carpetas y archivos que facilitan la ubicación de sus elementos:

- **`app/`:** contiene el código Python de la aplicación, las plantillas HTML, los archivos CSS y las funciones relacionadas con la conexión y las consultas a la base de datos.
- **`database/`:** contiene el script SQL para crear las tablas, relaciones y restricciones de la base de datos.
- **`docs/`:** reúne la documentación del proyecto, los informes y el modelo físico de la base de datos.
- **`tests/`:** carpeta destinada a la organización de pruebas del sistema.
- **`requirements.txt`:** contiene las dependencias de Python utilizadas por la aplicación.
- **`.gitignore`:** especifica los archivos y carpetas locales que no deben incluirse en el repositorio.

## Base de datos

La base de datos se llama `autos_colombia` y está desarrollada en PostgreSQL. En esta primera iteración, su estructura se compone de cuatro tablas principales: `vehiculos`, `celdas`, `movimientos` y `novedades`.

Estas tablas permiten relacionar los vehículos con sus movimientos, identificar las celdas utilizadas y almacenar las novedades que se presenten durante el servicio. El script de creación se encuentra en la carpeta `database/`, mientras que el modelo físico puede encontrarse en `docs/`.

## Requisitos y configuración

Para ejecutar el sistema se requiere Python 3 y PostgreSQL, además de una base de datos denominada `autos_colombia`.

La conexión utiliza variables de entorno definidas en un archivo local `.env`, donde se configuran los datos de conexión a PostgreSQL y la clave secreta de Flask. Este archivo es de uso local y no forma parte de los archivos compartidos en el repositorio.

Las dependencias necesarias se encuentran especificadas en `requirements.txt`.

## Ejecución de la aplicación

Para ejecutar el proyecto, primero se debe preparar la base de datos y configurar las variables de entorno. Luego, desde la carpeta raíz del proyecto, se deben instalar las dependencias:

```bash
pip install -r requirements.txt
```

Una vez instaladas, la aplicación puede ejecutarse mediante el siguiente comando:

```bash
python app/app.py
```

Después de iniciar el servidor, el sistema se puede consultar desde el navegador en:

`http://127.0.0.1:5000`

---

# Evidencia de Aprendizaje 2 – Diseño del Sistema de Información: Iteración 2

## Descripción

En esta segunda etapa amplié las funcionalidades de Autos Colombia mediante la incorporación de los módulos de gestión de usuarios y gestión de celdas. El objetivo fue complementar las operaciones desarrolladas en la primera iteración y facilitar la administración de la información del parqueadero.

## Funcionalidades incorporadas

**Gestión de usuarios**

- Registro de usuarios con sus datos personales y de contacto.
- Consulta del listado de usuarios registrados.
- Edición de la información de los usuarios.
- Activación y desactivación de usuarios.
- Validación para evitar el registro de documentos duplicados.

**Gestión de celdas**

- Registro de nuevas celdas.
- Consulta de las celdas registradas.
- Identificación de celdas disponibles, ocupadas e inactivas.
- Activación y desactivación de celdas.
- Validación para impedir la desactivación de celdas que tengan un vehículo estacionado.

## Actualización de la base de datos

Para esta iteración amplié la estructura de la base de datos `autos_colombia` mediante la incorporación de la tabla `usuarios` y los ajustes necesarios para relacionar los usuarios con los vehículos y administrar el estado de funcionamiento de las celdas.

La base de datos conserva las tablas y funcionalidades desarrolladas durante la primera iteración.

## Diseño y documentación

Como parte de esta etapa también elaboré los siguientes elementos:

- Requisitos funcionales y no funcionales.
- Historias de usuario y criterios de aceptación.
- Diagramas UML de casos de uso para la gestión de usuarios y celdas.
- Diagramas de secuencia correspondientes a las dos iteraciones.
- Diagrama de componentes del sistema.
- Mockups de las interfaces de gestión de usuarios y celdas.
- Plan de pruebas para verificar las nuevas funcionalidades.

## Pruebas realizadas

Se realizaron ocho casos de prueba relacionados con el registro, consulta, edición y cambio de estado de usuarios y celdas. Todas las pruebas obtuvieron resultados aprobados.

---

#### Link Video de Sustentación: `https://youtu.be/YIkJbHXBQaw`

---
