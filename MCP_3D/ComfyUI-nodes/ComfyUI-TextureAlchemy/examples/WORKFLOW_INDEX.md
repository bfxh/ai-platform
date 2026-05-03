# 📂 TextureAlchemy - Workflow Index

Complete list of example workflows with descriptions.

---

## 🚀 **QUICK START WORKFLOWS**

### **10_fastest_pbr_extraction.json** ⚡
**Difficulty:** Beginner  
**Time:** ~2 seconds  
**Purpose:** Fastest way to extract PBR maps from a photo

**What you get:**
- Albedo, Roughness, Metallic, AO
- Lighting map

**Nodes used:**
- Load Image
- Marigold x2 (appearance + lighting)
- PBR Extractor
- PBR Saver
- Preview

**Perfect for:** Quick material creation, learning the basics

---

## 🎨 **ADVANCED TECHNIQUE WORKFLOWS**

### **11_frequency_separation_workflow.json** 🔬
**Difficulty:** Intermediate  
**Time:** ~1 second  
**Purpose:** Professional texture editing - separate tone from detail

**What it demonstrates:**
- Frequency Separation (the pro secret!)
- Low frequency (tone/color) editing
- High frequency (detail) editing
- Recombining with adjustments

**Nodes used:**
- Load Image
- Frequency Separation
- Frequency Recombine
- Preview x4

**Perfect for:** 
- Professional texture retouching
- Editing tone without affecting detail
- Boosting or reducing detail independently
- Skin/fabric texture work

**Pro Tip:** Edit low and high frequencies separately before recombining!

---

### **12_procedural_material_creation.json** 🎲
**Difficulty:** Advanced  
**Time:** ~3 seconds  
**Purpose:** Create complete PBR materials from scratch (no photo needed!)

**What it demonstrates:**
- Procedural noise generation
- Pattern generation (brick)
- Blending multiple layers
- Scratch generation
- Color ramp stylization
- Normal map combination
- Complete PBR assembly

**Nodes used:**
- Procedural Noise Generator (FBM)
- Pattern Generator (brick)
- Blend Mode Utility x2
- Scratches Generator
- Color Ramp
- Height to Normal
- Normal Map Combiner
- Edge Wear Mask Generator
- PBR Combiner
- PBR Saver

**Perfect for:**
- Creating materials without photos
- Stylized/game materials
- Learning procedural techniques
- Experimental art

**What you'll learn:**
- Layering techniques
- Procedural generation
- Blend mode usage
- PBR assembly from components

---

## 📦 **SPECIALIZED WORKFLOWS**

### **13_material_mixing_blending.json** 🎭
**Coming soon!**  
**Purpose:** Blend two different materials together with masks

**Features:**
- Multi-texture blending
- Layer masks
- Blend modes (24 options!)
- Material Mixer node

**Use case:** Mix brick + moss for aged walls

---

### **14_advanced_materials_sss_anisotropy.json** ✨
**Coming soon!**  
**Purpose:** Create advanced material types

**Features:**
- SSS map generation (skin, wax)
- Anisotropy maps (brushed metal, hair)
- Translucency maps (leaves)
- Emission masks (glowing elements)

**Use case:** Organic materials, metals, special effects

---

### **15_mask_generation_weathering.json** 🎭
**Coming soon!**  
**Purpose:** Generate masks for weathering and effects

**Features:**
- Edge Wear Mask Generator
- Dirt/Grime Mask Generator
- Gradient Mask Generator
- Color Selection Mask

**Use case:** Realistic weathering, selective editing

---

### **16_texture_analysis_qa.json** 📊
**Coming soon!**  
**Purpose:** Analyze and validate textures

**Features:**
- Texture Analyzer (stats + seamless check!)
- UV Checker Generator
- Edge Detection
- Quality metrics

**Use case:** QA workflows, debugging

---

## 🧪 **TEST & LEARNING WORKFLOWS**

### **17_blend_modes_comparison.json** 🎨
**Coming soon!**  
**Purpose:** Compare all 24 blend modes side-by-side

**Perfect for:** Learning which blend mode to use when

---

### **18_noise_types_showcase.json** 🌊
**Coming soon!**  
**Purpose:** See all 6 noise types and pattern types

**Features:**
- Perlin, FBM, Turbulence, Voronoi, Cellular, White noise
- All 7 pattern types
- Side-by-side comparison

**Perfect for:** Understanding procedural generation

---

### **19_detail_control_showcase.json** 🔍
**Coming soon!**  
**Purpose:** Demonstrate all detail control nodes

**Features:**
- Frequency Separation
- Clarity Enhancer
- Smart Blur
- Micro Detail Overlay
- Before/after comparisons

**Perfect for:** Learning professional detail control

---

### **20_color_grading_showcase.json** 🌈
**Coming soon!**  
**Purpose:** Master color adjustment tools

**Features:**
- Levels Adjustment
- Auto Contrast
- Temperature & Tint
- Color Match/Transfer
- HSV Adjuster

**Perfect for:** Color grading mastery

---

## 📋 **WORKFLOW DIFFICULTY GUIDE**

| Level | Nodes | Time | Description |
|-------|-------|------|-------------|
| **Beginner** | 3-6 | <5s | Basic extraction, simple processing |
| **Intermediate** | 7-12 | 5-15s | Advanced techniques, multi-step |
| **Advanced** | 13+ | 15s+ | Complex pipelines, procedural |
| **Expert** | 20+ | 30s+ | Production workflows, full automation |

---

## 🎯 **WHICH WORKFLOW SHOULD I USE?**

**I want to...**

**→ Extract PBR from a photo quickly**  
Use: `10_fastest_pbr_extraction.json`

**→ Learn professional editing techniques**  
Use: `11_frequency_separation_workflow.json`

**→ Create materials without photos**  
Use: `12_procedural_material_creation.json`

**→ Blend two materials together**  
Use: `13_material_mixing_blending.json` (coming soon)

**→ Add realistic weathering**  
Use: `15_mask_generation_weathering.json` (coming soon)

**→ Create organic/special materials**  
Use: `14_advanced_materials_sss_anisotropy.json` (coming soon)

**→ Check texture quality**  
Use: `16_texture_analysis_qa.json` (coming soon)

**→ Learn blend modes**  
Use: `17_blend_modes_comparison.json` (coming soon)

**→ Understand procedural noise**  
Use: `18_noise_types_showcase.json` (coming soon)

**→ Master detail control**  
Use: `19_detail_control_showcase.json` (coming soon)

**→ Learn color grading**  
Use: `20_color_grading_showcase.json` (coming soon)

---

## 📝 **HOW TO USE THESE WORKFLOWS**

1. **Load the JSON file**
   - In ComfyUI: Menu → Load → Browse to `examples/` folder
   - Select the workflow JSON file
   
2. **Replace the input image**
   - Click on "Load Image" node
   - Choose your texture photo
   
3. **Adjust parameters**
   - Modify values to suit your texture
   - Hover over parameters for tooltips
   
4. **Queue Prompt**
   - Click "Queue Prompt" to run
   - Watch the magic happen!
   
5. **Check outputs**
   - Preview nodes show results
   - Saved files appear in output folder

---

## 💡 **WORKFLOW TIPS**

**Performance:**
- Start with lower resolution for testing
- Use Preview nodes to check intermediate steps
- GPU nodes are faster (most nodes)

**Organization:**
- Use Notes to document your workflows
- Group related nodes together
- Name nodes clearly

**Learning:**
- Start with simpler workflows
- Work up to complex ones
- Experiment with parameters!

**Troubleshooting:**
- Check console for errors
- Verify input image formats
- Ensure all connections are correct

---

## 🔄 **UPDATING WORKFLOWS**

These workflows are designed for **TextureAlchemy v3.0**.

If nodes are missing:
1. Make sure you've restarted ComfyUI
2. Check that all new .py files are loaded
3. Look in "Texture Alchemist" category

---

## 📦 **WORKFLOW PACKS**

**Beginner Pack:** (Ready!)
- 10_fastest_pbr_extraction.json ✅

**Pro Pack:** (Ready!)
- 11_frequency_separation_workflow.json ✅
- 12_procedural_material_creation.json ✅

**Complete Pack:** (In Progress)
- All 20 workflows
- Covers every technique
- Full documentation

---

## 🎊 **MORE WORKFLOWS COMING SOON!**

Stay tuned for:
- Game asset creation workflows
- Film/VFX workflows
- Stylized art workflows
- Batch processing workflows
- And more!

---

**Happy texture creating!** 🚀✨

For questions or custom workflow requests, check the main README.md!

