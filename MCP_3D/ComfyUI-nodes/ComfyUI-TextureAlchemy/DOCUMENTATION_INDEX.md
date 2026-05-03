# 📚 TextureAlchemy - Documentation Index

Complete guide to all documentation files.

---

## 📖 Documentation Files

### 1. **README.md** - Main Documentation
**Start here!** Complete reference for all 29 nodes.

**Contents:**
- Installation instructions
- Full node descriptions with parameters
- Example workflows (visual diagrams)
- Pro tips and best practices
- Technical details
- Version history

**Best for:** Learning nodes, reference lookup, understanding features

---

### 2. **WORKFLOWS.md** - Workflow Guide
Step-by-step workflows for common use cases.

**Contents:**
- 10 complete workflows (quick start to advanced)
- 5 testing workflows
- Benchmark results
- Workflow templates
- Best practices for different use cases

**Best for:** Following tutorials, learning workflow patterns, testing nodes

**Featured Workflows:**
- ⚡ Fastest PBR Extraction (3 nodes)
- 🎯 Complete PBR Material (7 maps)
- 🎨 Seamless Tile-able Material
- 🛠️ Material with Procedural Wear
- 📦 Channel-Packed ORM Texture
- 🔀 Material Mixing
- 🌈 Stylized/Artistic Materials
- 🔧 High-Detail Normals
- 🌐 Cross-Platform Export
- ⚙️ Generate Missing Maps

---

### 3. **QUICK_REFERENCE.md** - Quick Lookup
Fast reference for all nodes and parameters.

**Contents:**
- Node tables (category, I/O, key use)
- Parameter defaults (copy-paste ready)
- Common combinations
- Troubleshooting table
- Value ranges
- Performance tips
- Best practices cheat sheet

**Best for:** Quick lookups, troubleshooting, copy-paste parameters

**Print this!** Perfect desk reference.

---

### 4. **THIS FILE** - Documentation Index
You are here! Navigation guide for all docs.

---

## 🎯 How to Use This Documentation

### For Beginners:
1. **Start:** README.md (read "Quick Start" section)
2. **Follow:** WORKFLOWS.md ("Workflow 1: Fastest PBR Extraction")
3. **Learn:** Gradually explore more workflows
4. **Reference:** Keep QUICK_REFERENCE.md handy

### For Intermediate Users:
1. **Browse:** WORKFLOWS.md for advanced techniques
2. **Experiment:** Mix and match workflows
3. **Optimize:** Use performance tips in QUICK_REFERENCE.md
4. **Reference:** README.md for detailed parameters

### For Advanced Users:
1. **Quick lookup:** QUICK_REFERENCE.md for parameters
2. **Inspiration:** WORKFLOWS.md for advanced combinations
3. **Customize:** Create your own workflows
4. **Contribute:** Share your workflows!

---

## 🔍 Finding Information

### "How do I...?"

| Question | Document | Section |
|----------|----------|---------|
| Extract PBR from image? | README.md | PBR Extractor |
| Save complete material? | README.md | PBR Saver |
| Make texture tileable? | README.md | Seamless Tiling |
| Add wear/damage? | WORKFLOWS.md | Workflow 4 |
| Mix materials? | WORKFLOWS.md | Workflow 6 |
| Pack channels? | WORKFLOWS.md | Workflow 5 |
| Troubleshoot issues? | QUICK_REFERENCE.md | Troubleshooting |
| Find defaults? | QUICK_REFERENCE.md | Parameter Defaults |

### "What is...?"

| Question | Document | Section |
|----------|----------|---------|
| PBR_PIPE? | README.md | Technical Details |
| Color Ramp? | README.md | Color Utilities |
| ORM texture? | WORKFLOWS.md | Workflow 5 |
| Curvature map? | README.md | Curvature Generator |
| RNM blending? | README.md | Normal Map Combiner |
| Best format? | QUICK_REFERENCE.md | File Format Guide |

### "Why is my...?"

| Problem | Document | Section |
|---------|----------|---------|
| Roughness washed out? | QUICK_REFERENCE.md | Troubleshooting |
| Normals inverted? | QUICK_REFERENCE.md | Troubleshooting |
| Colors muted? | QUICK_REFERENCE.md | Troubleshooting |
| Texture not tiling? | README.md | Seamless Tiling |
| Node running slow? | QUICK_REFERENCE.md | Performance Tips |

---

## 📊 Documentation Stats

**Total Pages:** 4 documents  
**Total Words:** ~15,000+  
**Total Workflows:** 10 complete + 5 test workflows  
**Total Nodes Documented:** 26 nodes  
**Code Examples:** 50+ workflow snippets  
**Tips & Tricks:** 100+ tips  

---

## 🎓 Learning Path

### Day 1: Basics
- Read README.md intro
- Try Workflow 1 (Fastest PBR)
- Understand PBR_PIPE concept
- Save your first material

### Day 2: Complete Workflow
- Try Workflow 2 (Complete PBR)
- Add normals and height
- Use Pipeline Adjuster
- Experiment with parameters

### Day 3: Advanced Techniques
- Try Workflow 3 (Seamless Tiling)
- Try Workflow 4 (Wear & Damage)
- Understand curvature maps
- Create material variations

### Day 4: Optimization
- Try Workflow 5 (Channel Packing)
- Learn texture scaling
- Optimize for target platform
- Batch process materials

### Week 2: Mastery
- Try all 10 workflows
- Create custom workflows
- Mix and match techniques
- Contribute your workflows!

---

## 🔗 Quick Navigation

**Need to:**
- **Learn a node?** → README.md
- **Follow a tutorial?** → WORKFLOWS.md
- **Look up a parameter?** → QUICK_REFERENCE.md
- **Find a workflow?** → WORKFLOWS.md
- **Troubleshoot?** → QUICK_REFERENCE.md
- **Get inspired?** → WORKFLOWS.md (Advanced section)

---

## 📝 Documentation Conventions

### Symbols Used:
- ⭐ NEW - New in v2.0
- 💾 - Saves files
- 🎨 - Visual/interactive
- ⚡ - Fast/optimized
- 🔧 - Technical
- 🎯 - Recommended
- ⚠️ - Warning/important

### Node Names:
- **Bold** - Node name
- `code` - Parameter name
- "quotes" - Parameter value option
- → - Data flow / connection

### Example Format:
```
Node Name
├─ parameter: value
├─ parameter: value
└─ parameter: value
        ↓
   Next Node
```

---

## 🎯 Common Workflows (Quick Access)

1. **Extract PBR (Fast):** Load → Marigold x2 → PBR Extractor → PBR Saver
2. **Add Normals:** PBR Pipe → PBR Combiner + Lotus Normal → PBR Saver
3. **Tile Texture:** Load → Seamless Tiling → [Extract PBR]
4. **Add Wear:** PBR Pipe → Curvature + Wear Generator → PBR Combiner
5. **Pack ORM:** PBR Splitter → Channel Packer → Save
6. **Mix Materials:** 2x PBR Pipes → Material Mixer → PBR Saver
7. **Color Variations:** PBR Pipe → HSV Adjuster → PBR Combiner
8. **Stylize:** Height → Gradient Map → Color Ramp → PBR Combiner

---

## 💡 Pro Tips Collection

### Must-Read Tips:
1. **Use Pipeline System** - Cleaner workflows (README.md)
2. **Preview Before Saving** - PBR Pipe Preview (WORKFLOWS.md)
3. **Pack Channels for Games** - ORM format (WORKFLOWS.md #5)
4. **Interactive Color Ramp** - Click/drag/double-click (README.md)
5. **Increase gamma_appearance** - If washed out (QUICK_REFERENCE.md)
6. **Use EXR for Precision** - Normals/height (QUICK_REFERENCE.md)
7. **Seamless First** - Apply before extraction (WORKFLOWS.md #3)
8. **Curvature for Wear** - Realistic weathering (WORKFLOWS.md #4)
9. **HSV Not RGB** - Better color control (README.md)
10. **Batch Process** - Enumerate mode (README.md, PBR Saver)

---

## 🆘 Getting Help

### 1. Check Documentation
- **Workflow issue?** → WORKFLOWS.md
- **Node confusion?** → README.md
- **Parameter values?** → QUICK_REFERENCE.md
- **Troubleshooting?** → QUICK_REFERENCE.md

### 2. Search Documentation
Use Ctrl+F to search for:
- Node name
- Error message
- Parameter name
- Technique (e.g., "seamless", "wear", "mix")

### 3. Example Workflow
Find similar workflow in WORKFLOWS.md and adapt it.

### 4. Test Workflow
Run appropriate test from WORKFLOWS.md "Testing Workflows" section.

---

## 🔄 Keeping Updated

**Documentation Version:** 2.0  
**Last Updated:** December 2024  
**Nodes Documented:** 26 nodes  
**Workflows Included:** 15 complete workflows  

**What's New in v2.0:**
- ⭐ 13 new nodes documented
- 🎨 Interactive Color Ramp guide
- 🛠️ 10 new workflows
- 📊 Performance benchmarks
- 🎯 Expanded troubleshooting
- 💡 100+ pro tips

---

## 📖 Reading Order Recommendations

### First Time Users:
1. README.md (Quick Start section)
2. WORKFLOWS.md (Workflow 1)
3. QUICK_REFERENCE.md (browse)

### Learning All Features:
1. README.md (all nodes)
2. WORKFLOWS.md (all workflows)
3. QUICK_REFERENCE.md (memorize common values)

### Production Work:
1. WORKFLOWS.md (find template)
2. QUICK_REFERENCE.md (lookup parameters)
3. README.md (detailed reference if needed)

### Teaching Others:
1. README.md (overview)
2. WORKFLOWS.md (step-by-step)
3. QUICK_REFERENCE.md (cheat sheet)

---

## 🎉 You're All Set!

**You now have:**
✅ Complete node reference (README.md)  
✅ Step-by-step workflows (WORKFLOWS.md)  
✅ Quick reference guide (QUICK_REFERENCE.md)  
✅ This navigation guide (DOCUMENTATION_INDEX.md)

**Start creating amazing PBR materials!** 🚀

---

**Questions? Check the docs → Can't find it? It's probably in QUICK_REFERENCE.md → Still stuck? Review similar workflow in WORKFLOWS.md**

**Happy texturing!** 🎨

