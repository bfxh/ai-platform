# Godot MCP Bridge - Herramientas Disponibles

Este documento describe todas las herramientas MCP disponibles para interactuar con Godot Editor desde Cursor AI.

---

## Índice

1. [Herramientas de Proyecto](#herramientas-de-proyecto)
2. [Herramientas de Editor](#herramientas-de-editor)
3. [Herramientas de Escena](#herramientas-de-escena)
4. [Herramientas de Nodos](#herramientas-de-nodos)
5. [Herramientas de Mallas (Mesh)](#herramientas-de-mallas-mesh)
6. [Herramientas de Materiales](#herramientas-de-materiales)
7. [Herramientas de Sprites y Texturas](#herramientas-de-sprites-y-texturas)
8. [Herramientas de Colisión](#herramientas-de-colisión)
9. [Herramientas de Iluminación](#herramientas-de-iluminación)
10. [Herramientas de Cámara](#herramientas-de-cámara)
11. [Herramientas de Entorno](#herramientas-de-entorno)
12. [Herramientas de Audio](#herramientas-de-audio)
13. [Herramientas de Scripts](#herramientas-de-scripts)
14. [Herramientas de Ejecución](#herramientas-de-ejecución)
15. [Herramientas de Archivos](#herramientas-de-archivos)
16. [Herramientas de Sprite2D Avanzadas](#herramientas-de-sprite2d-avanzadas)
17. [Herramientas de AtlasTexture](#herramientas-de-atlastexture)
18. [Herramientas de SpriteFrames](#herramientas-de-spriteframes)
19. [Herramientas de AnimatedSprite2D](#herramientas-de-animatedsprite2d)
20. [Herramientas de Animation](#herramientas-de-animation)
21. [Herramientas de AnimationPlayer](#herramientas-de-animationplayer)
22. [Herramientas de TileSet](#herramientas-de-tileset)
23. [Herramientas de Introspección](#herramientas-de-introspección)

---

## Herramientas de Proyecto

### `godot_get_project_info`
Obtiene información general del proyecto Godot.

**Parámetros:** Ninguno

**Retorna:**
- Nombre del proyecto
- Versión del engine
- Escena principal configurada
- Ruta del proyecto

**Ejemplo de uso:**
```
"Obtén la información del proyecto actual"
```

---

### `godot_add_input_action`
Agrega una acción de entrada (input action) con una tecla asociada al mapa de controles.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `action_name` | string | ✅ | Nombre de la acción (ej: `move_up`, `jump`) |
| `key` | string | ✅ | Código de tecla (ej: `KEY_UP`, `KEY_W`, `KEY_SPACE`) |

**Teclas comunes:**
- Flechas: `KEY_UP`, `KEY_DOWN`, `KEY_LEFT`, `KEY_RIGHT`
- Letras: `KEY_A`, `KEY_B`, ... `KEY_Z`
- Números: `KEY_0`, `KEY_1`, ... `KEY_9`
- Especiales: `KEY_SPACE`, `KEY_ENTER`, `KEY_ESCAPE`, `KEY_TAB`, `KEY_SHIFT`

**Ejemplo de uso:**
```
"Agrega una acción llamada 'move_forward' con la tecla W"
```

---

### `godot_remove_input_action`
Elimina una acción de entrada del mapa de controles.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `action_name` | string | ✅ | Nombre de la acción a eliminar |

**Ejemplo de uso:**
```
"Elimina la acción de entrada 'jump'"
```

---

## Herramientas de Editor

### `godot_get_editor_state`
Obtiene el estado actual del editor de Godot.

**Parámetros:** Ninguno

**Retorna:**
- Escenas abiertas
- Escena activa
- Nodos seleccionados
- Estado de reproducción

**Ejemplo de uso:**
```
"Muéstrame el estado actual del editor"
```

---

### `godot_open_scene`
Abre una escena en el editor de Godot.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `scene_path` | string | ✅ | Ruta de la escena (ej: `res://scenes/Main.tscn`) |

**Ejemplo de uso:**
```
"Abre la escena res://levels/Level1.tscn"
```

---

### `godot_save_scene`
Guarda la escena actual o en una ruta específica.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `scene_path` | string | ❌ | Ruta donde guardar (opcional, usa la ruta actual si no se especifica) |

**Ejemplo de uso:**
```
"Guarda la escena actual"
"Guarda la escena como res://scenes/NewScene.tscn"
```

---

## Herramientas de Escena

### `godot_create_scene`
Crea una nueva escena con un nodo raíz especificado.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `root_type` | string | ✅ | Tipo de nodo raíz: `Node3D`, `Node2D`, `Control`, `Node` |
| `root_name` | string | ❌ | Nombre del nodo raíz (default: "Root") |
| `scene_path` | string | ✅ | Ruta donde guardar la escena |

**Ejemplo de uso:**
```
"Crea una nueva escena 3D en res://scenes/Game.tscn"
"Crea una escena 2D con raíz llamada 'World' en res://levels/Level1.tscn"
```

---

### `godot_instance_scene`
Instancia una escena existente como hijo de un nodo.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `parent_path` | string | ✅ | Ruta del nodo padre |
| `scene_path` | string | ✅ | Ruta de la escena a instanciar |
| `name` | string | ❌ | Nombre para la instancia |

**Ejemplo de uso:**
```
"Instancia la escena res://enemies/Enemy.tscn como hijo del nodo raíz"
```

---

### `godot_get_scene_tree`
Obtiene la jerarquía completa del árbol de la escena actual.

**Parámetros:** Ninguno

**Retorna:** Estructura jerárquica de todos los nodos de la escena.

**Ejemplo de uso:**
```
"Muéstrame el árbol de la escena actual"
```

---

## Herramientas de Nodos

### `godot_list_nodes`
Lista los nodos hijos de un nodo padre específico.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `parent_path` | string | ❌ | Ruta del nodo padre (default: raíz de la escena) |

**Ejemplo de uso:**
```
"Lista los hijos del nodo Player"
```

---

### `godot_get_node_properties`
Obtiene las propiedades de un nodo específico.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo |

**Ejemplo de uso:**
```
"Dame las propiedades del nodo Camera3D"
```

---

### `godot_set_node_properties`
Establece propiedades en un nodo.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo |
| `properties` | object | ✅ | Diccionario de propiedades a establecer |

**Propiedades comunes:**
- `position`: Vector2/Vector3 - Posición del nodo
- `rotation`: float/Vector3 - Rotación en radianes
- `scale`: Vector2/Vector3 - Escala del nodo
- `visible`: bool - Visibilidad
- `modulate`: Color - Modulación de color (2D)

**Ejemplo de uso:**
```
"Mueve el nodo Player a la posición (100, 200)"
"Cambia la escala del Sprite a 2x"
```

---

### `godot_add_node`
Agrega un nuevo nodo a la escena.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `parent_path` | string | ✅ | Ruta del nodo padre |
| `type` | string | ✅ | Tipo de nodo a crear |
| `name` | string | ✅ | Nombre del nuevo nodo |
| `properties` | object | ❌ | Propiedades iniciales |

**Tipos de nodos comunes:**

| Categoría | Tipos |
|-----------|-------|
| **2D** | `Node2D`, `Sprite2D`, `AnimatedSprite2D`, `CharacterBody2D`, `RigidBody2D`, `Area2D`, `CollisionShape2D`, `Camera2D` |
| **3D** | `Node3D`, `MeshInstance3D`, `CharacterBody3D`, `RigidBody3D`, `Area3D`, `CollisionShape3D`, `Camera3D` |
| **UI** | `Control`, `Button`, `Label`, `TextEdit`, `Panel`, `VBoxContainer`, `HBoxContainer` |
| **Audio** | `AudioStreamPlayer`, `AudioStreamPlayer2D`, `AudioStreamPlayer3D` |

**Ejemplo de uso:**
```
"Agrega un MeshInstance3D llamado 'Cube' como hijo del nodo raíz"
"Crea un nodo Sprite2D llamado 'Player' con posición (100, 100)"
```

---

### `godot_remove_node`
Elimina un nodo de la escena.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo a eliminar |

**Ejemplo de uso:**
```
"Elimina el nodo Enemy"
```

---

## Herramientas de Mallas (Mesh)

### `godot_create_mesh`
Crea y asigna una malla a un nodo MeshInstance3D.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta al nodo MeshInstance3D |
| `mesh_type` | string | ✅ | Tipo de malla |
| `mesh_params` | object | ❌ | Parámetros de la malla |

**Tipos de malla disponibles:**

| Tipo | Parámetros |
|------|------------|
| `BoxMesh` | `size`: Vector3 (default: 1,1,1) |
| `SphereMesh` | `radius`: float, `height`: float |
| `CylinderMesh` | `radius`: float, `height`: float |
| `CapsuleMesh` | `radius`: float, `height`: float |
| `PlaneMesh` | `size`: Vector2 |

**Ejemplo de uso:**
```
"Crea un BoxMesh en el nodo Cube con tamaño (2, 2, 2)"
"Agrega una esfera al MeshInstance3D con radio 0.5"
```

---

## Herramientas de Materiales

### `godot_create_material`
Crea y aplica un material a un nodo.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo |
| `material_type` | string | ❌ | `StandardMaterial3D` o `CanvasItemMaterial` |
| `properties` | object | ❌ | Propiedades del material |

**Propiedades de StandardMaterial3D:**
- `albedo_color`: Color (ej: `{r: 1, g: 0, b: 0, a: 1}` para rojo)
- `metallic`: float (0-1)
- `roughness`: float (0-1)
- `emission`: Color
- `emission_energy`: float

**Ejemplo de uso:**
```
"Aplica un material rojo metálico al nodo Cube"
"Crea un material con emisión azul para el nodo Light"
```

---

### `godot_set_material`
Asigna un material existente (recurso .tres/.res) a un nodo.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo |
| `material_path` | string | ✅ | Ruta del recurso material |
| `surface_index` | int | ❌ | Índice de superficie (default: 0) |

**Ejemplo de uso:**
```
"Asigna el material res://materials/metal.tres al nodo Cube"
```

---

## Herramientas de Sprites y Texturas

### `godot_set_sprite_texture`
Establece una textura en un Sprite2D o Sprite3D.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo Sprite |
| `texture_path` | string | ✅ | Ruta de la textura |
| `hframes` | int | ❌ | Frames horizontales (para spritesheets) |
| `vframes` | int | ❌ | Frames verticales (para spritesheets) |
| `frame` | int | ❌ | Frame actual |

**Ejemplo de uso:**
```
"Asigna la textura res://sprites/player.png al Sprite2D"
"Configura el sprite con 4 frames horizontales"
```

---

### `godot_set_modulate`
Establece la modulación de color en un CanvasItem (nodos 2D y UI).

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo |
| `color` | object | ✅ | Color `{r, g, b, a}` (valores 0-1) |
| `self_modulate` | bool | ❌ | Si usar self_modulate en lugar de modulate |

**Ejemplo de uso:**
```
"Cambia el color del sprite a rojo semi-transparente"
"Aplica un tinte verde al nodo Player"
```

---

## Herramientas de Colisión

### `godot_create_collision_shape`
Crea una forma de colisión en un CollisionShape2D/3D.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo CollisionShape |
| `shape_type` | string | ✅ | Tipo de forma |
| `shape_params` | object | ❌ | Parámetros de la forma |

**Formas 3D:**
| Tipo | Parámetros |
|------|------------|
| `BoxShape3D` | `size`: Vector3 |
| `SphereShape3D` | `radius`: float |
| `CapsuleShape3D` | `radius`: float, `height`: float |
| `CylinderShape3D` | `radius`: float, `height`: float |

**Formas 2D:**
| Tipo | Parámetros |
|------|------------|
| `RectangleShape2D` | `size`: Vector2 |
| `CircleShape2D` | `radius`: float |
| `CapsuleShape2D` | `radius`: float, `height`: float |

**Ejemplo de uso:**
```
"Crea un BoxShape3D de tamaño (1, 2, 1) en el CollisionShape3D"
"Agrega un círculo de colisión con radio 32 pixeles"
```

---

## Herramientas de Iluminación

### `godot_create_light`
Crea un nodo de luz.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `parent_path` | string | ✅ | Ruta del nodo padre |
| `light_type` | string | ✅ | Tipo de luz |
| `name` | string | ❌ | Nombre del nodo |
| `properties` | object | ❌ | Propiedades de la luz |

**Tipos de luz:**
- **3D:** `DirectionalLight3D`, `OmniLight3D`, `SpotLight3D`
- **2D:** `PointLight2D`, `DirectionalLight2D`

**Propiedades comunes:**
- `light_color`: Color
- `light_energy`: float
- `shadow_enabled`: bool
- `position`: Vector3
- `rotation`: Vector3

**Ejemplo de uso:**
```
"Crea una luz direccional con sombras habilitadas"
"Agrega una luz puntual naranja con energía 2.0"
```

---

## Herramientas de Cámara

### `godot_configure_camera`
Configura las propiedades de una cámara.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta de la cámara |
| `properties` | object | ✅ | Propiedades a configurar |

**Propiedades Camera3D:**
- `fov`: float - Campo de visión en grados
- `near`: float - Plano cercano
- `far`: float - Plano lejano
- `projection`: int - 0=Perspectiva, 1=Ortogonal
- `current`: bool - Si es la cámara activa

**Propiedades Camera2D:**
- `zoom`: Vector2
- `offset`: Vector2
- `current`: bool

**Ejemplo de uso:**
```
"Configura la cámara con FOV de 90 grados"
"Activa la Camera2D y establece zoom a 2x"
```

---

## Herramientas de Entorno

### `godot_create_environment`
Crea o configura un WorldEnvironment.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ❌ | Ruta del nodo (crea uno nuevo si no se especifica) |
| `properties` | object | ❌ | Propiedades del entorno |

**Propiedades disponibles:**
- `background_mode`: int - Modo de fondo (0=Clear, 1=Custom Color, 2=Sky, etc.)
- `background_color`: Color
- `ambient_light_color`: Color
- `ambient_light_energy`: float
- `fog_enabled`: bool
- `glow_enabled`: bool

**Ejemplo de uso:**
```
"Crea un entorno con fondo azul oscuro y niebla habilitada"
"Configura la luz ambiental con color cálido"
```

---

## Herramientas de Audio

### `godot_create_audio_player`
Crea un nodo reproductor de audio.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `parent_path` | string | ✅ | Ruta del nodo padre |
| `audio_type` | string | ❌ | Tipo de reproductor |
| `name` | string | ❌ | Nombre del nodo |
| `stream_path` | string | ❌ | Ruta del archivo de audio |
| `properties` | object | ❌ | Propiedades del reproductor |

**Tipos de reproductor:**
- `AudioStreamPlayer` - Audio global/UI
- `AudioStreamPlayer2D` - Audio espacial 2D
- `AudioStreamPlayer3D` - Audio espacial 3D

**Propiedades:**
- `volume_db`: float
- `autoplay`: bool
- `max_distance`: float (para 2D/3D)
- `bus`: string

**Ejemplo de uso:**
```
"Crea un reproductor de audio 2D con el sonido res://audio/jump.wav"
"Agrega música de fondo con autoplay activado"
```

---

## Herramientas de Scripts

### `godot_read_script`
Lee el contenido de un archivo de script.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `path` | string | ✅ | Ruta del script (ej: `res://scripts/player.gd`) |

**Ejemplo de uso:**
```
"Lee el contenido del script player.gd"
```

---

### `godot_write_script`
Escribe contenido a un archivo de script.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `path` | string | ✅ | Ruta del script |
| `content` | string | ✅ | Contenido del script |

**Ejemplo de uso:**
```
"Crea un script de movimiento para el jugador en res://scripts/player_movement.gd"
```

---

### `godot_assign_script`
Asigna un script a un nodo.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo |
| `script_path` | string | ✅ | Ruta del script |

**Ejemplo de uso:**
```
"Asigna el script player.gd al nodo Player"
```

---

## Herramientas de Ejecución

### `godot_run_main`
Ejecuta la escena principal del proyecto.

**Parámetros:** Ninguno

**Ejemplo de uso:**
```
"Ejecuta el juego"
```

---

### `godot_run_current`
Ejecuta la escena actualmente abierta en el editor.

**Parámetros:** Ninguno

**Ejemplo de uso:**
```
"Ejecuta la escena actual"
```

---

### `godot_stop`
Detiene la ejecución del juego.

**Parámetros:** Ninguno

**Ejemplo de uso:**
```
"Detén el juego"
```

---

## Herramientas de Archivos

### `godot_search_files`
Busca archivos en el proyecto.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `query` | string | ❌ | Texto a buscar en nombres de archivo |
| `type` | string | ❌ | Extensión de archivo (ej: `gd`, `tscn`, `png`) |
| `folder` | string | ❌ | Carpeta donde buscar (default: `res://`) |

**Ejemplo de uso:**
```
"Busca todos los archivos .gd en el proyecto"
"Encuentra escenas que contengan 'level' en el nombre"
```

---

## Herramientas de Sprite2D Avanzadas

Herramientas para control fino de Sprite2D con spritesheets y regiones.

### `godot_sprite2d_set_texture`
Asigna una textura a un nodo Sprite2D.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo Sprite2D |
| `texture_path` | string | ✅ | Ruta de la textura (res://...) |

**Ejemplo de uso:**
```
"Asigna la textura res://sprites/character.png al Sprite2D del jugador"
```

---

### `godot_sprite2d_set_grid`
Configura la grilla de un Sprite2D para spritesheets (hframes/vframes).

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo Sprite2D |
| `hframes` | int | ✅ | Número de frames horizontales |
| `vframes` | int | ✅ | Número de frames verticales |

**Ejemplo de uso:**
```
"Configura el sprite con 8 frames horizontales y 4 verticales"
```

---

### `godot_sprite2d_set_frame`
Establece el frame actual por índice (0 a hframes*vframes-1).

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo Sprite2D |
| `frame` | int | ✅ | Índice del frame |

**Ejemplo de uso:**
```
"Cambia al frame 5 del sprite"
```

---

### `godot_sprite2d_set_frame_coords`
Establece el frame actual por coordenadas de grilla (x, y).

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo Sprite2D |
| `x` | int | ✅ | Columna del frame (0-based) |
| `y` | int | ✅ | Fila del frame (0-based) |

**Ejemplo de uso:**
```
"Selecciona el frame en columna 2, fila 1"
```

---

### `godot_sprite2d_get_grid`
Obtiene la configuración actual de la grilla y frame del Sprite2D.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo Sprite2D |

**Retorna:**
- `hframes`, `vframes`: Configuración de grilla
- `frame`: Frame actual (índice)
- `frame_coords`: Frame actual (coordenadas)
- `total_frames`: Total de frames disponibles
- `region_enabled`: Estado de región
- `region_rect`: Rectángulo de región actual

---

### `godot_sprite2d_enable_region`
Activa o desactiva el modo de región en un Sprite2D.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo Sprite2D |
| `enabled` | bool | ✅ | true para activar, false para desactivar |

**Ejemplo de uso:**
```
"Activa el modo región en el sprite del personaje"
```

---

### `godot_sprite2d_set_region_rect`
Define el rectángulo de región para recortar la textura.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo Sprite2D |
| `x` | number | ✅ | Posición X del rectángulo |
| `y` | number | ✅ | Posición Y del rectángulo |
| `w` | number | ✅ | Ancho del rectángulo |
| `h` | number | ✅ | Alto del rectángulo |

**Ejemplo de uso:**
```
"Recorta la región del sprite desde (0, 0) con tamaño 64x64"
```

---

### `godot_sprite2d_set_region_clip`
Activa o desactiva el filtro de clip de región (evita sangrado de pixels).

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo Sprite2D |
| `enabled` | bool | ✅ | true para activar el clip |

---

## Herramientas de AtlasTexture

Herramientas para crear y manejar AtlasTexture (sub-texturas desde una textura grande).

### `godot_atlas_create`
Crea un AtlasTexture recortando una región de una textura base.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `texture_path` | string | ✅ | Ruta de la textura base |
| `rect` | object | ✅ | Región a recortar: `{x, y, w, h}` |
| `margin` | object | ❌ | Márgenes opcionales: `{x, y, w, h}` |
| `save_path` | string | ❌ | Ruta para guardar el recurso .tres |

**Ejemplo de uso:**
```
"Crea un AtlasTexture del sprite principal recortando la región (0, 0, 64, 64)"
```

---

### `godot_atlas_batch_create`
Crea múltiples AtlasTextures a partir de una lista de rectángulos.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `texture_path` | string | ✅ | Ruta de la textura base |
| `rects` | array | ✅ | Lista de rectángulos: `[{x, y, w, h}, ...]` |
| `margin` | object | ❌ | Márgenes aplicados a todos |
| `save_folder` | string | ❌ | Carpeta para guardar los recursos |

**Ejemplo de uso:**
```
"Crea atlas para cada frame del spritesheet, guardando en res://atlas/"
```

---

### `godot_node_set_texture`
Asigna cualquier Texture2D (incluido AtlasTexture) a un nodo compatible.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo (Sprite2D, TextureRect, etc.) |
| `texture_path` | string | ✅ | Ruta de la textura o AtlasTexture |

**Nodos compatibles:** Sprite2D, Sprite3D, TextureRect, TextureButton

---

## Herramientas de SpriteFrames

Herramientas para crear y gestionar recursos SpriteFrames (animaciones 2D).

### `godot_spriteframes_create`
Crea un nuevo recurso SpriteFrames vacío.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `save_path` | string | ❌ | Ruta para guardar el recurso .tres |

**Retorna:**
- `spriteframes_path`: Ruta del recurso creado
- `animations`: Lista de animaciones (incluye "default")

---

### `godot_spriteframes_add_animation`
Agrega una nueva animación al SpriteFrames.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `spriteframes_path` | string | ✅ | Ruta del recurso SpriteFrames |
| `animation_name` | string | ✅ | Nombre de la nueva animación |

**Ejemplo de uso:**
```
"Agrega una animación 'walk' al SpriteFrames del personaje"
```

---

### `godot_spriteframes_set_fps`
Establece la velocidad (FPS) de una animación.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `spriteframes_path` | string | ✅ | Ruta del recurso SpriteFrames |
| `animation_name` | string | ✅ | Nombre de la animación |
| `fps` | number | ✅ | Frames por segundo |

---

### `godot_spriteframes_set_loop`
Activa o desactiva el loop de una animación.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `spriteframes_path` | string | ✅ | Ruta del recurso SpriteFrames |
| `animation_name` | string | ✅ | Nombre de la animación |
| `loop` | bool | ✅ | true para activar loop |

---

### `godot_spriteframes_add_frame`
Agrega un frame (textura) a una animación.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `spriteframes_path` | string | ✅ | Ruta del recurso SpriteFrames |
| `animation_name` | string | ✅ | Nombre de la animación |
| `texture_path` | string | ✅ | Ruta de la textura/AtlasTexture |
| `duration` | number | ❌ | Multiplicador de duración (default: 1.0) |
| `at_position` | int | ❌ | Posición de inserción (-1 = final) |

**Ejemplo de uso:**
```
"Agrega el frame res://sprites/walk_01.png a la animación 'walk'"
```

---

### `godot_spriteframes_remove_frame`
Elimina un frame de una animación.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `spriteframes_path` | string | ✅ | Ruta del recurso SpriteFrames |
| `animation_name` | string | ✅ | Nombre de la animación |
| `frame_index` | int | ✅ | Índice del frame a eliminar |

---

### `godot_spriteframes_rename_animation`
Renombra una animación existente.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `spriteframes_path` | string | ✅ | Ruta del recurso SpriteFrames |
| `old_name` | string | ✅ | Nombre actual |
| `new_name` | string | ✅ | Nuevo nombre |

---

### `godot_spriteframes_list_animations`
Lista todas las animaciones de un SpriteFrames con detalles.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `spriteframes_path` | string | ✅ | Ruta del recurso SpriteFrames |

**Retorna:**
- Lista de animaciones con: `name`, `fps`, `loop`, `frame_count`

---

## Herramientas de AnimatedSprite2D

Herramientas para controlar nodos AnimatedSprite2D.

### `godot_animsprite_attach`
Asigna un recurso SpriteFrames a un AnimatedSprite2D.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo AnimatedSprite2D |
| `spriteframes_path` | string | ✅ | Ruta del recurso SpriteFrames |

---

### `godot_animsprite_play`
Reproduce una animación en el AnimatedSprite2D.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo AnimatedSprite2D |
| `animation_name` | string | ❌ | Animación a reproducir (usa la actual si no se especifica) |
| `custom_speed` | number | ❌ | Velocidad personalizada (default: 1.0) |
| `from_end` | bool | ❌ | Reproducir desde el final |

---

### `godot_animsprite_stop`
Detiene la animación actual.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo AnimatedSprite2D |

---

### `godot_animsprite_pause`
Pausa la animación actual (mantiene el frame).

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo AnimatedSprite2D |

---

### `godot_animsprite_set_speed`
Establece la escala de velocidad del AnimatedSprite2D.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo AnimatedSprite2D |
| `speed_scale` | number | ✅ | Multiplicador de velocidad |

---

## Herramientas de Animation

Herramientas para crear y editar recursos Animation (animaciones programáticas).

### `godot_animation_create`
Crea un nuevo recurso Animation.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `name` | string | ✅ | Nombre de la animación |
| `length` | number | ✅ | Duración en segundos |
| `loop_mode` | string | ❌ | `none`, `linear`, `pingpong` |
| `step` | number | ❌ | Precisión del step (default: 0.1) |
| `save_path` | string | ❌ | Ruta para guardar .tres |

**Ejemplo de uso:**
```
"Crea una animación de 2 segundos con loop lineal"
```

---

### `godot_animation_add_track`
Agrega un track de valor a la animación.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `animation_path` | string | ✅ | Ruta del recurso Animation |
| `node_path` | string | ✅ | Ruta del nodo a animar |
| `property` | string | ✅ | Propiedad a animar (ej: `frame`, `position`, `modulate`) |

**Retorna:**
- `track_index`: Índice del track creado

**Ejemplo de uso:**
```
"Agrega un track para animar la propiedad 'frame' del Sprite2D"
```

---

### `godot_animation_insert_key`
Inserta un keyframe en un track de la animación.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `animation_path` | string | ✅ | Ruta del recurso Animation |
| `track_index` | int | ✅ | Índice del track |
| `time` | number | ✅ | Tiempo del keyframe (segundos) |
| `value` | any | ✅ | Valor del keyframe |

**Ejemplo de uso:**
```
"Inserta un keyframe en t=0.5s con valor frame=3"
```

---

## Herramientas de AnimationPlayer

Herramientas para controlar nodos AnimationPlayer.

### `godot_animplayer_add_animation`
Agrega una Animation al AnimationPlayer.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo AnimationPlayer |
| `animation_name` | string | ✅ | Nombre para la animación en el player |
| `animation_path` | string | ✅ | Ruta del recurso Animation |

---

### `godot_animplayer_play`
Reproduce una animación en el AnimationPlayer.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo AnimationPlayer |
| `animation_name` | string | ✅ | Nombre de la animación a reproducir |
| `custom_blend` | number | ❌ | Tiempo de blend personalizado |
| `custom_speed` | number | ❌ | Velocidad personalizada (default: 1.0) |
| `from_end` | bool | ❌ | Reproducir desde el final |

---

### `godot_animplayer_stop`
Detiene el AnimationPlayer.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo AnimationPlayer |
| `keep_state` | bool | ❌ | Mantener el estado actual (default: false) |

---

## Herramientas de TileSet

Herramientas para crear y gestionar TileSet y TileSetAtlasSource.

### `godot_tileset_ensure_atlas`
Crea o asegura que exista un TileSetAtlasSource en un TileSet.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `tileset_path` | string | ✅ | Ruta del TileSet (se crea si no existe) |
| `texture_path` | string | ✅ | Ruta de la textura del atlas |
| `tile_size` | object | ✅ | Tamaño de tile: `{x, y}` |
| `margins` | object | ❌ | Márgenes: `{x, y}` |
| `separation` | object | ❌ | Separación entre tiles: `{x, y}` |

**Retorna:**
- `source_id`: ID del source creado/existente

**Ejemplo de uso:**
```
"Crea un TileSet con tiles de 16x16 usando el tilemap.png"
```

---

### `godot_tileset_create_tile`
Crea un tile en el TileSetAtlasSource.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `tileset_path` | string | ✅ | Ruta del TileSet |
| `source_id` | int | ✅ | ID del source |
| `atlas_coords` | object | ✅ | Coordenadas en el atlas: `{x, y}` |
| `size` | object | ❌ | Tamaño en celdas: `{x, y}` (default: 1x1) |

---

### `godot_tileset_list_tiles`
Lista todos los tiles de un TileSetAtlasSource.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `tileset_path` | string | ✅ | Ruta del TileSet |
| `source_id` | int | ✅ | ID del source |

**Retorna:**
- Lista de tiles con: `atlas_coords`, `size`
- `texture_region_size`: Tamaño de región de textura

---

## Herramientas de Introspección

Herramientas para consultar metadatos antes de ejecutar acciones. Permiten al LLM conocer propiedades válidas, tipos, rangos y opciones disponibles en lugar de adivinar.

### `godot_class_get_property_list`
Obtiene todas las propiedades de una clase de Godot con tipos, hints, rangos y ejemplos.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `class_name` | string | ✅ | Nombre de la clase (Camera3D, Sprite2D, CharacterBody2D) |

**Retorna:**
- `class_name`: Nombre de la clase
- `parent_class`: Clase padre
- `properties[]`: Lista con name, type, hint, hint_string, enum_values, range, example
- `count`: Total de propiedades

**Ejemplo de uso:**
```
"Qué propiedades tiene Camera3D?"
```

---

### `godot_node_get_property_list`
Obtiene todas las propiedades de un nodo específico incluyendo valores actuales y propiedades de scripts.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo |

**Retorna:**
- `node_path`: Ruta del nodo
- `node_type`: Tipo de nodo
- `properties[]`: Lista con name, type, hint, current_value, example
- `count`: Total de propiedades

**Ejemplo de uso:**
```
"Muéstrame las propiedades del nodo Player"
```

---

### `godot_property_describe`
Describe una propiedad específica con detalle: tipo exacto, rango, valores enum y ejemplo de payload válido.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `target` | string | ✅ | Nombre de clase o ruta de nodo |
| `property_name` | string | ✅ | Nombre de la propiedad |

**Retorna:**
- `name`: Nombre de la propiedad
- `type`: Tipo (Vector2, float, Color, etc.)
- `hint`: Tipo de hint (range, enum, flags)
- `hint_string`: Valores del hint
- `enum_values[]`: Lista de valores enum si aplica
- `range`: Min, max, step si aplica
- `current_value`: Valor actual (solo para nodos)
- `example`: Ejemplo de payload JSON válido

**Ejemplo de uso:**
```
"Describe la propiedad 'fov' de Camera3D"
"Cómo debo configurar la propiedad 'position' del nodo Player?"
```

---

### `godot_validate_set_properties`
Valida propiedades sin aplicarlas. Detecta errores antes de modificar el nodo.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `node_path` | string | ✅ | Ruta del nodo |
| `properties` | object | ✅ | Propiedades a validar |

**Retorna:**
- `valid`: true/false
- `node_path`: Ruta del nodo
- `node_type`: Tipo del nodo
- `valid_properties[]`: Propiedades que pasaron validación
- `errors[]`: Lista de errores (propiedad inexistente, tipo incorrecto, valor fuera de rango)
- `warnings[]`: Advertencias (valores en límites)

**Ejemplo de uso:**
```
"Valida si puedo asignar position=(100,200) y fov=90 al nodo Camera"
```

---

### `godot_catalog_get`
Obtiene catálogo de opciones válidas para mallas, colisiones, luces, etc.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `kind` | string | ✅ | Tipo de catálogo |

**Tipos de catálogo disponibles:**
- `mesh`: BoxMesh, SphereMesh, CylinderMesh, etc. con parámetros
- `shape2d`: RectangleShape2D, CircleShape2D, etc.
- `shape3d`: BoxShape3D, SphereShape3D, etc.
- `light2d`: PointLight2D, DirectionalLight2D
- `light3d`: DirectionalLight3D, OmniLight3D, SpotLight3D
- `audio`: AudioStreamPlayer, AudioStreamPlayer2D/3D
- `loop_mode`: Modos de loop de Animation
- `background_mode`: Modos de fondo de Environment
- `node_2d`: Nodos 2D comunes
- `node_3d`: Nodos 3D comunes
- `node_ui`: Nodos de UI comunes

**Retorna:**
- `kind`: Tipo de catálogo
- `description`: Descripción
- `options[]`: Lista con nombre, parámetros y ejemplo

**Ejemplo de uso:**
```
"Qué tipos de malla puedo crear?"
"Qué formas de colisión 2D existen?"
```

---

### `godot_resource_get_info`
Obtiene información de un archivo de recurso (.tres/.res).

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `resource_path` | string | ✅ | Ruta del recurso |

**Retorna:**
- `path`: Ruta del recurso
- `class`: Tipo de recurso (Material, Animation, etc.)
- `properties`: Propiedades principales con valores
- `subresources[]`: Lista de subrecursos referenciados

**Ejemplo de uso:**
```
"Qué contiene el recurso res://materials/metal.tres?"
```

---

### `godot_animation_get_info`
Obtiene información detallada de un recurso Animation.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `animation_path` | string | ✅ | Ruta del recurso Animation |

**Retorna:**
- `path`: Ruta del recurso
- `length`: Duración en segundos
- `loop_mode`: none/linear/pingpong
- `step`: Precisión del step
- `track_count`: Número de tracks
- `tracks[]`: Lista con index, type, node_path, property, key_count, keys_preview

**Ejemplo de uso:**
```
"Muéstrame los tracks de la animación res://anims/walk.tres"
```

---

### `godot_spriteframes_get_info`
Obtiene información de un recurso SpriteFrames.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `spriteframes_path` | string | ✅ | Ruta del recurso SpriteFrames |

**Retorna:**
- `path`: Ruta del recurso
- `animation_count`: Número de animaciones
- `animations[]`: Lista con name, fps, loop, frame_count, frames (texturas)

**Ejemplo de uso:**
```
"Qué animaciones tiene el SpriteFrames del personaje?"
```

---

### `godot_texture_get_info`
Obtiene información de una textura, útil para spritesheets.

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `texture_path` | string | ✅ | Ruta de la textura |

**Retorna:**
- `path`: Ruta de la textura
- `class`: Tipo de textura
- `width`, `height`: Dimensiones en pixels
- `has_alpha`: Si tiene canal alpha
- `format`: Formato de imagen
- `is_likely_spritesheet`: Si parece ser un spritesheet
- `grid_suggestions[]`: Sugerencias de grid con cell_size, hframes, vframes, total_frames

**Ejemplo de uso:**
```
"Analiza el spritesheet res://sprites/character.png para saber cómo dividirlo"
```

---

### Flujo Recomendado con Introspección

Para evitar errores al configurar propiedades:

1. **Consultar propiedades disponibles:**
   - `godot_node_get_property_list(node_path)` para ver todas las propiedades

2. **Obtener detalle de una propiedad específica:**
   - `godot_property_describe(target, property_name)` para ver tipo, rango, ejemplo

3. **Validar antes de aplicar:**
   - `godot_validate_set_properties(node_path, properties)` para verificar errores

4. **Aplicar cambios:**
   - `godot_set_node_properties(node_path, properties)` con confianza

---

## Notas Importantes

### Rutas de Nodos
Las rutas de nodos siguen el formato del árbol de escena:
- Nodo raíz: `/root/NombreEscena` o simplemente `NombreEscena`
- Hijos: `Parent/Child/GrandChild`

### Colores
Los colores se especifican como objetos con componentes RGBA (valores de 0 a 1):
```json
{"r": 1.0, "g": 0.5, "b": 0.0, "a": 1.0}
```

### Vectores
- **Vector2:** `{"x": 100, "y": 200}` o `[100, 200]`
- **Vector3:** `{"x": 1, "y": 2, "z": 3}` o `[1, 2, 3]`

### Requisitos
- Godot 4.x con el addon GodotBridge habilitado
- El editor de Godot debe estar abierto con un proyecto cargado
- El token de autenticación debe estar configurado correctamente

---

## Ejemplos de Uso Común

### Crear una escena 3D con un cubo móvil
1. `godot_create_scene` - Crear escena Node3D
2. `godot_add_node` - Agregar MeshInstance3D
3. `godot_create_mesh` - Crear BoxMesh
4. `godot_create_material` - Aplicar material
5. `godot_write_script` - Crear script de movimiento
6. `godot_assign_script` - Asignar al nodo
7. `godot_add_input_action` - Configurar controles

### Crear un personaje 2D
1. `godot_create_scene` - Crear escena Node2D
2. `godot_add_node` - Agregar CharacterBody2D
3. `godot_add_node` - Agregar Sprite2D como hijo
4. `godot_set_sprite_texture` - Asignar textura
5. `godot_add_node` - Agregar CollisionShape2D
6. `godot_create_collision_shape` - Configurar forma
7. `godot_write_script` - Crear script de control

### Crear un personaje animado con SpriteFrames
1. `godot_spriteframes_create` - Crear recurso SpriteFrames
2. `godot_spriteframes_add_animation` - Agregar animación "idle"
3. `godot_spriteframes_add_animation` - Agregar animación "walk"
4. `godot_atlas_batch_create` - Crear atlas de cada frame desde spritesheet
5. `godot_spriteframes_add_frame` - Agregar frames a cada animación
6. `godot_spriteframes_set_fps` - Configurar velocidad
7. `godot_add_node` - Crear AnimatedSprite2D
8. `godot_animsprite_attach` - Asignar SpriteFrames al nodo
9. `godot_animsprite_play` - Reproducir animación

### Animar propiedades con AnimationPlayer
1. `godot_animation_create` - Crear recurso Animation
2. `godot_animation_add_track` - Agregar track para propiedad "position"
3. `godot_animation_insert_key` - Insertar keyframe en t=0
4. `godot_animation_insert_key` - Insertar keyframe en t=1
5. `godot_add_node` - Crear AnimationPlayer
6. `godot_animplayer_add_animation` - Agregar animación al player
7. `godot_animplayer_play` - Reproducir

### Crear un TileMap con TileSet
1. `godot_tileset_ensure_atlas` - Crear TileSet con atlas
2. `godot_tileset_create_tile` - Crear tiles individuales
3. `godot_add_node` - Agregar TileMap a la escena
4. `godot_set_node_properties` - Asignar TileSet al TileMap
