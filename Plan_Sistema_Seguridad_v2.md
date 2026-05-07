# PLAN INTEGRAL DEL SISTEMA
## Control de Entrada y Salida — Personal de Seguridad (SENATI)

| Propiedad | Valor |
|---|---|
| **Stack Backend** | Django 4.x (Python) |
| **Base de Datos** | Firebase Firestore (NoSQL) |
| **Frontend** | Django Templates + Tailwind CSS |
| **Versión del Plan** | v2.0 — Mayo 2026 |

---

## 1. OBJETIVO DEL SISTEMA

Diseñar e implementar un sistema web con Django que permita registrar, almacenar y consultar el control de entrada y salida del personal de seguridad, capturando:

- Hora de entrada
- Nombre y apellido del personal
- Hora de salida
- Motivo de salida
- Área a la que se dirige
- **Turno de trabajo asignado** *(mejora v2.0)*

El sistema debe garantizar **seguridad, trazabilidad y disponibilidad 24/7**.

---

## 2. STACK TECNOLÓGICO

| Capa | Tecnología | Propósito |
|---|---|---|
| **Backend** | Django 4.x (Python) | Servidor principal, lógica de negocio, generación de reportes |
| **Base de datos** | Firebase Firestore (NoSQL) | Almacenamiento en la nube vía firebase-admin SDK |
| **Autenticación** | Firebase Authentication | Manejo de sesiones y tokens JWT |
| **Frontend** | Django Templates + Tailwind CSS | HTML renderizado en servidor |
| **Tiempo real** | Firestore onSnapshot (JavaScript) | Actualizaciones del dashboard sin recargar |
| **Reportes Excel** | openpyxl | Exportación a .xlsx y .csv |
| **Reportes PDF** | WeasyPrint o ReportLab | Generación de PDF para auditorías |

---

## 3. REQUISITOS FUNCIONALES

| Código | Requisito | Descripción | Estado |
|---|---|---|---|
| RF-01 | Registro de entrada | Registrar hora + nombre del guardia | ✅ Cubierto |
| RF-02 | Registro de salida | Registrar hora de salida + turno | ✅ Cubierto |
| RF-03 | Motivo de salida | Combobox con 6 opciones + campo libre | ✅ Cubierto |
| RF-04 | Área de destino | Selección de catálogo predefinido | ✅ Cubierto |
| RF-05 | Consulta registros | Filtros: fecha, nombre, motivo, área | ✅ Cubierto |
| RF-06 | Reportes | Excel/CSV + PDF con rango de fechas | ✅ Mejorado |
| RF-07 | Seguridad y roles | Admin / Supervisor / Consulta + Auth | ✅ Mejorado |

---

## 4. ROLES Y PERMISOS (RF-07 mejorado)

El sistema contempla **4 roles** con permisos diferenciados. El rol se almacena en el token de Firebase Auth como **custom claims** y se verifica en cada vista Django mediante un decorador `@firebase_auth_required`.

| Rol | Registro E/S | Ver Dashboard | Ver Logs | Reportes | CRUD Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| **Administrador** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Operador Caseta** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Supervisor** | ❌ | ✅ | ✅ | ✅ | ❌ |
| **Consulta** | ❌ | ❌ | ✅ (solo lectura) | ✅ | ❌ |

- **Administrador**: acceso total, gestiona catálogos y cuentas del sistema.
- **Operador de Caseta**: registra entradas y salidas en tiempo real desde la caseta.
- **Supervisor**: monitorea el dashboard y genera reportes, sin poder registrar.
- **Consulta**: acceso de solo lectura al historial de logs para auditorías.

---

## 5. GESTIÓN DE TURNOS *(mejora nueva v2.0)*

El sistema soporta **4 tipos de turno**. Cada registro de entrada queda vinculado al turno activo en ese momento, permitiendo reportes consolidados por turno.

| Código | Nombre del Turno | Horario | Descripción |
|---|---|---|---|
| T-01 | Mañana | 06:00 – 14:00 | Turno de apertura de instalaciones |
| T-02 | Tarde | 14:00 – 22:00 | Turno de continuidad operativa |
| T-03 | Noche | 22:00 – 06:00 | Turno nocturno de vigilancia |
| T-04 | Personalizado | Libre | Definido por el administrador por evento o necesidad especial |

### 5.1 Reglas de Negocio para Turnos

1. Un guardia tiene asignado un turno por defecto (`assignedShift` en su ficha).
2. Al registrar entrada, el operador puede confirmar o cambiar el turno (útil para coberturas y horas extra).
3. El **Turno Personalizado** requiere ingresar hora de inicio y hora de fin manualmente.
4. El sistema alertará en el dashboard cuando un guardia lleve más de **9 horas activo** sin registrar salida.
5. Los reportes pueden filtrarse por turno para análisis de cobertura.

---

## 6. DISEÑO DE BASE DE DATOS (Firebase Firestore)

### 6.1 Colección: `security_personnel`

Catálogo de guardias — incluye `cargo` y `assignedShift` (mejoras v2.0).

| Campo | Tipo Firestore | Requerido | Descripción |
|---|---|:---:|---|
| `firstName` | string | ✅ | Nombre del guardia |
| `lastName` | string | ✅ | Apellido del guardia |
| `documentId` | string | ✅ | DNI / Identificación |
| `cargo` | string | ✅ | Cargo o puesto del guardia *(nuevo)* |
| `assignedShift` | string | ✅ | ID del turno asignado por defecto *(nuevo)* |
| `status` | string | ✅ | `active` \| `inactive` |
| `createdAt` | timestamp | ✅ | Fecha de creación |

```json
{
  "firstName": "Juan",
  "lastName": "Pérez",
  "documentId": "12345678",
  "cargo": "Guardia de Seguridad",
  "assignedShift": "T-01",
  "status": "active",
  "createdAt": "2026-05-07T06:00:00Z"
}
```

---

### 6.2 Colección: `security_shifts` *(nueva)*

| Campo | Tipo | Descripción |
|---|---|---|
| `name` | string | Ej: `'Mañana'`, `'Tarde'`, `'Noche'`, `'Personalizado'` |
| `startTime` | string | Hora de inicio (HH:MM) — `null` si es Personalizado |
| `endTime` | string | Hora de fin (HH:MM) — `null` si es Personalizado |
| `isActive` | boolean | Si el turno está disponible para asignación |

```json
{
  "name": "Mañana",
  "startTime": "06:00",
  "endTime": "14:00",
  "isActive": true
}
```

---

### 6.3 Colección: `security_logs` *(corazón del sistema)*

Ahora incluye `shiftId` para vincular cada evento a un turno.

| Campo | Tipo | Descripción |
|---|---|---|
| `personnelId` | string (ref) | ID del guardia |
| `shiftId` | string (ref) | ID del turno en que ocurre el evento *(nuevo)* |
| `entryTime` | timestamp | Marca de tiempo de entrada |
| `exitTime` | timestamp \| null | Marca de tiempo de salida |
| `exitReason` | string \| null | Motivo de salida (de catálogo fijo) |
| `exitReasonDetail` | string \| null | Texto libre si `exitReason = 'Otro'` |
| `destinationAreaId` | string \| null | ID del área de destino |
| `operatorId` | string | ID del operador que registró |
| `status` | string | `entered` \| `exited` |

```json
{
  "personnelId": "abc123",
  "shiftId": "T-01",
  "entryTime": "2026-05-07T06:05:00Z",
  "exitTime": null,
  "exitReason": null,
  "exitReasonDetail": null,
  "destinationAreaId": null,
  "operatorId": "op001",
  "status": "entered"
}
```

---

### 6.4 Colección: `security_areas`

Sin cambios. Campos: `name`, `description`, `isActive`.

```json
{
  "name": "Almacén Principal",
  "description": "Área de almacenamiento bloque A",
  "isActive": true
}
```

---

## 7. MÓDULO DE REPORTES *(Fase 4 mejorada)*

### 7.1 Exportación a Excel / CSV

- **Librería**: `openpyxl` (Excel `.xlsx`) y módulo `csv` nativo de Python.
- El Excel tendrá formato profesional: encabezados con color, columnas ajustadas, filtros automáticos.
- **Columnas exportadas**: Guardia, DNI, Cargo, Turno, Fecha/Hora Entrada, Fecha/Hora Salida, Duración, Motivo Salida, Área Destino, Operador.
- El CSV es útil para integrar con otros sistemas o importar a Power BI.

### 7.2 Exportación a PDF

- **Librería**: WeasyPrint (renderiza HTML a PDF) o ReportLab (PDF programático).
- El PDF incluirá:
  - Logo / encabezado institucional
  - Rango de fechas del reporte
  - Tabla de registros con totales y duración
  - Firma digital del supervisor (nombre + fecha de generación)
- Diseñado para **impresión en A4** y adjunto en correos de auditoría.

### 7.3 Filtros disponibles en reportes

| Filtro | Tipo de control | Ejemplo |
|---|---|---|
| Rango de fechas | DatePicker (desde/hasta) | 01/05/2026 – 07/05/2026 |
| Guardia | Buscador + Select | Juan Pérez |
| Turno | Select múltiple | Mañana, Noche |
| Área de destino | Select múltiple | Almacén Principal |
| Motivo de salida | Checkboxes | Ronda, Emergencia |
| Estado | Toggle | Solo activos / Todos |

---

## 8. RUTAS DEL SISTEMA (URLs de Django)

| URL | Rol requerido | Descripción |
|---|---|---|
| `/security/login/` | Público | Login con Firebase Auth |
| `/security/` | Todos | Dashboard con estadísticas en tiempo real |
| `/security/register/` | Operador, Admin | Registrar entrada y salida del día |
| `/security/logs/` | Todos | Historial filtrable de registros |
| `/security/reports/` | Supervisor, Admin | Generar y exportar reportes (Excel / PDF) |
| `/security/admin/personnel/` | Admin | CRUD guardias (incluye cargo y turno) |
| `/security/admin/areas/` | Admin | CRUD áreas de destino |
| `/security/admin/shifts/` | Admin | CRUD turnos *(nuevo)* |
| `/security/admin/users/` | Admin | Gestión de cuentas y roles del sistema |

---

## 9. REGLAS DE NEGOCIO COMPLETAS

### 9.1 Reglas de Registro

1. **Entrada única**: si el guardia tiene `status='entered'`, el sistema bloquea una nueva entrada y muestra alerta.
2. **Salida obligatoria previa**: no se puede registrar una nueva entrada sin haber registrado la salida anterior.
3. El **motivo de salida es obligatorio**. Si se selecciona `'Otro'`, el campo de texto se vuelve obligatorio.
4. El **área de destino** se selecciona exclusivamente del catálogo predefinido (sin texto libre).
5. Los registros con `status='exited'` son **inmutables**: no se modifican ni eliminan desde la interfaz.

### 9.2 Reglas de Turno *(nuevas)*

1. Al registrar entrada, se vincula el turno activo (por defecto el asignado al guardia, modificable por el operador).
2. Si el guardia permanece con `status='entered'` por más de 9 horas, el dashboard muestra **alerta visual**.
3. El turno `'Personalizado'` requiere ingresar `start_time` y `end_time` manualmente al momento del registro.
4. Los reportes por turno calculan automáticamente: duración promedio, horas totales trabajadas y cantidad de salidas por motivo.

### 9.3 Reglas de Seguridad

1. Todas las vistas de Django verifican el token de Firebase Auth mediante el decorador `@firebase_auth_required`.
2. Los permisos por rol se verifican con custom claims del token (`role: 'admin' | 'operator' | 'supervisor' | 'readonly'`).
3. Un operador **nunca** puede acceder a rutas `/admin/`.

### 9.4 Motivos de Salida disponibles

- Ronda de vigilancia
- Hora de almuerzo / refrigerio
- Fin de turno
- Emergencia
- Permiso especial
- **Otro** *(activa campo de texto obligatorio)*

---

## 10. FASES DE IMPLEMENTACIÓN

| Fase | Nombre | Tareas principales | Días estimados |
|---|---|---|:---:|
| **1** | Configuración Base | Entorno Django, firebase-admin SDK, Auth middleware, estructura de carpetas | 1–2 días |
| **2** | Catálogos (Admin) | CRUD Personal (con cargo + turno asignado), CRUD Áreas, CRUD Turnos, permisos por rol | 2–3 días |
| **3** | Motor de Registro | Pantalla `/register` con validación turno activo, lógica entrada única, modal salida con motivo + área | 3–4 días |
| **4** | Consultas y Reportes | Tabla histórica con filtros combinados, exportación Excel/CSV (openpyxl), exportación PDF (WeasyPrint) | 3–4 días |
| **5** | Dashboard | Contador en tiempo real (Firestore onSnapshot vía JS), estadísticas del día, alertas de turno vencido | 2 días |
| **6** | Estética y UX | Tailwind CSS, diseño responsive, animaciones, pruebas de carga y seguridad | 1–2 días |

> **Tiempo total estimado: 12 – 17 días de desarrollo activo.**

---

## 11. ESTRUCTURA DEL PROYECTO DJANGO

```
proyecto/
│
├── security_system/               # App principal del módulo
│   ├── views/
│   │   ├── dashboard.py           # Vista del dashboard en tiempo real
│   │   ├── register.py            # Registro de entrada y salida
│   │   ├── logs.py                # Historial con filtros
│   │   ├── reports.py             # Generación y exportación de reportes
│   │   └── admin/
│   │       ├── personnel.py       # CRUD guardias
│   │       ├── areas.py           # CRUD áreas
│   │       ├── shifts.py          # CRUD turnos
│   │       └── users.py           # CRUD usuarios del sistema
│   │
│   ├── firebase.py                # Inicialización firebase-admin + helpers Firestore
│   ├── auth.py                    # Decorador @firebase_auth_required + roles
│   │
│   ├── reports/
│   │   ├── excel_exporter.py      # Exportación a .xlsx y .csv con openpyxl
│   │   └── pdf_exporter.py        # Exportación a PDF con WeasyPrint
│   │
│   ├── templates/
│   │   └── security/              # Templates HTML con Tailwind CSS
│   │
│   └── urls.py                    # Todas las rutas del módulo /security/
│
├── static/
│   └── js/
│       └── realtime.js            # Firestore onSnapshot para el dashboard
│
├── .env                           # ⚠️ Variables de entorno — NUNCA en el código
├── requirements.txt
└── manage.py
```

> ⚠️ **SEGURIDAD CRÍTICA**: Las credenciales de Firebase (`private_key`, `api_key`) **JAMÁS** deben escribirse directamente en el código ni subirse a repositorios. Deben cargarse exclusivamente desde variables de entorno usando `python-decouple` o `django-environ`.

---

## 12. DEPENDENCIAS PYTHON (`requirements.txt`)

```txt
django>=4.2
firebase-admin>=6.0
openpyxl>=3.1
weasyprint>=60.0
python-decouple>=3.8
whitenoise>=6.0
gunicorn>=21.0
```

| Paquete | Versión | Uso en el proyecto |
|---|---|---|
| `django` | >=4.2 | Framework principal |
| `firebase-admin` | >=6.0 | Conexión a Firestore y Firebase Auth |
| `openpyxl` | >=3.1 | Exportación Excel (.xlsx) y CSV |
| `weasyprint` | >=60.0 | Exportación PDF |
| `python-decouple` | >=3.8 | Manejo seguro de variables de entorno |
| `whitenoise` | >=6.0 | Servir archivos estáticos en producción |
| `gunicorn` | >=21.0 | Servidor WSGI para producción |

---

## 13. VARIABLES DE ENTORNO (`.env`)

```env
# Django
SECRET_KEY=tu_secret_key_aqui
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Firebase
FIREBASE_PROJECT_ID=tu_project_id
FIREBASE_PRIVATE_KEY_ID=tu_private_key_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk@tu_proyecto.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=tu_client_id

# Firebase Web (para el frontend JS)
VITE_FIREBASE_API_KEY=tu_api_key
VITE_FIREBASE_AUTH_DOMAIN=tu_proyecto.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=tu_project_id
```

---

*Plan v2.0 — Sistema de Control de Entrada y Salida — SENATI — Mayo 2026*
