# Godot MCP Bridge

Bridge que permite a **IAs con soporte MCP** (Cursor, Claude Desktop, Windsurf, etc.) interactuar directamente con el **Editor de Godot 4.x** mediante el protocolo MCP (Model Context Protocol).

Con este bridge, puedes pedirle a la IA que cree escenas, agregue nodos, configure materiales, escriba scripts y mucho más, todo desde tu editor favorito.

---

## ✨ Características

- 🎮 **Control total del editor**: Crear/abrir/guardar escenas, ejecutar el juego
- 🌳 **Manipulación de nodos**: Agregar, eliminar, duplicar, renombrar nodos
- 🎨 **Recursos visuales**: Materiales, texturas, sprites, luces, cámaras
- 📜 **Scripts**: Leer, escribir y asignar scripts GDScript
- ⌨️ **Input Map**: Configurar acciones de entrada y teclas
- 💥 **Física**: Crear formas de colisión 2D/3D
- 🔊 **Audio**: Crear reproductores de audio
- 🌍 **Entorno**: Configurar WorldEnvironment

---

## 🔌 Compatibilidad

Este proyecto tiene **dos niveles de compatibilidad**:

### Clientes MCP (Listos para usar)

El servidor MCP usa el **Model Context Protocol** de Anthropic:

| Cliente | Soporte |
|---------|---------|
| **Cursor** | ✅ Listo |
| **Claude Desktop** | ✅ Listo |
| **Windsurf** | ✅ Listo |
| **Zed** | ✅ Con plugin |
| **VS Code** | ⚠️ Requiere extensión MCP |
| **Otros IDEs** | ❌ Solo si implementan MCP |

### Conexión Directa WebSocket (Para desarrolladores)

El addon de Godot expone un **servidor WebSocket JSON-RPC** independiente de MCP:

```
ws://127.0.0.1:49631
```

Esto permite crear clientes personalizados en cualquier lenguaje (Python, Node.js, C#, etc.) sin necesidad del protocolo MCP.

---

## 📋 Requisitos

- **Godot 4.x** (probado con 4.4.1)
- **Python 3.9+**
- **Cliente MCP**: Cursor, Claude Desktop, Windsurf, u otro compatible

---

## 🚀 Instalación

### Paso 1: Instalar el Addon en Godot

1. Copia la carpeta `godot-addon/addons/godotbridge` a tu proyecto de Godot:

```
tu-proyecto/
├── addons/
│   └── godotbridge/
│       ├── plugin.cfg
│       ├── godotbridge_plugin.gd
│       ├── rpc_server.gd
│       ├── rpc_handlers.gd
│       ├── serializers.gd
│       └── validators.gd
```

2. En Godot, ve a **Project → Project Settings → Plugins**

3. Activa el plugin **"GodotBridge"**

4. Verifica en la consola que aparezca:
```
[GodotBridge] Plugin initialized on port 49631
```

5. El plugin genera un archivo de token en:
   - Windows: `%APPDATA%/Godot/app_userdata/TU_PROYECTO/godotbridge_token.txt`
   - Linux: `~/.local/share/godot/app_userdata/TU_PROYECTO/godotbridge_token.txt`
   - macOS: `~/Library/Application Support/Godot/app_userdata/TU_PROYECTO/godotbridge_token.txt`

### Paso 2: Instalar el Servidor MCP

1. Navega a la carpeta del servidor:

```bash
cd mcp-server
```

2. Instala las dependencias:

```bash
pip install websockets>=10.0
```

### Paso 3: Configurar Cursor

1. Abre la configuración de MCP en Cursor:
   - **Windows/Linux**: `%USERPROFILE%/.cursor/mcp.json` o `~/.cursor/mcp.json`
   - **macOS**: `~/.cursor/mcp.json`

2. Agrega la configuración del servidor. Hay **dos opciones**:

#### Opción A: Token por Archivo (Recomendado)

Esta opción usa `GODOT_TOKEN_FILE` para leer el token desde el archivo generado por el plugin. Es más seguro y el token se actualiza automáticamente:

```json
{
  "mcpServers": {
    "godot": {
      "command": "python",
      "args": ["C:/RUTA/COMPLETA/mcp-server/src/main.py"],
      "env": {
        "GODOT_WS_URL": "ws://127.0.0.1:49631",
        "GODOT_TOKEN_FILE": "C:/Users/TU_USUARIO/AppData/Roaming/Godot/app_userdata/TU_PROYECTO/godotbridge_token.txt",
        "GODOT_MCP_VERBOSE": "1"
      }
    }
  }
}
```

#### Opción B: Token Directo

Esta opción usa `GODOT_TOKEN` con el valor del token directamente. Útil para configuraciones rápidas o cuando no quieres depender de la ruta del archivo:

```json
{
  "mcpServers": {
    "godot": {
      "command": "python",
      "args": ["C:/RUTA/COMPLETA/mcp-server/src/main.py"],
      "env": {
        "GODOT_WS_URL": "ws://127.0.0.1:49631",
        "GODOT_TOKEN": "tu_token_aqui_desde_godotbridge_token.txt",
        "GODOT_MCP_VERBOSE": "1"
      }
    }
  }
}
```

> ⚠️ **Importante**: 
> - Reemplaza las rutas con las correctas de tu sistema.
> - El token se encuentra en el archivo `godotbridge_token.txt` generado por el plugin.
> - Si usas la Opción B, deberás actualizar el token manualmente si cambia.
> - `GODOT_MCP_VERBOSE` es opcional, actívalo con `"1"` para ver logs detallados.

3. Reinicia Cursor para cargar la configuración.

---

## 🎯 Uso

Una vez configurado, puedes hablar con Cursor AI y pedirle que interactúe con Godot:

### Ejemplos de comandos:

```
"Crea una nueva escena 3D llamada Level1"

"Agrega un MeshInstance3D con un cubo al nodo raíz"

"Configura las teclas WASD para movimiento"

"Escribe un script de movimiento para el jugador"

"Ejecuta el juego"
```

---

## 🛠️ Herramientas Disponibles

### Proyecto
| Herramienta | Descripción |
|-------------|-------------|
| `godot_get_project_info` | Obtener información del proyecto |
| `godot_add_input_action` | Agregar acción de input con tecla |
| `godot_remove_input_action` | Eliminar acción de input |

### Editor
| Herramienta | Descripción |
|-------------|-------------|
| `godot_get_editor_state` | Estado actual del editor |
| `godot_open_scene` | Abrir una escena |
| `godot_save_scene` | Guardar la escena actual |

### Escenas
| Herramienta | Descripción |
|-------------|-------------|
| `godot_create_scene` | Crear nueva escena |
| `godot_instance_scene` | Instanciar una escena |
| `godot_get_scene_tree` | Obtener árbol de escena |

### Nodos
| Herramienta | Descripción |
|-------------|-------------|
| `godot_list_nodes` | Listar nodos hijos |
| `godot_get_node_properties` | Obtener propiedades de un nodo |
| `godot_set_node_properties` | Establecer propiedades |
| `godot_add_node` | Agregar un nodo |
| `godot_remove_node` | Eliminar un nodo |

### Mallas y Materiales
| Herramienta | Descripción |
|-------------|-------------|
| `godot_create_mesh` | Crear malla (Box, Sphere, etc.) |
| `godot_create_material` | Crear y aplicar material |
| `godot_set_material` | Asignar material existente |

### Sprites y Texturas
| Herramienta | Descripción |
|-------------|-------------|
| `godot_set_sprite_texture` | Asignar textura a sprite |
| `godot_set_modulate` | Cambiar color/modulación |

### Física
| Herramienta | Descripción |
|-------------|-------------|
| `godot_create_collision_shape` | Crear forma de colisión |

### Iluminación y Cámara
| Herramienta | Descripción |
|-------------|-------------|
| `godot_create_light` | Crear luz (Directional, Omni, Spot, Point2D) |
| `godot_configure_camera` | Configurar cámara |
| `godot_create_environment` | Crear WorldEnvironment |

### Audio
| Herramienta | Descripción |
|-------------|-------------|
| `godot_create_audio_player` | Crear reproductor de audio |

### Scripts
| Herramienta | Descripción |
|-------------|-------------|
| `godot_read_script` | Leer contenido de script |
| `godot_write_script` | Escribir script |
| `godot_assign_script` | Asignar script a nodo |

### Ejecución
| Herramienta | Descripción |
|-------------|-------------|
| `godot_run_main` | Ejecutar escena principal |
| `godot_run_current` | Ejecutar escena actual |
| `godot_stop` | Detener ejecución |

### Archivos
| Herramienta | Descripción |
|-------------|-------------|
| `godot_search_files` | Buscar archivos en el proyecto |

---

## 🖼️ Sprite Sheet MCP (Nuevo)

Este proyecto incluye un **segundo MCP independiente** para análisis inteligente de spritesheets usando OpenCV.

### Características
- 🔍 **Detección automática de frames** por canal alpha o color de fondo
- 🎬 **Agrupación de animaciones** por filas, columnas o clustering espacial
- 📐 **Normalización** de tamaños y pivots
- 📤 **Exportación Godot-friendly** con comandos pre-armados

### Instalación Adicional

```bash
cd sprite-sheet-mcp
pip install -r requirements.txt
```

### Configuración en mcp.json

```json
{
  "mcpServers": {
    "godot": { ... },
    "sprite-sheet-tools": {
      "command": "python",
      "args": ["C:/RUTA/sprite-sheet-mcp/src/main.py"]
    }
  }
}
```

### Flujo de Trabajo

1. `sprite_analyze_sheet` → Detecta frames automáticamente
2. `sprite_group_animations` → Agrupa en animaciones
3. `sprite_export_godot_json` → Genera JSON con comandos de Godot
4. Usa el JSON con `godot_atlas_batch_create` y `godot_spriteframes_*`

Ver [sprite-sheet-mcp/TOOLS.md](sprite-sheet-mcp/TOOLS.md) para documentación completa.

---

## 📁 Estructura del Proyecto

```
godot-mcp-bridge/
├── godot-addon/
│   └── addons/
│       └── godotbridge/
│           ├── plugin.cfg           # Metadata del plugin
│           ├── godotbridge_plugin.gd # Plugin principal
│           ├── rpc_server.gd        # Servidor WebSocket
│           ├── rpc_handlers.gd      # Handlers RPC
│           ├── serializers.gd       # Serialización de datos
│           └── validators.gd        # Validación de inputs
├── mcp-server/
│   ├── src/
│   │   └── main.py                  # Servidor MCP Godot
│   ├── requirements.txt             # Dependencias Python
│   ├── TOOLS.md                     # Documentación de herramientas
│   └── INFORME_ERRORES.md          # Historial de debugging
├── sprite-sheet-mcp/                # MCP de análisis de spritesheets
│   ├── src/
│   │   ├── main.py                  # Servidor MCP
│   │   ├── detector.py              # Detección de frames (OpenCV)
│   │   ├── grouper.py               # Agrupación de animaciones
│   │   ├── normalizer.py            # Normalización
│   │   └── exporter.py              # Exportación Godot
│   ├── requirements.txt             # opencv-python, numpy, etc.
│   └── TOOLS.md                     # Documentación
└── README.md
```

---

## 🔧 Configuración Avanzada

### Cambiar Puerto

El puerto por defecto es `49631`. Para cambiarlo:

1. En Godot: **Project Settings → General → GodotBridge → Network → Port**
2. En el servidor MCP, agrega la variable de entorno:
```json
"env": {
  "GODOT_WS_URL": "ws://127.0.0.1:NUEVO_PUERTO"
}
```

### Modo Debug

Para ver logs detallados del servidor MCP:
```json
"env": {
  "GODOT_MCP_VERBOSE": "1"
}
```

---

## 🔒 Seguridad

- El servidor solo acepta conexiones desde `localhost` (127.0.0.1)
- Se utiliza autenticación por token de sesión
- Los métodos RPC están en una allowlist

---

## ❓ Solución de Problemas

### El servidor MCP no conecta

1. Verifica que Godot esté abierto con el plugin activo
2. Verifica que la ruta al token sea correcta en `mcp.json`
3. Revisa la consola de Godot por errores

### Las herramientas no aparecen en Cursor

1. Reinicia Cursor después de modificar `mcp.json`
2. Verifica que Python esté en el PATH
3. Revisa los logs de Cursor (Help → Toggle Developer Tools)

### Error "Node not found"

- Usa nombres de nodos relativos a la raíz de la escena (ej: `Player`, `Player/Sprite2D`)
- No incluyas el nombre de la raíz si es el mismo que el nodo (ej: usa `Player`, no `Game/Player`)

---

## 📄 Licencia

MIT License

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor abre un issue o pull request.
