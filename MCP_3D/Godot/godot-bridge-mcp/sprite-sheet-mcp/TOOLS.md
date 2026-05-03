# Sprite Sheet MCP - Herramientas

Este documento describe las herramientas disponibles en el MCP de análisis de spritesheets.

## Herramientas Disponibles

### 1. `sprite_analyze_sheet`

Analiza un spritesheet y detecta frames automáticamente usando canal alpha o segmentación por color de fondo.

**Parámetros:**
| Parámetro | Tipo | Requerido | Default | Descripción |
|-----------|------|-----------|---------|-------------|
| `image_path` | string | Sí | - | Ruta al archivo de imagen (PNG recomendado) |
| `mode` | string | No | `"auto"` | Modo de detección: `auto`, `alpha`, `bg_color` |
| `bg_color` | object | No | `null` | Color de fondo `{r, g, b, tolerance}` para modo `bg_color` |
| `min_area` | integer | No | `64` | Área mínima en píxeles para considerar un frame válido |
| `merge_distance` | integer | No | `4` | Distancia máxima para unir componentes cercanos |

**Ejemplo:**
```json
{
  "image_path": "C:/proyecto/Art/mage_sheet.png",
  "mode": "alpha",
  "min_area": 100,
  "merge_distance": 8
}
```

**Respuesta:**
```json
{
  "sheet": {"width": 1024, "height": 512, "has_alpha": true, "path": "..."},
  "detection": {"mode": "alpha", "raw_components": 48, "merged_frames": 32},
  "frames": [
    {"id": 0, "x": 0, "y": 0, "w": 64, "h": 64},
    {"id": 1, "x": 64, "y": 0, "w": 64, "h": 64}
  ]
}
```

---

### 2. `sprite_slice_frames`

Recorta frames detectados y los exporta como archivos PNG individuales o como metadatos de atlas.

**Parámetros:**
| Parámetro | Tipo | Requerido | Default | Descripción |
|-----------|------|-----------|---------|-------------|
| `image_path` | string | Sí | - | Ruta al spritesheet |
| `frames` | array | Sí | - | Array de frames de `sprite_analyze_sheet` |
| `output_dir` | string | Sí | - | Directorio de salida |
| `export_mode` | string | No | `"png_frames"` | `png_frames` o `atlas_json` |
| `naming` | string | No | `"frame_{id}"` | Patrón de nombres |
| `padding` | integer | No | `0` | Padding alrededor de cada frame |

**Ejemplo:**
```json
{
  "image_path": "C:/proyecto/Art/mage_sheet.png",
  "frames": [{"id": 0, "x": 0, "y": 0, "w": 64, "h": 64}],
  "output_dir": "C:/proyecto/Art/mage_frames",
  "export_mode": "png_frames"
}
```

---

### 3. `sprite_group_animations`

Agrupa frames en animaciones usando clustering espacial (filas/columnas) o similitud visual.

**Parámetros:**
| Parámetro | Tipo | Requerido | Default | Descripción |
|-----------|------|-----------|---------|-------------|
| `frames` | array | Sí | - | Array de frames |
| `grouping_mode` | string | No | `"rows"` | `rows`, `columns`, `grid`, `spatial_cluster` |
| `row_tolerance` | integer | No | `10` | Tolerancia en Y para agrupar por filas |
| `expected_animations` | integer | No | `null` | Número esperado de animaciones (ayuda al clustering) |
| `ordering` | string | No | `"x_asc"` | Orden dentro de grupos: `x_asc`, `y_asc`, `id` |

**Ejemplo:**
```json
{
  "frames": [{"id": 0, "x": 0, "y": 0, "w": 64, "h": 64}],
  "grouping_mode": "rows",
  "row_tolerance": 15
}
```

**Respuesta:**
```json
{
  "grouping_mode": "rows",
  "animation_count": 4,
  "animations": {
    "anim_00": {"frameIds": [0, 1, 2, 3], "fps": 10, "loop": true},
    "anim_01": {"frameIds": [4, 5, 6, 7], "fps": 10, "loop": true}
  }
}
```

---

### 4. `sprite_preview_layout`

Genera una imagen de debug con bounding boxes y etiquetas sobre los frames detectados.

**Parámetros:**
| Parámetro | Tipo | Requerido | Default | Descripción |
|-----------|------|-----------|---------|-------------|
| `image_path` | string | Sí | - | Ruta al spritesheet |
| `frames` | array | Sí | - | Array de frames |
| `animations` | object | No | `null` | Grupos de animaciones para colorear |
| `output_path` | string | Sí | - | Ruta para guardar la imagen preview |
| `show_labels` | boolean | No | `true` | Mostrar IDs de frame |
| `show_dimensions` | boolean | No | `false` | Mostrar dimensiones |

**Ejemplo:**
```json
{
  "image_path": "C:/proyecto/Art/mage_sheet.png",
  "frames": [...],
  "animations": {"idle": {"frameIds": [0,1,2,3]}},
  "output_path": "C:/proyecto/debug_preview.png",
  "show_labels": true
}
```

---

### 5. `sprite_export_godot_json`

Exporta los datos analizados como JSON compatible con las herramientas de godot-mcp-bridge.

**Parámetros:**
| Parámetro | Tipo | Requerido | Default | Descripción |
|-----------|------|-----------|---------|-------------|
| `source_image` | string | Sí | - | Ruta al spritesheet original |
| `frames` | array | Sí | - | Array de frames |
| `animations` | object | Sí | - | Grupos de animaciones |
| `normalize_size` | string | No | `"none"` | `none`, `max`, `median` |
| `pivot` | string | No | `"center"` | `center`, `bottom_center`, `top_left` |
| `output_path` | string | No | `null` | Ruta para guardar JSON |
| `godot_texture_path` | string | No | `null` | Ruta res:// para Godot |

**Ejemplo:**
```json
{
  "source_image": "C:/proyecto/Art/mage_sheet.png",
  "frames": [...],
  "animations": {"idle": {"frameIds": [0,1,2,3], "fps": 8, "loop": true}},
  "normalize_size": "max",
  "pivot": "bottom_center",
  "godot_texture_path": "res://Art/mage_sheet.png"
}
```

**Respuesta:**
```json
{
  "meta": {"generator": "sprite-sheet-mcp", "version": "1.0.0"},
  "texture": {"path": "res://Art/mage_sheet.png"},
  "frames": [...],
  "animations": {...},
  "godot_commands": {
    "commands": [
      {"tool": "godot_atlas_batch_create", "arguments": {...}},
      {"tool": "godot_spriteframes_create", "arguments": {...}}
    ]
  }
}
```

---

## Flujo de Trabajo Recomendado

### Paso 1: Analizar el spritesheet
```
sprite_analyze_sheet(image_path="...", mode="auto")
```

### Paso 2: Generar preview para validar
```
sprite_preview_layout(image_path="...", frames=[...], output_path="preview.png")
```

### Paso 3: Agrupar en animaciones
```
sprite_group_animations(frames=[...], grouping_mode="rows")
```

### Paso 4: Exportar para Godot
```
sprite_export_godot_json(source_image="...", frames=[...], animations={...})
```

### Paso 5: Usar el resultado con godot-mcp-bridge
El JSON exportado incluye `godot_commands` con los comandos pre-armados para:
1. `godot_atlas_batch_create` - Crear AtlasTextures
2. `godot_spriteframes_create` - Crear recurso SpriteFrames
3. `godot_spriteframes_add_animation` - Agregar cada animación
4. `godot_spriteframes_add_frame` - Agregar frames a cada animación

---

## Modos de Detección

### `alpha` (Recomendado para PNG con transparencia)
Usa el canal alpha para detectar sprites. Píxeles con alpha > 10 se consideran parte del sprite.

### `bg_color` (Para imágenes sin transparencia)
Detecta el color de fondo y lo excluye. Por defecto detecta el color de las esquinas.

### `auto`
Selecciona automáticamente: usa `alpha` si la imagen tiene canal alpha, sino `bg_color`.

---

## Modos de Agrupación

### `rows`
Agrupa frames que están en la misma fila (similar posición Y). Ideal para spritesheets organizados horizontalmente.

### `columns`
Agrupa frames en la misma columna (similar posición X). Para spritesheets verticales.

### `grid`
Detecta estructura de grilla y agrupa por filas.

### `spatial_cluster`
Usa DBSCAN para detectar clusters espaciales. Mejor para spritesheets caóticos o irregulares.
