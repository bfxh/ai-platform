# 🎮 TextureAlchemy - Workflow Guide

Complete workflow examples for common use cases.

---

## 🚀 Quick Start Workflows

### Workflow 1: Fastest PBR Extraction (3 Nodes)

**What it does:** Extract PBR maps from a single image in the fastest way possible.

**Nodes needed:**
1. Load Image
2. Marigold Depth Estimation (run twice: appearance + lighting models)
3. PBR Extractor
4. PBR Saver
5. Preview Image

**Setup:**
```
Load Image
   ├─> MarigoldDepthEstimation_v2 (model: "appearance")
   │   └─> PBR Extractor (marigold_appearance input)
   │
   └─> MarigoldDepthEstimation_v2 (model: "lighting")
       └─> PBR Extractor (marigold_lighting input)
               │
               ├─ albedo_source: "appearance"
               ├─ gamma_albedo: 0.45
               ├─ gamma_appearance: 0.7
               └─ gamma_lighting: 0.45
               │
               ↓ (pbr_pipe output)
               │
           PBR Saver
               ├─ base_name: "my_material"
               ├─ output_path: "pbr_materials"
               ├─ file_format: "png"
               └─ enumeration_mode: "enumerate"
               │
               ↓ (images output)
               │
           Preview Image (see all maps at once!)
```

**Result:** Gets albedo, roughness, metallic, and AO in one go!

---

### Workflow 2: Complete PBR Material (Normal + Height)

**What it does:** Full PBR material with all maps including normals and height.

**Nodes needed:**
1. Load Image
2. Marigold x2 (appearance + lighting)
3. Lotus Sampler x2 (normal + depth) → VAEDecode
4. PBR Extractor
5. Normal Processor
6. Height Processor
7. PBR Combiner
8. PBR Pipeline Adjuster
9. PBR Saver

**Setup:**
```
Load Image ──┬──> Marigold (appearance) ──┐
             │                             ├──> PBR Extractor ──> pbr_pipe ──┐
             ├──> Marigold (lighting) ─────┘                                  │
             │                                                                │
             ├──> VAEEncode ──> Lotus (normal) ──> VAEDecode ──> Normal Processor ──┐
             │                                                   ├─ invert_green: True │
             │                                                   └─ strength: 1.0      │
             │                                                                         │
             └──> VAEEncode ──> Lotus (depth) ──> VAEDecode ──> Height Processor ───┐│
                                                                 ├─ invert: False     ││
                                                                 └─ bit_depth: 16     ││
                                                                                      ││
                                                                                      ↓↓
                                                                        PBR Combiner
                                                                        ├─ pbr_pipe (from extractor)
                                                                        ├─ normal (from processor)
                                                                        └─ height (from processor)
                                                                                      ↓
                                                                        PBR Pipeline Adjuster
                                                                        ├─ ao_strength_albedo: 1.0
                                                                        ├─ roughness_strength: 1.2
                                                                        ├─ normal_strength: 1.0
                                                                        └─ albedo_saturation: 1.1
                                                                                      ↓
                                                                        PBR Saver → Preview
```

**Result:** Complete 7-map PBR material ready for any engine!

---

## 🎨 Advanced Workflows

### Workflow 3: Seamless Tile-able Material with Preview

**What it does:** Create seamlessly repeating PBR material for games with tiling preview.

**Additional nodes:**
- Seamless Tiling Maker (after load image)
- Texture Tiler (to preview tiling)
- All standard PBR extraction nodes

**Setup:**
```
Load Image
   ↓
Seamless Tiling Maker
├─ method: "blend_edges"
└─ blend_width: 0.1
   ├─> image (seamless) ──┬──> Texture Tiler (2x2) ──> Preview (check seams!)
   │                       └──> [PBR extraction...]
   └─> edge_mask (for inpainting) ──> Preview/Save (optional)
   ↓
[Continue with standard PBR extraction...]
   ↓
PBR Saver
├─ base_name: "tileable_material"
└─ file_format: "png"
```

**Result:** Perfect for repeating game textures, no visible seams! Preview shows how it tiles.

**Advanced - Offset Testing + Inpainting:**
```
Seamless Tiling Maker
├─> image ────────────┬──> Texture Offset (test different alignments)
│                      │    ├─ offset_x: 0.5 (shift to check seams)
│                      │    └─ offset_y: 0.5
│                      │         ↓
│                      │    Texture Tiler (3x3) ──> Preview
│                      │
└─> edge_mask ────────┼──> Inpainting Node (cleanup seams)
                      │    ├─ mask: edge_mask
                      │    └─ denoise: 0.3-0.5
                      ↓
                  Ultra-clean seamless texture
```

---

### Workflow 4: Material with Procedural Wear

**What it does:** Add realistic weathering and edge damage to materials.

**Additional nodes:**
- Curvature Generator
- Wear Generator
- PBR Pipe Preview (for checking)

**Setup:**
```
[Standard PBR extraction to pbr_pipe]
   ↓
PBR Splitter ──┬──> normal ──> Curvature Generator ──┐
               │    ├─ input_type: "normal"          │
               │    ├─ strength: 1.0                 │
               │    └─ blur_radius: 1.0              │
               │                                      │
               └──> ao ─────────────────────────────┐│
               └──> albedo ──────────────────────┐  ││
                                                 │  ││
                                                 ↓  ↓↓
                                            Wear Generator
                                            ├─ wear_strength: 0.5
                                            ├─ edge_wear: 0.7
                                            ├─ dirt_strength: 0.3
                                            ├─ curvature: (from generator)
                                            └─ ao: (from splitter)
                                                 │
                                                 ↓
                                            worn_albedo + wear_mask
                                                 │
                                                 ↓
                                            PBR Combiner (override albedo)
                                            ├─ pbr_pipe: (original)
                                            └─ albedo: (worn version)
                                                 ↓
                                            PBR Saver
```

**Result:** Realistic aged/weathered materials with edge damage!

---

### Workflow 5: Channel-Packed ORM Texture

**What it does:** Create industry-standard ORM (AO+Roughness+Metallic) packed texture.

**Setup:**
```
[Standard PBR extraction]
   ↓
PBR Splitter
├─> ao ─────────> Channel Packer (red_channel) ──┐
├─> roughness ──> Channel Packer (green_channel) ─┤
└─> metallic ───> Channel Packer (blue_channel) ──┘
                  ├─ preset: "orm_unity"
                       ↓
                  Save Image
                  (ORM_packed.png)
                  R=AO, G=Roughness, B=Metallic
```

**Result:** Single texture instead of 3 (saves VRAM in games!)

---

### Workflow 6: Material Mixing (Layered Materials)

**What it does:** Blend two different materials together.

**Setup:**
```
Material A:
  Load Image A → [Extract PBR] → pbr_pipe_A ──┐
                                               │
Material B:                                    │
  Load Image B → [Extract PBR] → pbr_pipe_B ──┤
                                               │
Optional Mask:                                 │
  Load Mask → (grayscale image) ──────────────┤
                                               ↓
                                    PBR Material Mixer
                                    ├─ base_pipe: A
                                    ├─ overlay_pipe: B
                                    ├─ blend_mode: "overlay"
                                    ├─ blend_strength: 0.5
                                    └─ mask: (optional)
                                               ↓
                                    PBR Saver → Preview
```

**Example:** Blend brick (base) + moss (overlay) for aged walls!

---

### Workflow 7: Stylized/Artistic Materials

**What it does:** Create stylized materials with custom color gradients.

**Setup:**
```
[Extract PBR to get height/AO]
   ↓
PBR Splitter ──> height ──> Gradient Map ──> Color Ramp ──┐
                            ├─ min: 0.2     ├─ preset: "heat"   │
                            └─ max: 0.8     └─ (or custom)      │
                                                                 ↓
                                                    Stylized Albedo
                                                                 ↓
                                            PBR Combiner (override albedo)
                                            ├─ pbr_pipe: (original)
                                            └─ albedo: (stylized)
                                                                 ↓
                                            HSV Adjuster (optional)
                                            ├─ hue_shift: 0.1
                                            ├─ saturation: 1.5
                                            └─ value: 1.1
                                                                 ↓
                                            PBR Saver
```

**Result:** Artistic materials with custom color schemes!

---

### Workflow 8: High-Detail Normals

**What it does:** Layer multiple normal details for maximum detail.

**Setup:**
```
Lotus Normal (large detail) ──> Normal Processor ──┐
                                ├─ strength: 1.0    │
                                                     ↓
                                        Normal Map Combiner #1
                                        ├─ base_normal: (Lotus)
                                        ├─ detail_normal: (photo detail)
                                        ├─ blend_mode: "reoriented"
                                        └─ detail_strength: 0.7
                                                     ↓
                                        Normal Map Combiner #2
                                        ├─ base_normal: (combined)
                                        ├─ detail_normal: (micro detail)
                                        ├─ blend_mode: "reoriented"
                                        └─ detail_strength: 0.5
                                                     ↓
                                        Detail Map Blender (optional)
                                        ├─ base: (normals)
                                        ├─ detail: (surface detail)
                                        ├─ map_type: "normal"
                                        └─ strength: 0.3
                                                     ↓
                                        Final Normal → PBR Combiner
```

**Result:** Multi-layer normals with macro + micro detail!

---

### Workflow 9: Cross-Platform Material Export

**What it does:** Export materials for both OpenGL and DirectX engines.

**Setup:**
```
[Extract complete PBR with normals]
   ↓
PBR Pipeline Adjuster → PBR Saver (OpenGL version)
├─ invert_normal_green: False  ├─ base_name: "material_GL"
                               │
                               ↓
                    PBR Splitter → normal → Normal Format Converter
                                              ├─ conversion: "OpenGL_to_DirectX"
                                                           ↓
                                              DirectX Normal → PBR Combiner
                                                           ↓
                                              PBR Saver (DirectX version)
                                              ├─ base_name: "material_DX"
```

**Result:** Two versions for maximum compatibility!

---

### Workflow 10: Generate Missing Maps

**What it does:** Generate normal and AO from height when you only have height map.

**Setup:**
```
Load Height Map
   ├──> Height to Normal Converter ──> normal ──┐
   │    ├─ method: "scharr"                     │
   │    └─ strength: 1.5                        │
   │                                             │
   └──> AO Approximator ──> ao ─────────────────┤
        ├─ radius: 12                            │
        ├─ samples: 24                           │
        ├─ strength: 1.2                         │
        └─ normal: (from converter)              │
                                                  ↓
                                        PBR Combiner
                                        ├─ height: (original)
                                        ├─ normal: (generated)
                                        └─ ao: (generated)
                                                  ↓
                                        PBR Saver
```

**Result:** Complete PBR set from just a height map!

---

## 🧪 Testing Workflows

### Test 1: Format Compatibility Test

**Purpose:** Verify all export formats work correctly.

**Setup:**
```
[Any PBR extraction workflow]
   ↓
PBR Saver #1 (PNG test)
├─ base_name: "test_png"
├─ file_format: "png"
   ↓
PBR Saver #2 (JPG test)
├─ base_name: "test_jpg"
├─ file_format: "jpg"
   ↓
PBR Saver #3 (EXR test)
├─ base_name: "test_exr"
├─ file_format: "exr"
   ↓
PBR Saver #4 (TIFF test)
├─ base_name: "test_tiff"
├─ file_format: "tiff"
```

**Check:** All formats save correctly, EXR has higher precision.

---

### Test 2: Pipeline Passthrough Test

**Purpose:** Verify PBR_PIPE passes through correctly.

**Setup:**
```
PBR Extractor → PBR Pipe Preview #1 → Preview
                      ↓
                PBR Combiner (add normal)
                      ↓
                PBR Pipe Preview #2 → Preview
                      ↓
                PBR Pipeline Adjuster
                      ↓
                PBR Pipe Preview #3 → Preview
                      ↓
                PBR Saver
```

**Check:** Each preview shows cumulative changes, final save has all maps.

---

### Test 3: Node Performance Test

**Purpose:** Compare speeds of different methods.

**Color Ramp Speed Test:**
```
Load 4K image → Color Ramp (custom gradient) → Preview
- Measure: Should complete in <100ms
```

**Normal Conversion Speed Test:**
```
Load 2K height → Height to Normal
├─ method: "sobel" (time this)
├─ method: "scharr" (time this)
└─ method: "prewitt" (time this)
```

**AO Generation Speed Test:**
```
Load height → AO Approximator
├─ samples: 8 (fast)
├─ samples: 16 (balanced)
├─ samples: 32 (quality)
└─ samples: 64 (slow but best)
```

---

### Test 4: Quality Comparison Test

**Purpose:** Compare different blend modes and methods.

**Normal Blending Methods:**
```
Base Normal ──┬──> Normal Combiner #1 (reoriented) → Preview
Detail Normal ┤──> Normal Combiner #2 (whiteout) → Preview
              └──> Normal Combiner #3 (linear) → Preview
```

**Material Mixing Modes:**
```
Material A ──┬──> Material Mixer (mix) → Preview
Material B ──┼──> Material Mixer (multiply) → Preview
             ├──> Material Mixer (overlay) → Preview
             ├──> Material Mixer (add) → Preview
             └──> Material Mixer (screen) → Preview
```

---

### Test 5: Edge Case Test

**Purpose:** Test node robustness with unusual inputs.

**Tests:**
1. **Empty pipe:** PBR Combiner with no inputs → Should output empty pipe
2. **Single channel:** Load grayscale → Color Ramp → Should work
3. **Different sizes:** Mix 512x512 + 1024x1024 materials → Should auto-resize
4. **Missing maps:** PBR Saver with partial pipe → Should save only available maps
5. **Zero values:** All parameters at min/max extremes → Should clamp gracefully

---

## 📊 Benchmark Results (Reference)

Tested on RTX 3080, 1024x1024 images:

| Node | Time | Notes |
|------|------|-------|
| PBR Extractor | 50ms | Fast, GPU |
| Color Ramp | <100ms | 100x faster than v1.0 |
| Normal to Depth (hybrid) | 500ms | Iterative, CPU |
| Height to Normal | 10ms | Very fast, GPU |
| Curvature Generator | 50ms | Fast convolution |
| Wear Generator | 100ms | Multiple passes |
| Channel Packer | <5ms | Instant |
| Material Mixer | 30ms | Per map, GPU |
| Seamless Tiling (blend) | 80ms | Edge blending |
| HSV Adjuster | 40ms | RGB→HSV→RGB |

---

## 🎯 Workflow Templates

### Template: Game Asset Creation
1. Load texture → Seamless Tiling
2. Extract PBR (Marigold + Lotus)
3. Add wear (Curvature + Wear Generator)
4. Pack channels (Channel Packer ORM)
5. Scale LODs (Texture Scaler 1x, 0.5x, 0.25x)
6. Save all versions

### Template: Archviz Material
1. Load photo → Extract PBR
2. Add detail (Detail Map Blender)
3. Enhance quality (Pipeline Adjuster)
4. Mix variations (HSV Adjuster)
5. Export high-res (EXR format)

### Template: Stylized Art
1. Extract basic PBR
2. Custom colors (Color Ramp)
3. Artistic adjustment (HSV Adjuster)
4. Add effects (Wear/Gradient Maps)
5. Export for renderer

---

## 💾 Saving Best Practices

**For Games:**
- Format: PNG (8-bit)
- Pack ORM: Yes
- Resolution: Power of 2 (512, 1024, 2048)
- Enumerate: Yes (for variants)

**For Film/Archviz:**
- Format: EXR (32-bit)
- Pack: No (separate maps)
- Resolution: As high as needed
- Precision: Maximum (32-bit)

**For Web/Mobile:**
- Format: JPG (compressed)
- Pack ORM: Yes (save bandwidth)
- Resolution: 512x512 max
- Optimize: Use Texture Scaler

---

**These workflows cover 90% of PBR material creation needs!** 🚀

For custom workflows, mix and match nodes as needed. The pipeline system makes it easy to experiment!

