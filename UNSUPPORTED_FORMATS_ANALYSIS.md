# FileConverter - Unsupported Formats Analysis

## Current Support Summary

### ✅ Currently Supported (27 formats)
- **Images (8)**: png, jpg, jpeg, webp, gif, bmp, tiff, ico
- **Videos (7)**: mp4, avi, mov, mkv, webm, flv, wmv
- **Audio (7)**: mp3, wav, flac, aac, ogg, m4a, wma
- **Documents (5)**: txt, pdf, docx, md, html, rtf

---

# PART 1: Missing Formats in Existing Categories

## 📸 IMAGE FORMATS (Not Currently Supported)

### High Priority - Common Formats

#### **SVG (Scalable Vector Graphics)**
- **Purpose**: Vector graphics, logos, icons, web graphics
- **Use Cases**: Web design, print materials, scalable graphics
- **Why Important**: Only vector format, infinitely scalable without quality loss
- **Complexity**: **MEDIUM**
  - Tool: ImageMagick or CairoSVG (Python)
  - Challenge: Rasterization (SVG→PNG/JPG) is easy, vectorization (PNG→SVG) is very hard
  - Size: Small library footprint
- **User Demand**: **HIGH** (very commonly requested)

#### **PSD (Adobe Photoshop Document)**
- **Purpose**: Professional photo editing with layers
- **Use Cases**: Graphic design, photo manipulation, print media
- **Why Important**: Industry standard for designers
- **Complexity**: **VERY HIGH**
  - Tool: Would need psd-tools (Python) or ImageMagick (limited support)
  - Challenge: Preserving layers is complex; flattening is easier
  - Size: PSD files can be huge (100s of MB)
  - Limitation: Can only flatten to raster formats, not full PSD manipulation
- **User Demand**: **MEDIUM-HIGH** (professional users)

#### **HEIC/HEIF (High Efficiency Image Format)**
- **Purpose**: Modern iPhone default format, better compression than JPEG
- **Use Cases**: Mobile photography, space-efficient storage
- **Why Important**: Becoming standard on Apple devices
- **Complexity**: **MEDIUM**
  - Tool: pillow-heif (Python) or FFmpeg with libheif
  - Challenge: Requires libheif system library
  - Size: ~2-5 MB library addition
  - Compatibility: Patent issues in some regions
- **User Demand**: **VERY HIGH** (iPhone users constantly need this)

#### **AVIF (AV1 Image File Format)**
- **Purpose**: Next-gen image format, better compression than WebP
- **Use Cases**: Web optimization, modern websites
- **Why Important**: Emerging web standard, supported by all major browsers
- **Complexity**: **MEDIUM**
  - Tool: pillow-avif or FFmpeg
  - Challenge: Requires libavif
  - Size: ~3-5 MB
- **User Demand**: **MEDIUM** (growing rapidly)

#### **RAW Formats (CR2, NEF, ARW, DNG, etc.)**
- **Purpose**: Unprocessed camera sensor data for professional photography
- **Use Cases**: Professional photography, maximum editing flexibility
- **Why Important**: Photographers need to convert RAW to usable formats
- **Complexity**: **HIGH**
  - Tool: rawpy (Python wrapper for LibRaw) or dcraw
  - Challenge: Each camera brand has different RAW format
  - Size: Large library (~10-20 MB), many camera profiles needed
  - Processing: CPU-intensive demosaicing
- **User Demand**: **HIGH** (professional photographers)

### Medium Priority - Specialized Formats

#### **EPS (Encapsulated PostScript)**
- **Purpose**: Vector graphics for print, older Adobe format
- **Use Cases**: Print media, legacy documents
- **Complexity**: **HIGH** (requires Ghostscript)
- **User Demand**: **LOW** (legacy format, being replaced by PDF/SVG)

#### **TGA (Truevision Targa)**
- **Purpose**: Gaming textures, video editing
- **Use Cases**: 3D modeling, game development
- **Complexity**: **EASY** (Pillow supports it)
- **User Demand**: **LOW** (niche use case)

#### **DDS (DirectDraw Surface)**
- **Purpose**: Game textures with mipmaps
- **Use Cases**: Game development, 3D graphics
- **Complexity**: **MEDIUM** (needs special library)
- **User Demand**: **LOW** (very niche)

---

## 🎬 VIDEO FORMATS (Not Currently Supported)

### High Priority

#### **M4V (iTunes Video)**
- **Purpose**: Apple's MPEG-4 container, similar to MP4
- **Use Cases**: iTunes purchases, Apple ecosystem
- **Complexity**: **EASY** (FFmpeg already supports it)
- **User Demand**: **MEDIUM** (Apple users)

#### **3GP/3G2 (Mobile Video)**
- **Purpose**: Old mobile phone video format
- **Use Cases**: Legacy mobile devices, WhatsApp videos
- **Complexity**: **EASY** (FFmpeg supports it)
- **User Demand**: **MEDIUM** (still used in some regions)

#### **VOB (DVD Video Object)**
- **Purpose**: DVD video files
- **Use Cases**: Ripping DVDs, preserving old media
- **Complexity**: **MEDIUM** (FFmpeg supports, but may have DRM issues)
- **User Demand**: **MEDIUM** (legacy media)

#### **MTS/M2TS (AVCHD)**
- **Purpose**: HD camcorder format (Sony, Panasonic)
- **Use Cases**: Camcorder footage
- **Complexity**: **EASY** (FFmpeg supports it)
- **User Demand**: **MEDIUM** (camcorder users)

#### **OGV (Ogg Video)**
- **Purpose**: Open-source video format
- **Use Cases**: Web, open-source projects
- **Complexity**: **EASY** (FFmpeg supports it)
- **User Demand**: **LOW-MEDIUM** (open-source advocates)

### Medium Priority

#### **MPG/MPEG (MPEG-1/2)**
- **Purpose**: Older video standard, DVDs, VCDs
- **Use Cases**: Legacy video files
- **Complexity**: **EASY** (FFmpeg supports it)
- **User Demand**: **LOW** (legacy format)

#### **RM/RMVB (RealMedia)**
- **Purpose**: Old streaming format (RealPlayer)
- **Use Cases**: Old Asian media files
- **Complexity**: **MEDIUM** (FFmpeg support varies)
- **User Demand**: **LOW** (legacy, mostly obsolete)

---

## 🎵 AUDIO FORMATS (Not Currently Supported)

### High Priority

#### **OPUS (Opus Audio Codec)**
- **Purpose**: Modern, efficient codec for voice and music
- **Use Cases**: VoIP, podcasts, streaming
- **Why Important**: Best quality-to-bitrate ratio, used by Discord, WhatsApp
- **Complexity**: **EASY** (FFmpeg supports it natively)
- **User Demand**: **HIGH** (modern web standard)

#### **ALAC (Apple Lossless)**
- **Purpose**: Lossless compression for Apple ecosystem
- **Use Cases**: iTunes, Apple Music, audiophiles
- **Complexity**: **EASY** (FFmpeg supports it)
- **User Demand**: **MEDIUM-HIGH** (Apple users)

#### **APE (Monkey's Audio)**
- **Purpose**: Lossless compression, popular in Asia
- **Use Cases**: Archiving music, audiophile collections
- **Complexity**: **EASY** (FFmpeg supports it)
- **User Demand**: **MEDIUM** (audiophiles)

#### **DSD (Direct Stream Digital)**
- **Purpose**: Super high-quality audio (SACD)
- **Use Cases**: Ultra-high-end audiophile music
- **Complexity**: **HIGH** (special handling, large files)
- **User Demand**: **LOW** (extreme niche)

### Medium Priority

#### **MID/MIDI (Musical Instrument Digital Interface)**
- **Purpose**: Music notation, synthesizer instructions
- **Use Cases**: Music composition, karaoke
- **Complexity**: **VERY HIGH**
  - Not actual audio, but instructions
  - Converting to audio requires soundfonts
  - Converting from audio to MIDI is AI-level complex
- **User Demand**: **LOW** (very specialized)

#### **WV (WavPack)**
- **Purpose**: Lossless/lossy compression
- **Use Cases**: Audio archiving
- **Complexity**: **EASY** (FFmpeg supports it)
- **User Demand**: **LOW** (niche format)

#### **AMR (Adaptive Multi-Rate)**
- **Purpose**: Mobile voice recording
- **Use Cases**: Voice memos, old phone recordings
- **Complexity**: **EASY** (FFmpeg supports it)
- **User Demand**: **LOW-MEDIUM** (mobile users)

---

## 📄 DOCUMENT FORMATS (Not Currently Supported)

### High Priority

#### **EPUB (Electronic Publication)**
- **Purpose**: eBooks for e-readers
- **Use Cases**: Digital books, e-reader devices
- **Why Important**: Standard eBook format
- **Complexity**: **MEDIUM**
  - Tool: ebooklib (Python) or Calibre CLI
  - Challenge: Structured format with metadata, images, styles
  - Size: ~5 MB for Calibre
- **User Demand**: **HIGH** (eBook readers, authors)

#### **MOBI/AZW (Kindle Format)**
- **Purpose**: Amazon Kindle eBooks
- **Use Cases**: Kindle devices
- **Complexity**: **MEDIUM-HIGH**
  - Tool: Calibre (Amazon's format is proprietary)
  - Challenge: DRM on purchased books
- **User Demand**: **HIGH** (Kindle users)

#### **ODT (OpenDocument Text)**
- **Purpose**: LibreOffice/OpenOffice documents
- **Use Cases**: Open-source office suites
- **Complexity**: **MEDIUM** (Pandoc supports it)
- **User Demand**: **MEDIUM** (LibreOffice users)

#### **XLS/XLSX (Excel Spreadsheets)**
- **Purpose**: Spreadsheets, data tables
- **Use Cases**: Business, data analysis
- **Complexity**: **HIGH**
  - Tool: openpyxl (Python) or LibreOffice CLI
  - Challenge: Formulas, charts, macros are complex
  - Realistic: Can convert to CSV/PDF, not to other spreadsheet formats
- **User Demand**: **VERY HIGH** (extremely common request)

#### **PPT/PPTX (PowerPoint)**
- **Purpose**: Presentations
- **Use Cases**: Business, education
- **Complexity**: **VERY HIGH**
  - Tool: python-pptx or LibreOffice CLI
  - Challenge: Animations, transitions, embedded media
  - Realistic: Can convert to PDF/images, not to other presentation formats
- **User Demand**: **HIGH** (business users)

#### **LaTeX (.tex)**
- **Purpose**: Scientific/academic document typesetting
- **Use Cases**: Research papers, academic writing, math-heavy docs
- **Complexity**: **MEDIUM**
  - Tool: Pandoc supports LaTeX ↔ other formats
  - Challenge: Compiling .tex to PDF requires full LaTeX installation (~1-2 GB)
- **User Demand**: **MEDIUM** (academic users)

### Medium Priority

#### **CSV (Comma-Separated Values)**
- **Purpose**: Tabular data
- **Use Cases**: Data exchange, spreadsheets
- **Complexity**: **EASY** (Python built-in)
- **User Demand**: **HIGH** (extremely common)
- **Note**: Could be part of data category

#### **XML/JSON (Data Formats)**
- **Purpose**: Structured data
- **Use Cases**: Data exchange, APIs
- **Complexity**: **EASY** (Python built-in)
- **User Demand**: **MEDIUM** (developers)

#### **TEX (Plain TeX)**
- **Purpose**: Lower-level typesetting than LaTeX
- **Use Cases**: Academic, specialized publishing
- **Complexity**: **HIGH** (requires TeX distribution)
- **User Demand**: **LOW** (very niche)

---

# PART 2: New Categories to Add

## 📊 SPREADSHEETS & DATA (NEW CATEGORY)

### Formats
- **XLSX** (Excel) - VERY HIGH demand
- **XLS** (Old Excel) - HIGH demand
- **ODS** (OpenDocument Spreadsheet) - MEDIUM demand
- **CSV** (Comma-Separated Values) - VERY HIGH demand
- **TSV** (Tab-Separated Values) - MEDIUM demand
- **Numbers** (Apple Numbers) - LOW demand

### Tools Needed
- **openpyxl** (Python) - Read/write Excel
- **pandas** (Python) - Data manipulation
- **LibreOffice CLI** (headless) - Complex conversions
- **Size**: ~20-50 MB (openpyxl + pandas + dependencies)

### Realistic Capabilities
✅ **Can Do**:
- Excel ↔ CSV/TSV (easy)
- Excel → PDF (with LibreOffice)
- CSV ↔ JSON/XML (easy)
- Basic spreadsheet ↔ spreadsheet (losing formulas)

❌ **Cannot Do Well**:
- Preserve Excel formulas in other formats
- Convert charts/graphs
- Maintain macros/VBA code
- Complex formatting

### Complexity: **MEDIUM-HIGH**
### User Demand: **VERY HIGH**

---

## 📦 ARCHIVES & COMPRESSION (NEW CATEGORY)

### Formats
- **ZIP** - VERY HIGH demand
- **RAR** - HIGH demand (read-only due to proprietary format)
- **7Z** - MEDIUM demand
- **TAR.GZ** - MEDIUM demand (Linux users)
- **TAR.BZ2** - LOW demand
- **GZ** (single file) - MEDIUM demand

### Tools Needed
- **zipfile** (Python built-in)
- **py7zr** (Python) - 7-Zip
- **rarfile** (Python) - RAR reading (requires unrar binary)
- **tarfile** (Python built-in)
- **Size**: ~5-10 MB

### Operations
- Compress files/folders into archive
- Extract archives
- Convert between archive formats (extract + recompress)
- List archive contents
- Add/remove files from archives

### Complexity: **EASY-MEDIUM**
### User Demand: **VERY HIGH**

---

## 📐 CAD & 3D MODELS (NEW CATEGORY)

### Formats
- **STL** (3D printing) - HIGH demand
- **OBJ** (3D models) - MEDIUM demand
- **FBX** (Game assets) - LOW demand
- **GLTF/GLB** (Web 3D) - MEDIUM demand
- **DWG** (AutoCAD) - MEDIUM demand (proprietary, hard)
- **DXF** (AutoCAD Exchange) - MEDIUM demand
- **PLY** (3D scans) - LOW demand
- **COLLADA** (.dae) - LOW demand

### Tools Needed
- **trimesh** (Python) - 3D mesh processing
- **Open3D** (Python) - Point cloud/mesh processing
- **assimp** - Asset import library
- **Size**: ~50-100 MB (heavy dependencies)

### Realistic Capabilities
✅ **Can Do**:
- STL ↔ OBJ ↔ PLY (mesh formats)
- Basic geometry conversion
- Mesh optimization (reduce polygons)
- Export preview images

❌ **Cannot Do Well**:
- CAD ↔ Mesh (loses parametric data)
- Preserve materials/textures perfectly
- Convert animations
- DWG support (proprietary, complex)

### Complexity: **VERY HIGH**
### User Demand: **MEDIUM** (3D printing enthusiasts, game devs)

---

## 🖼️ EBOOKS (NEW CATEGORY)

### Formats
- **EPUB** - VERY HIGH demand
- **MOBI** (Kindle) - HIGH demand
- **AZW3** (Kindle) - HIGH demand
- **PDF** (already have) - VERY HIGH demand
- **FB2** (FictionBook) - LOW demand
- **LIT** (Microsoft Reader) - VERY LOW demand (obsolete)

### Tools Needed
- **ebooklib** (Python) - EPUB manipulation
- **Calibre CLI** - Best eBook converter
- **Size**: ~30-80 MB (Calibre is large)

### Operations
- Convert between eBook formats
- Extract text/images from eBooks
- Reflow text (change font size)
- Convert documents → eBook

### Complexity: **MEDIUM**
### User Demand: **VERY HIGH**

---

## 🎨 FONTS (NEW CATEGORY)

### Formats
- **TTF** (TrueType) - HIGH demand
- **OTF** (OpenType) - HIGH demand
- **WOFF/WOFF2** (Web fonts) - MEDIUM demand
- **EOT** (Embedded OpenType) - LOW demand (obsolete)

### Tools Needed
- **fonttools** (Python)
- **woff2** (Google library)
- **Size**: ~10-20 MB

### Operations
- Convert font formats (TTF ↔ OTF ↔ WOFF)
- Subset fonts (remove unused characters)
- Extract font information

### Complexity: **MEDIUM**
### User Demand: **LOW-MEDIUM** (web developers, designers)

---

## 🗜️ SUBTITLE FILES (NEW CATEGORY)

### Formats
- **SRT** (SubRip) - VERY HIGH demand
- **ASS/SSA** (Advanced SubStation) - MEDIUM demand
- **VTT** (WebVTT) - MEDIUM demand
- **SUB** (MicroDVD) - LOW demand

### Tools Needed
- **pysrt** (Python)
- **webvtt-py** (Python)
- **Size**: <1 MB (very lightweight)

### Operations
- Convert subtitle formats
- Adjust timing (shift subtitles)
- Merge/split subtitles
- Burn subtitles into video (with FFmpeg)

### Complexity: **EASY**
### User Demand: **MEDIUM** (video editors, translators)

---

## 💾 DATABASE EXPORTS (NEW CATEGORY)

### Formats
- **SQL** (SQL dump)
- **JSON** (database export)
- **XML** (database export)
- **CSV** (table export)

### Tools Needed
- Built-in Python libraries
- **Size**: <5 MB

### Operations
- Convert between data export formats
- Transform JSON ↔ CSV ↔ XML
- Simple schema conversions

### Complexity: **EASY-MEDIUM**
### User Demand: **MEDIUM** (developers, data analysts)

---

## 📧 EMAIL FORMATS (NEW CATEGORY)

### Formats
- **EML** (Email message)
- **MSG** (Outlook message)
- **MBOX** (Unix mailbox)
- **PST** (Outlook data file) - Very complex

### Tools Needed
- **email** (Python built-in) - EML
- **extract-msg** (Python) - MSG
- **mailbox** (Python built-in) - MBOX
- **Size**: ~5-10 MB

### Operations
- Extract email content
- Convert email formats
- Extract attachments
- Export to PDF/TXT

### Complexity: **MEDIUM**
### User Demand**: **LOW-MEDIUM** (email archiving)

---

# PART 3: Priority Recommendations

## 🎯 Top 5 MUST-ADD Formats (Individual)

1. **HEIC/HEIF** (Image)
   - Demand: ⭐⭐⭐⭐⭐ (iPhone users need this constantly)
   - Complexity: ⭐⭐⭐ (Medium)
   - Impact: Massive user base
   - Estimated Time: 4-6 hours

2. **SVG** (Image)
   - Demand: ⭐⭐⭐⭐⭐ (Web designers, everyone)
   - Complexity: ⭐⭐⭐ (Medium, rasterization only)
   - Impact: Very high
   - Estimated Time: 3-5 hours

3. **EPUB** (eBook)
   - Demand: ⭐⭐⭐⭐ (Readers, authors)
   - Complexity: ⭐⭐⭐ (Medium)
   - Impact: New category, broad appeal
   - Estimated Time: 6-8 hours

4. **OPUS** (Audio)
   - Demand: ⭐⭐⭐⭐ (Modern web standard)
   - Complexity: ⭐ (Easy, FFmpeg already has it)
   - Impact: Modern users
   - Estimated Time: 1-2 hours

5. **RAW Formats** (Image)
   - Demand: ⭐⭐⭐⭐ (Photographers)
   - Complexity: ⭐⭐⭐⭐ (High)
   - Impact: Professional users
   - Estimated Time: 8-12 hours

## 🎯 Top 3 MUST-ADD Categories

1. **ARCHIVES & COMPRESSION**
   - Demand: ⭐⭐⭐⭐⭐ (Everyone needs this)
   - Complexity: ⭐⭐ (Easy-Medium)
   - Impact: Massive, universal appeal
   - Estimated Time: 10-15 hours
   - **HIGHEST PRIORITY**

2. **SPREADSHEETS & DATA**
   - Demand: ⭐⭐⭐⭐⭐ (Business users, very common)
   - Complexity: ⭐⭐⭐⭐ (Medium-High)
   - Impact: Huge business use case
   - Estimated Time: 15-20 hours

3. **EBOOKS**
   - Demand: ⭐⭐⭐⭐ (Readers, authors, publishers)
   - Complexity: ⭐⭐⭐ (Medium)
   - Impact: Large user base
   - Estimated Time: 12-18 hours

## ⚡ Quick Wins (Easy to Add)

1. **OPUS** (Audio) - 1-2 hours
2. **M4V** (Video) - 1 hour
3. **3GP** (Video) - 1 hour
4. **CSV** (Data) - 2 hours
5. **SRT** (Subtitles) - 3-4 hours

---

# PART 4: Implementation Complexity Matrix

## Complexity Tiers

### 🟢 EASY (1-3 hours each)
- Already supported by FFmpeg or Pillow
- Minimal code changes
- Examples: OPUS, M4V, 3GP, TGA, CSV (basic)

### 🟡 MEDIUM (4-8 hours each)
- Requires new library but straightforward
- Some complexity in format handling
- Examples: HEIC, SVG (raster only), EPUB, Archives (ZIP/7Z)

### 🟠 MEDIUM-HIGH (8-15 hours each)
- Complex libraries or multiple tools needed
- Format has many edge cases
- Examples: Spreadsheets (XLSX), eBooks (with metadata), RAW images

### 🔴 HIGH (15-30 hours each)
- Very complex libraries
- Many edge cases and limitations
- May require external binaries
- Examples: PSD (full support), CAD formats, Office formats (full fidelity)

### ⚫ VERY HIGH (30+ hours each)
- Extremely complex or incomplete tooling
- Many unsupported features
- May be impractical
- Examples: Full PPT conversion, DWG, MIDI synthesis, 3D with textures/animations

---

# PART 5: Estimated Bundle Size Impact

| Category | Additional Size | Justification |
|----------|----------------|---------------|
| **HEIC Support** | +3-5 MB | libheif library |
| **SVG Support** | +2-3 MB | CairoSVG or librsvg |
| **RAW Support** | +15-20 MB | LibRaw + camera profiles |
| **Archive Support** | +5-10 MB | 7z, RAR libraries |
| **Spreadsheet Support** | +20-30 MB | openpyxl, pandas |
| **eBook Support** | +30-50 MB | Calibre (large but powerful) |
| **3D Model Support** | +50-100 MB | trimesh, Open3D, heavy dependencies |
| **Font Support** | +10-15 MB | fonttools, WOFF2 |

**Current installer size**: ~620 MB per platform
**With all high-priority additions**: ~700-750 MB per platform (+12-20%)

---

# PART 6: Feature Completeness by Category

## Current Categories

### Images
- **Completeness**: 70%
- **Major Gaps**: HEIC (critical), SVG (critical), PSD, RAW
- **Assessment**: Missing modern formats (HEIC) and professional formats (RAW, PSD)

### Videos
- **Completeness**: 85%
- **Major Gaps**: M4V, 3GP (minor), VOB (legacy)
- **Assessment**: Pretty complete for common use

### Audio
- **Completeness**: 80%
- **Major Gaps**: OPUS (important), ALAC (Apple users)
- **Assessment**: Missing modern codec (OPUS)

### Documents
- **Completeness**: 60%
- **Major Gaps**: EPUB, ODT, Office formats (critical)
- **Assessment**: Limited to basic text formats

---

# SUMMARY & RECOMMENDATIONS

## Immediate Actions (Within 1 Week)

1. **Add HEIC support** - Critical for iPhone users
2. **Add OPUS audio** - Modern web standard, trivial to add
3. **Add M4V, 3GP video** - Quick wins
4. **Add SVG support** (rasterization) - High demand

**Total Time**: ~10-15 hours
**Impact**: Covers 80% of common user requests

## Phase 2 (Within 1 Month)

5. **Add Archive/Compression category** - Universal need
6. **Add EPUB/MOBI support** - eBook readers
7. **Add CSV/basic spreadsheet** - Data users
8. **Add RAW image support** - Photographers

**Total Time**: ~30-40 hours
**Impact**: Transforms app into comprehensive conversion tool

## Phase 3 (Future Consideration)

9. **Full spreadsheet support (XLSX)** - Business users
10. **CAD/3D models** - Specialized users
11. **Subtitle files** - Video editors
12. **Font conversion** - Designers

## Don't Bother With

- ❌ Full PSD support (too complex, limited benefit)
- ❌ Full Office suite (PPT, Word with macros) - too complex
- ❌ DWG (proprietary, very difficult)
- ❌ MIDI synthesis (impractical)
- ❌ Legacy formats (EPS, RM, LIT)

---

## User Impact Analysis

| Format/Category | User Count Estimate | Conversion Frequency |
|----------------|---------------------|---------------------|
| HEIC | ⭐⭐⭐⭐⭐ Millions | Daily (iPhone photos) |
| Archives | ⭐⭐⭐⭐⭐ Millions | Weekly |
| SVG | ⭐⭐⭐⭐ Hundreds of thousands | Weekly |
| EPUB | ⭐⭐⭐⭐ Hundreds of thousands | Monthly |
| Spreadsheets | ⭐⭐⭐⭐⭐ Millions | Weekly |
| OPUS | ⭐⭐⭐ Tens of thousands | Monthly |
| RAW | ⭐⭐⭐ Tens of thousands | Daily (photographers) |
| 3D Models | ⭐⭐ Thousands | Weekly (makers) |
| Subtitles | ⭐⭐ Thousands | Weekly (video editors) |

**Conclusion**: Focus on HEIC, Archives, SVG, and Spreadsheets for maximum user impact.
