# Informe de Chequeo de Herramientas MCP - Godot Bridge

**Fecha:** 14 de Enero 2026  
**Versión Godot:** 4.4.1-stable  
**Proyecto:** prueba-plataformero

---

## Resumen Ejecutivo

| Estado | Cantidad | Porcentaje |
|--------|----------|------------|
| ✅ Funcionando | 18 | 60% |
| ❌ Con errores | 10 | 33% |
| ⚠️ Comportamiento dudoso | 2 | 7% |

---

## Herramientas Funcionando Correctamente ✅

### Proyecto
| Herramienta | Estado | Notas |
|-------------|--------|-------|
| `godot_get_project_info` | ✅ OK | Retorna info completa |
| `godot_remove_input_action` | ✅ OK | Funciona correctamente |

### Editor
| Herramienta | Estado | Notas |
|-------------|--------|-------|
| `godot_get_editor_state` | ✅ OK | Retorna estado completo |
| `godot_open_scene` | ✅ OK | Abre escenas correctamente |

### Escena
| Herramienta | Estado | Notas |
|-------------|--------|-------|
| `godot_get_scene_tree` | ✅ OK | Retorna árbol completo |
| `godot_list_nodes` | ✅ OK | Lista nodos correctamente |
| `godot_create_scene` | ✅ OK | Crea escenas nuevas |

### Nodos (parcial)
| Herramienta | Estado | Notas |
|-------------|--------|-------|
| `godot_set_node_properties` | ✅ OK | Funciona con paths simples (ej: "Background") |
| `godot_set_modulate` | ✅ OK | Aplica colores correctamente |
| `godot_assign_script` | ✅ OK | Asigna scripts a nodos |

### Entorno
| Herramienta | Estado | Notas |
|-------------|--------|-------|
| `godot_create_environment` | ✅ OK | Crea WorldEnvironment |
| `godot_configure_camera` | ✅ OK | Configura cámaras |

### Scripts
| Herramienta | Estado | Notas |
|-------------|--------|-------|
| `godot_read_script` | ✅ OK | Lee contenido de scripts |
| `godot_write_script` | ✅ OK | Escribe scripts nuevos |

### Archivos
| Herramienta | Estado | Notas |
|-------------|--------|-------|
| `godot_search_files` | ✅ OK | Busca archivos por tipo |

### Ejecución
| Herramienta | Estado | Notas |
|-------------|--------|-------|
| `godot_run_main` | ✅ OK | Ejecuta escena principal |
| `godot_run_current` | ✅ OK | Ejecuta escena actual |
| `godot_stop` | ✅ OK | Detiene ejecución |

---

## Herramientas con Errores ❌

### Error Principal: "Node not found" / "Parent node not found"

**Código de error:** `RPC Error 4010`

Las siguientes herramientas fallan al intentar encontrar nodos usando paths relativos:

| Herramienta | Error | Path probado |
|-------------|-------|--------------|
| `godot_add_node` | Parent node not found | `"Game"` |
| `godot_remove_node` | Node not found | `"WorldEnvironment"` |
| `godot_instance_scene` | Parent node not found | `"Game"` |
| `godot_create_light` | Parent node not found | `"Game"` |
| `godot_create_audio_player` | Parent node not found | `"Game"` |
| `godot_create_mesh` | Node not found | `"Player"` |
| `godot_create_material` | Node not found | `"Background"` |
| `godot_create_collision_shape` | Node not found | `"Player/CharacterBody2D/CollisionShape2D"` |
| `godot_set_sprite_texture` | Node not found | `"Player/CharacterBody2D/Sprite2D"` |

### Error: "Unknown key"

**Código de error:** `RPC Error 4001`

| Herramienta | Error | Parámetro |
|-------------|-------|-----------|
| `godot_add_input_action` | Unknown key | `"KEY_T"` |

---

## Herramientas con Comportamiento Dudoso ⚠️

| Herramienta | Comportamiento | Notas |
|-------------|----------------|-------|
| `godot_get_node_properties` | Retorna `null` | No retorna error, pero tampoco datos |
| `godot_save_scene` | Retorna `null` | No confirma si guardó |

---

## Análisis de Causas Raíz

### 1. Inconsistencia en Resolución de Paths de Nodos

**Problema:** Algunas herramientas aceptan paths relativos simples (ej: `"Background"`) mientras que otras requieren paths completos del editor.

**Herramientas afectadas:**
- Todas las del módulo `resources.*` (create_light, create_audio_player, create_mesh, etc.)
- `scene.add_node`, `scene.remove_node`, `scene.instance_scene`

**Herramientas que SÍ funcionan con paths simples:**
- `scene.set_node_properties`
- `resources.set_modulate`
- `scene.assign_script`
- `resources.configure_camera`

**Causa probable:** Los handlers en `rpc_handlers.gd` usan diferentes métodos para resolver nodos:
- Algunos usan `_get_scene_root().get_node_or_null(path)`
- Otros podrían estar buscando desde `/root` del editor

### 2. Formato de Teclas Incorrecto

**Problema:** `godot_add_input_action` no reconoce el formato `"KEY_T"`.

**Causa probable:** El código usa `OS.find_keycode_from_string()` que podría requerir un formato diferente (posiblemente solo `"T"` o el valor numérico del keycode).

### 3. Handlers Retornando Null

**Problema:** `godot_get_node_properties` y `godot_save_scene` retornan `null` en lugar de datos o error.

**Causa probable:** Los handlers no están implementados correctamente o hay un error silencioso.

---

## Plan de Reparación

### Prioridad Alta 🔴

1. **Unificar resolución de paths de nodos**
   - Archivo: `godot-addon/addons/godotbridge/rpc_handlers.gd`
   - Todos los handlers deben usar el mismo método para encontrar nodos
   - Implementar función helper `_find_node_by_path(path: String)` que:
     - Si el path empieza con `/`, buscar desde root
     - Si no, buscar desde la raíz de la escena editada

2. **Corregir formato de teclas en input actions**
   - Archivo: `godot-addon/addons/godotbridge/rpc_handlers.gd`
   - Método: `_project_add_input_action`
   - Investigar formato correcto para `OS.find_keycode_from_string()`

### Prioridad Media 🟡

3. **Corregir handlers que retornan null**
   - `_scene_get_node_properties`: Verificar implementación
   - `_editor_save_scene`: Agregar respuesta de confirmación

### Prioridad Baja 🟢

4. **Mejorar mensajes de error**
   - Incluir el path que se intentó resolver
   - Sugerir formato correcto

---

## Handlers a Revisar

```
rpc_handlers.gd:
├── _project_add_input_action     ❌ Revisar formato de keys
├── _scene_get_node_properties    ⚠️ Retorna null
├── _scene_add_node               ❌ Path resolution
├── _scene_remove_node            ❌ Path resolution
├── _scene_instance_scene         ❌ Path resolution
├── _editor_save_scene            ⚠️ Retorna null
├── resources.create_light        ❌ Path resolution
├── resources.create_audio_player ❌ Path resolution
├── resources.create_mesh         ❌ Path resolution
├── resources.create_material     ❌ Path resolution
├── resources.create_collision_shape ❌ Path resolution
└── resources.set_sprite_texture  ❌ Path resolution
```

---

## Notas Adicionales

- El sistema de paths del editor de Godot incluye toda la jerarquía interna del editor, lo que complica la resolución de nodos
- Las herramientas que funcionan probablemente tienen una implementación especial para manejar esto
- Se recomienda revisar cómo `_get_scene_root()` está implementado y asegurar que todos los handlers lo usen consistentemente
