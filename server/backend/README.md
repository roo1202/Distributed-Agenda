├── backend/               # Backend (FastAPI)
│   ├── app/               # Código principal de la aplicación
│   │   ├── __init__.py    # Inicialización del paquete
│   │   ├── main.py        # Punto de entrada para FastAPI
│   │   ├── api/           # Rutas y controladores de la API
│   │   │   ├── __init__.py
│   │   │   ├── v1/        # Versionamiento de la API
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py # Rutas principales
│   │   ├── core/          # Configuración y lógica central
│   │   │   ├── __init__.py
│   │   │   ├── config.py  # Configuración del proyecto
│   │   │   ├── security.py # Gestión de seguridad (e.g., JWT)
│   │   ├── models/        # Modelos de la base de datos
│   │   │   ├── __init__.py
│   │   │   ├── user.py    # Ejemplo de modelo
│   │   ├── schemas/       # Esquemas de Pydantic
│   │   │   ├── __init__.py
│   │   │   ├── user.py    # Ejemplo de esquema
│   │   ├── services/      # Lógica de negocio y servicios
│   │   │   ├── __init__.py
│   │   │   ├── user_service.py # Ejemplo de servicio
│   │   ├── db/            # Configuración de la base de datos
│   │   │   ├── __init__.py
│   │   │   ├── base.py    # Base de datos y ORM
│   │   │   ├── session.py # Gestión de la sesión
│   ├── tests/             # Tests unitarios y funcionales
│   │   ├── __init__.py
│   │   ├── test_user.py   # Ejemplo de test
│   ├── Dockerfile         # Dockerfile para el backend
│   ├── requirements.txt   # Dependencias del backend
│   ├── .env               # Configuración de entorno
│   └── README.md          # Documentación del backend
