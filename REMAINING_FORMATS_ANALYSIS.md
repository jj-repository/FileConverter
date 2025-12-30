# FileConverter - Remaining Unsupported Formats Analysis (Updated)

> **Last Updated**: December 2024
> **Current Status**: 52 formats supported across 7 categories
> **Completed Phases**: Phase 1 (Quick Wins), Phase 2 (Archives), Phase 3 (Spreadsheets)

---

## ✅ What We've Already Implemented

### Completed Categories:
- **Images**: 11 formats (png, jpg, jpeg, webp, gif, bmp, tiff, ico, heic, heif, svg)
- **Videos**: 10 formats (mp4, avi, mov, mkv, webm, flv, wmv, m4v, 3gp, 3g2)
- **Audio**: 9 formats (mp3, wav, flac, aac, ogg, m4a, wma, opus, alac)
- **Documents**: 6 formats (txt, pdf, docx, md, html, rtf)
- **Data**: 3 formats (csv, json, xml)
- **Archives**: 8 formats (zip, tar, tar.gz, tgz, tar.bz2, tbz2, gz, 7z) ✨ NEW
- **Spreadsheets**: 5 formats (xlsx, xls-read, ods, csv, tsv) ✨ NEW

**Total**: 52 formats supported

---

# PART 1: Missing Formats in Existing Categories

## 🖼️ IMAGE FORMATS (Still Missing)

### High Priority

#### **RAW Image Formats (Camera RAW)**
- **Formats**: CR2 (Canon), NEF (Nikon), ARW (Sony), DNG (Adobe)
- **Purpose**: Professional photography, unprocessed camera data
- **Use Cases**: Photographers, photo editing workflows
- **Why Important**: Photographers need to convert RAW to usable formats
- **Complexity**: **HIGH**
  - Tool: rawpy (Python wrapper for LibRaw) or Pillow with plugin
  - Challenge: Each camera manufacturer has proprietary format
  - Limited conversion: RAW → JPEG/PNG only (can't create RAW)
  - Size: Large files, ~20-50 MB each
- **User Demand**: **HIGH** (professional photographers)
- **Bundle Impact**: +15-25 MB (LibRaw library)

#### **AVIF (AV1 Image Format)**
- **Purpose**: Next-gen image format, better compression than WebP
- **Use Cases**: Modern web, high-quality images with small file size
- **Why Important**: Gaining adoption, Chrome/Firefox support
- **Complexity**: **MEDIUM**
  - Tool: pillow-avif plugin
  - Challenge: Newer format, some compatibility issues
  - Size: ~5-10 MB
- **User Demand**: **MEDIUM-HIGH** (web developers, early adopters)
- **Bundle Impact**: +5-10 MB

#### **WebP2**
- **Purpose**: Successor to WebP with better compression
- **Use Cases**: Future web standard
- **Complexity**: **LOW-MEDIUM** (once standardized)
- **User Demand**: **LOW** (still experimental)

### Medium Priority

#### **TGA (Targa)**
- **Purpose**: Legacy image format, used in gaming/video
- **Use Cases**: Game development, video production
- **Complexity**: **EASY** (Pillow supports it)
- **User Demand**: **LOW-MEDIUM** (niche gaming/video)
- **Bundle Impact**: Already supported by Pillow (0 MB)

#### **PCX (PC Paintbrush)**
- **Purpose**: Very old DOS-era format
- **Complexity**: **EASY** (Pillow supports it)
- **User Demand**: **VERY LOW** (legacy only)

#### **PSD (Photoshop)**
- **Purpose**: Adobe Photoshop native format
- **Use Cases**: Professional image editing
- **Complexity**: **VERY HIGH**
  - Tool: psd-tools (Python)
  - Challenge: Layers, effects, complex structure
  - Realistic: Can only flatten to PNG/JPEG, can't preserve layers
- **User Demand**: **MEDIUM** (designers)
- **Bundle Impact**: +10-20 MB

---

## 🎥 VIDEO FORMATS (Still Missing)

### High Priority

#### **MTS/M2TS (AVCHD)**
- **Purpose**: Camcorder format (HD video)
- **Use Cases**: Consumer camcorders, video cameras
- **Why Important**: Common for home videos
- **Complexity**: **EASY-MEDIUM** (FFmpeg supports it)
- **User Demand**: **MEDIUM-HIGH** (consumer video)
- **Bundle Impact**: 0 MB (FFmpeg already included)

#### **VOB (DVD Video)**
- **Purpose**: DVD video files
- **Use Cases**: DVD ripping, archiving
- **Complexity**: **EASY** (FFmpeg supports it)
- **User Demand**: **MEDIUM** (DVD archiving)
- **Bundle Impact**: 0 MB (FFmpeg already included)

#### **TS (Transport Stream)**
- **Purpose**: TV broadcasts, streaming
- **Use Cases**: DVR recordings, TV capture
- **Complexity**: **EASY** (FFmpeg supports it)
- **User Demand**: **MEDIUM** (TV recording)
- **Bundle Impact**: 0 MB (FFmpeg already included)

### Medium Priority

#### **OGV (Ogg Video)**
- **Purpose**: Open-source video container
- **Complexity**: **EASY** (FFmpeg supports it)
- **User Demand**: **LOW** (rarely used)
- **Bundle Impact**: 0 MB

#### **F4V/FLV (Flash Video)**
- **Purpose**: Legacy Flash video
- **Complexity**: **EASY** (FFmpeg supports FLV)
- **User Demand**: **LOW** (Flash is dead)
- **Note**: FLV already supported

---

## 🎵 AUDIO FORMATS (Still Missing)

### High Priority

#### **APE (Monkey's Audio)**
- **Purpose**: Lossless audio compression
- **Use Cases**: Audiophile music collections
- **Complexity**: **MEDIUM** (FFmpeg supports it with libavcodec)
- **User Demand**: **MEDIUM** (audiophiles)
- **Bundle Impact**: 0 MB (FFmpeg already included)

#### **DSD (Direct Stream Digital)**
- **Purpose**: Super high-quality audio (SACD)
- **Use Cases**: Audiophile, professional audio
- **Complexity**: **HIGH** (specialized format, limited tools)
- **User Demand**: **LOW-MEDIUM** (very niche audiophiles)

### Medium Priority

#### **MIDI**
- **Purpose**: Musical instrument digital interface
- **Use Cases**: Music production, synthesizers
- **Complexity**: **HIGH**
  - Challenge: MIDI is instructions, not audio (needs synthesis)
  - Can't convert MIDI → MP3 without synthesizer
  - Can convert audio → MIDI but results are poor
- **User Demand**: **LOW-MEDIUM** (music producers)

#### **MKA (Matroska Audio)**
- **Purpose**: Audio container format
- **Complexity**: **EASY** (FFmpeg supports it)
- **User Demand**: **LOW** (uncommon)
- **Bundle Impact**: 0 MB

---

## 📄 DOCUMENT FORMATS (Still Missing)

### High Priority

#### **EPUB (Electronic Publication)**
- **Purpose**: eBooks for e-readers
- **Use Cases**: Digital books, Kindle alternatives, e-reader devices
- **Why Important**: Standard eBook format
- **Complexity**: **MEDIUM**
  - Tool: ebooklib (Python) or Calibre CLI
  - Challenge: Structured format with metadata, images, styles
  - Realistic: EPUB ↔ PDF, EPUB ↔ TXT, EPUB ↔ HTML
- **User Demand**: **VERY HIGH** (eBook readers, authors, publishers)
- **Bundle Impact**: +5-10 MB (ebooklib) or +30-80 MB (Calibre)

#### **MOBI/AZW (Kindle Format)**
- **Purpose**: Amazon Kindle eBooks
- **Use Cases**: Kindle devices
- **Complexity**: **MEDIUM-HIGH**
  - Tool: Calibre (Amazon's format is proprietary)
  - Challenge: DRM on purchased books (can't convert)
  - Realistic: Only non-DRM books
- **User Demand**: **HIGH** (Kindle users)
- **Bundle Impact**: +30-80 MB (Calibre required)

#### **ODT (OpenDocument Text)**
- **Purpose**: LibreOffice/OpenOffice documents
- **Use Cases**: Open-source office suites
- **Complexity**: **MEDIUM**
  - Tool: Pandoc supports it
  - Challenge: Complex formatting, styles
  - Realistic: ODT ↔ DOCX, ODT ↔ PDF, ODT ↔ TXT
- **User Demand**: **MEDIUM** (LibreOffice users)
- **Bundle Impact**: 0 MB (Pandoc already included)

#### **LaTeX (.tex)**
- **Purpose**: Scientific/academic document typesetting
- **Use Cases**: Research papers, academic writing, math-heavy docs
- **Complexity**: **MEDIUM-HIGH**
  - Tool: Pandoc supports LaTeX ↔ other formats
  - Challenge: Compiling .tex to PDF requires full LaTeX installation (~1-2 GB)
  - Realistic: LaTeX → HTML/MD/DOCX (easy), LaTeX → PDF (requires LaTeX install)
- **User Demand**: **MEDIUM** (academic users)
- **Bundle Impact**: 0 MB (Pandoc) or +1-2 GB (full LaTeX for PDF output)

### Medium Priority

#### **PPT/PPTX (PowerPoint)**
- **Purpose**: Presentations
- **Use Cases**: Business, education
- **Complexity**: **VERY HIGH**
  - Tool: python-pptx or LibreOffice CLI
  - Challenge: Animations, transitions, embedded media
  - Realistic: Can convert PPTX → PDF (flatten) or PPTX → images
  - Cannot convert to other presentation formats well
- **User Demand**: **HIGH** (business users)
- **Bundle Impact**: +50-100 MB (LibreOffice)

#### **Pages (Apple Pages)**
- **Purpose**: Apple's word processor format
- **Use Cases**: Mac users
- **Complexity**: **HIGH** (proprietary, limited tools)
- **User Demand**: **LOW-MEDIUM** (Mac users only)

---

# PART 2: New Categories to Add

## 📐 CAD & 3D MODELS (NEW CATEGORY)

### Formats
- **STL** (3D printing) - **VERY HIGH** demand
- **OBJ** (3D models) - **HIGH** demand
- **FBX** (Game assets) - **MEDIUM** demand
- **GLTF/GLB** (Web 3D) - **MEDIUM-HIGH** demand
- **DWG** (AutoCAD) - **MEDIUM** demand (proprietary, very hard)
- **DXF** (AutoCAD Exchange) - **MEDIUM** demand
- **PLY** (3D scans) - **MEDIUM** demand
- **COLLADA** (.dae) - **LOW** demand

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
- Export preview images (render to PNG)

❌ **Cannot Do Well**:
- CAD ↔ Mesh (loses parametric data)
- Preserve materials/textures perfectly
- Convert animations
- DWG support (proprietary, extremely complex)

### Complexity: **VERY HIGH**
### User Demand: **HIGH** (3D printing enthusiasts, game devs, architects)
### Bundle Impact: +50-100 MB

---

## 🎨 FONTS (NEW CATEGORY)

### Formats
- **TTF** (TrueType) - **HIGH** demand
- **OTF** (OpenType) - **HIGH** demand
- **WOFF/WOFF2** (Web fonts) - **MEDIUM-HIGH** demand
- **EOT** (Embedded OpenType) - **LOW** demand (obsolete)

### Tools Needed
- **fonttools** (Python) - Font conversion and manipulation
- **woff2** (Python wrapper) - WOFF2 compression
- **Size**: ~5-10 MB

### Operations
- Convert between font formats
- Extract font metadata
- Subset fonts (remove unused glyphs)
- Generate web font packages

### Realistic Capabilities
✅ **Can Do**:
- TTF ↔ OTF ↔ WOFF ↔ WOFF2
- Font subsetting
- Metadata extraction
- Web font optimization

❌ **Cannot Do Well**:
- Create fonts from scratch
- Advanced hinting optimization
- Font editing (only conversion)

### Complexity: **MEDIUM**
### User Demand: **MEDIUM-HIGH** (web developers, designers)
### Bundle Impact: +5-10 MB

---

## 📹 SUBTITLES & CAPTIONS (NEW CATEGORY)

### Formats
- **SRT** (SubRip) - **VERY HIGH** demand
- **VTT** (WebVTT) - **HIGH** demand
- **ASS/SSA** (Advanced SubStation Alpha) - **MEDIUM** demand
- **SUB** (MicroDVD) - **LOW** demand

### Tools Needed
- **pysrt** (Python) - SRT parsing/writing
- **webvtt-py** (Python) - WebVTT support
- **Size**: ~1-5 MB

### Operations
- Convert between subtitle formats
- Adjust timing/sync
- Merge/split subtitles
- Extract from video (requires FFmpeg)

### Realistic Capabilities
✅ **Can Do**:
- SRT ↔ VTT ↔ ASS/SSA
- Timing adjustments
- Text extraction
- Format normalization

❌ **Cannot Do Well**:
- Auto-generate subtitles (needs AI/speech recognition)
- Complex styling in simple formats

### Complexity: **EASY-MEDIUM**
### User Demand: **VERY HIGH** (video creators, accessibility)
### Bundle Impact: +1-5 MB

---

## 📚 EBOOKS (NEW CATEGORY)

### Already Covered in Documents
EPUB and MOBI already listed above under Documents → High Priority

### Additional eBook Formats
- **AZW3** (Kindle) - **HIGH** demand (similar to MOBI)
- **FB2** (FictionBook) - **LOW** demand (Russian markets)
- **LIT** (Microsoft Reader) - **VERY LOW** demand (obsolete)

---

## 🗄️ DATABASE & STRUCTURED DATA (Extension of Data Category)

### Formats
- **SQL/SQLite** - **MEDIUM-HIGH** demand
- **YAML** - **MEDIUM** demand
- **TOML** - **MEDIUM** demand
- **INI** - **MEDIUM** demand
- **JSONL/NDJSON** (Newline-delimited JSON) - **MEDIUM** demand

### Tools Needed
- **PyYAML** - YAML support
- **toml** - TOML support
- **sqlite3** (built-in Python) - SQLite
- **Size**: ~5-10 MB

### Operations
- Convert between configuration formats
- SQL → CSV/JSON (export)
- CSV/JSON → SQLite (import)
- YAML ↔ JSON ↔ TOML

### Complexity: **MEDIUM**
### User Demand: **MEDIUM-HIGH** (developers, DevOps)
### Bundle Impact: +5-10 MB

---

## 📧 EMAIL & MESSAGING (NEW CATEGORY)

### Formats
- **EML** (Email message) - **MEDIUM** demand
- **MSG** (Outlook message) - **MEDIUM** demand
- **MBOX** (Mailbox) - **LOW-MEDIUM** demand
- **PST** (Outlook data) - **MEDIUM** demand (very complex)

### Tools Needed
- **email** (Python built-in) - EML support
- **msg-extractor** (Python) - MSG support
- **mailbox** (Python built-in) - MBOX support
- **Size**: ~5-15 MB

### Operations
- Extract email content
- Convert between formats
- Export attachments
- Extract metadata

### Complexity: **MEDIUM-HIGH**
### User Demand: **MEDIUM** (email archiving, legal)
### Bundle Impact: +5-15 MB

---

## 🎮 GAME & MULTIMEDIA (NEW CATEGORY)

### Formats
- **GIF** (Animated) - Already supported for images
- **APNG** (Animated PNG) - **MEDIUM** demand
- **WebM** (Already have)
- **SWF** (Flash) - **LOW** demand (Flash is dead, very complex)

### User Demand: **LOW-MEDIUM** overall

---

# PART 3: Priority Recommendations (Updated)

## 🎯 Top 3 MUST-ADD Categories (Remaining)

### 1. **SUBTITLES & CAPTIONS**
   - Demand: ⭐⭐⭐⭐⭐ (VERY HIGH - video creators need this)
   - Complexity: ⭐⭐ (Easy-Medium)
   - Impact: Essential for accessibility and video content
   - Bundle Size: +1-5 MB
   - **HIGHEST PRIORITY REMAINING**

### 2. **EBOOKS (EPUB/MOBI)**
   - Demand: ⭐⭐⭐⭐⭐ (VERY HIGH - readers, authors, publishers)
   - Complexity: ⭐⭐⭐ (Medium)
   - Impact: Large user base, clear need
   - Bundle Size: +5-10 MB (ebooklib) or +30-80 MB (Calibre)
   - **HIGH PRIORITY**

### 3. **FONTS**
   - Demand: ⭐⭐⭐⭐ (HIGH - web developers, designers)
   - Complexity: ⭐⭐ (Medium)
   - Impact: Strong web development use case
   - Bundle Size: +5-10 MB
   - **HIGH PRIORITY**

### 4. **3D MODELS & CAD**
   - Demand: ⭐⭐⭐⭐ (HIGH - 3D printing boom)
   - Complexity: ⭐⭐⭐⭐⭐ (Very High)
   - Impact: Growing market (3D printing, game dev)
   - Bundle Size: +50-100 MB
   - **MEDIUM-HIGH PRIORITY** (high complexity trade-off)

### 5. **DATABASE/CONFIG FORMATS**
   - Demand: ⭐⭐⭐ (MEDIUM-HIGH - developers)
   - Complexity: ⭐⭐ (Medium)
   - Impact: Developer tools
   - Bundle Size: +5-10 MB
   - **MEDIUM PRIORITY**

---

## ⚡ Quick Wins (Easy to Add)

### Formats Already Supported by Existing Dependencies

1. **TGA** (Image) - 1 hour
   - Already supported by Pillow (0 MB)
   - Just add format to list

2. **MTS/M2TS** (Video) - 1-2 hours
   - Already supported by FFmpeg (0 MB)
   - Just add format to list

3. **VOB** (Video) - 1 hour
   - Already supported by FFmpeg (0 MB)
   - Just add format to list

4. **TS** (Video) - 1 hour
   - Already supported by FFmpeg (0 MB)
   - Just add format to list

5. **APE** (Audio) - 1-2 hours
   - Already supported by FFmpeg (0 MB)
   - Just add format to list

6. **ODT** (Document) - 2-3 hours
   - Already supported by Pandoc (0 MB)
   - Just add router endpoints

---

## 📊 Complexity Tiers (Remaining Formats)

### 🟢 EASY (1-3 hours each)
- TGA, MTS, VOB, TS, APE, OGV, MKA
- **Bundle Impact**: 0 MB (already have dependencies)

### 🟡 MEDIUM (4-8 hours each)
- Subtitles (SRT/VTT), AVIF, RAW images, Fonts, Database formats, ODT

### 🟠 MEDIUM-HIGH (8-15 hours each)
- EPUB, LaTeX, Email formats

### 🔴 HIGH (15-30 hours each)
- MOBI/AZW3 (requires Calibre), PSD, 3D Models, PowerPoint

### ⚫ VERY HIGH (30+ hours each)
- CAD formats (DWG), MIDI conversion, DSD audio, Advanced 3D with textures

---

# PART 4: Implementation Roadmap

## Phase 4 (Recommended Next): Subtitles & Captions
**Time**: 6-8 hours
**Bundle Size**: +1-5 MB
**Formats**: SRT, VTT, ASS/SSA

### Why First:
- VERY HIGH demand (video content explosion)
- Easy-Medium complexity
- Small bundle size
- Accessibility is important
- Fast time-to-value

---

## Phase 5: Quick Wins (FFmpeg Formats)
**Time**: 4-6 hours
**Bundle Size**: 0 MB
**Formats**: MTS, M2TS, VOB, TS, APE, TGA, OGV

### Why Second:
- Zero bundle size (already have dependencies)
- Quick wins to boost format count
- Low risk, high value
- Can knock out 7 formats quickly

---

## Phase 6: eBooks (EPUB)
**Time**: 12-18 hours
**Bundle Size**: +5-10 MB (ebooklib only) or +30-80 MB (full Calibre)
**Formats**: EPUB, optionally MOBI/AZW3

### Why Third:
- VERY HIGH demand
- Clear user need
- Medium complexity
- Decision: Use lightweight ebooklib or full Calibre?

---

## Phase 7: Fonts
**Time**: 8-12 hours
**Bundle Size**: +5-10 MB
**Formats**: TTF, OTF, WOFF, WOFF2

### Why Fourth:
- HIGH demand from web developers
- Medium complexity
- Small bundle size
- Growing importance with web fonts

---

## Phase 8: Database/Config Formats
**Time**: 6-10 hours
**Bundle Size**: +5-10 MB
**Formats**: YAML, TOML, SQLite, INI

### Why Fifth:
- Developer-focused
- Medium demand
- Extends Data category nicely
- Useful for DevOps workflows

---

## Phase 9: 3D Models (If Desired)
**Time**: 20-30 hours
**Bundle Size**: +50-100 MB
**Formats**: STL, OBJ, PLY, GLTF

### Why Later:
- Very high complexity
- Large bundle size
- Niche but growing market
- Requires careful implementation

---

# PART 5: Format Count Analysis

## Current Status
- **Implemented**: 52 formats across 7 categories
- **Missing (Realistic)**: ~40-50 additional formats
- **Total Potential**: ~100 formats

## Missing Breakdown by Category

### Existing Categories (Missing Formats):
- **Images**: 6 formats (RAW, AVIF, TGA, PSD, WebP2, PCX)
- **Videos**: 7 formats (MTS, M2TS, VOB, TS, OGV, more...)
- **Audio**: 4 formats (APE, DSD, MIDI, MKA)
- **Documents**: 6 formats (EPUB, MOBI, ODT, LaTeX, PPT, Pages)

### New Categories (All Formats Missing):
- **Subtitles**: 4 formats (SRT, VTT, ASS, SUB)
- **Fonts**: 4 formats (TTF, OTF, WOFF, WOFF2)
- **3D Models**: 8 formats (STL, OBJ, FBX, GLTF, DWG, DXF, PLY, DAE)
- **Database**: 5 formats (YAML, TOML, SQL, SQLite, INI)
- **Email**: 4 formats (EML, MSG, MBOX, PST)

---

# PART 6: Bundle Size Impact Summary

## Current Bundle Size
Estimated current total: ~150-200 MB (all dependencies)

## Potential Additions by Phase

| Phase | Category | Formats | Bundle Size | Total After |
|-------|----------|---------|-------------|-------------|
| Current | All implemented | 52 | ~150-200 MB | 150-200 MB |
| Phase 4 | Subtitles | 4 | +1-5 MB | 155-205 MB |
| Phase 5 | Quick Wins | 7 | 0 MB | 155-205 MB |
| Phase 6 | eBooks (light) | 2 | +5-10 MB | 160-215 MB |
| Phase 6 | eBooks (Calibre) | 3 | +30-80 MB | 185-285 MB |
| Phase 7 | Fonts | 4 | +5-10 MB | 165-225 MB |
| Phase 8 | Database | 5 | +5-10 MB | 170-235 MB |
| Phase 9 | 3D Models | 8 | +50-100 MB | 220-335 MB |

**Recommendation**: Stick with lightweight libraries when possible (ebooklib over Calibre)

---

# PART 7: User Demand Summary

## By Demand Level

### ⭐⭐⭐⭐⭐ VERY HIGH DEMAND (Remaining)
1. **Subtitles/Captions** (SRT, VTT) - Video accessibility
2. **EPUB** - eBook readers
3. **MOBI/AZW3** - Kindle users

### ⭐⭐⭐⭐ HIGH DEMAND (Remaining)
1. **Fonts** (TTF, OTF, WOFF) - Web developers
2. **RAW Images** - Photographers
3. **3D Models (STL)** - 3D printing
4. **PowerPoint** - Business users

### ⭐⭐⭐ MEDIUM-HIGH DEMAND (Remaining)
1. **Database formats** (YAML, TOML) - Developers
2. **MTS/VOB** - Video archiving
3. **AVIF** - Modern web
4. **LaTeX** - Academia

### ⭐⭐ MEDIUM DEMAND (Remaining)
1. **Email formats** - Archiving
2. **ODT** - LibreOffice users
3. **Advanced subtitle formats** (ASS)

### ⭐ LOW DEMAND (Remaining)
1. **PSD** - Limited use case
2. **DSD** - Niche audiophile
3. **Flash formats** - Obsolete
4. **Legacy formats** (PCX, EOT)

---

# PART 8: Recommendations Summary

## Recommended Implementation Order

1. ✅ **Phase 1**: Quick Wins (HEIC, SVG, OPUS, etc.) - **COMPLETED**
2. ✅ **Phase 2**: Archives - **COMPLETED**
3. ✅ **Phase 3**: Spreadsheets - **COMPLETED**
4. 🎯 **Phase 4**: **Subtitles** (SRT, VTT, ASS) - **RECOMMENDED NEXT**
5. 🎯 **Phase 5**: **Quick Wins 2** (MTS, VOB, TS, APE, TGA, ODT)
6. 🎯 **Phase 6**: **eBooks** (EPUB, MOBI)
7. 🎯 **Phase 7**: **Fonts** (TTF, OTF, WOFF, WOFF2)
8. 🎯 **Phase 8**: **Database/Config** (YAML, TOML, SQLite)
9. 🔮 **Phase 9**: **3D Models** (STL, OBJ, GLTF) - If desired

## Key Decision Points

### Should we add Calibre for better eBook support?
- **Pros**: Full MOBI/AZW3 support, better conversions
- **Cons**: +30-80 MB bundle size
- **Recommendation**: Start with ebooklib (+5-10 MB), upgrade later if needed

### Should we tackle 3D formats?
- **Pros**: Growing market, unique offering, 3D printing boom
- **Cons**: Very complex, large bundle, niche audience
- **Recommendation**: Phase 9 or later, after easier wins

### Should we add LaTeX → PDF compilation?
- **Pros**: Full LaTeX support
- **Cons**: +1-2 GB LaTeX distribution
- **Recommendation**: No. Support LaTeX → HTML/MD/DOCX only (via Pandoc)

---

# PART 9: Competitive Analysis

## What Competitors Support (That We Don't Yet)

### CloudConvert (Major Competitor)
**They have that we're missing**:
- Subtitles (SRT, VTT) ✨ **We should add**
- eBooks (EPUB, MOBI) ✨ **We should add**
- Fonts (TTF, OTF, WOFF) ✨ **We should add**
- 3D Models (STL, OBJ)
- CAD formats (DWG, DXF) - Very complex
- RAW images (CR2, NEF, ARW)

**We have that they charge premium for**:
- ✅ Archive conversion (we have all major formats)
- ✅ Spreadsheet conversion (we have XLSX, ODS, CSV, TSV)
- ✅ Advanced image formats (HEIC, SVG)

### OnlineConvert
**Gaps we have**:
- Video formats: MTS, VOB (easy to add)
- Audio: APE (easy to add)
- Similar eBook/subtitle gaps

### Zamzar
Similar gaps to CloudConvert

## Our Competitive Advantages (After Phases 1-3)
1. ✅ Desktop app (offline conversion)
2. ✅ Archive conversion (ZIP, 7Z, TAR.GZ, etc.)
3. ✅ Spreadsheet conversion (XLSX, ODS)
4. ✅ Data formats (CSV, JSON, XML)
5. ✅ Modern image formats (HEIC, SVG, WebP)
6. ✅ Batch conversion
7. ✅ Open source
8. ✅ No file size limits (competitors have limits)
9. ✅ Privacy (local conversion)

## Our Competitive Gaps (Top Priorities)
1. ❌ Subtitles (SRT, VTT) - **High priority**
2. ❌ eBooks (EPUB, MOBI) - **High priority**
3. ❌ Fonts (TTF, OTF, WOFF) - **Medium-high priority**
4. ❌ RAW images - **Medium priority**
5. ❌ 3D Models - **Medium priority**

---

# Conclusion

## Summary
- **Completed**: 52 formats, 7 categories
- **Realistic Remaining**: ~40-50 formats, 5 new categories
- **Recommended Next**: Subtitles (Phase 4), then Quick Wins (Phase 5)

## Next Steps
1. **Immediate**: Implement Subtitles (SRT, VTT) - Highest demand, easy-medium complexity
2. **Quick Wins**: Add FFmpeg-supported formats (MTS, VOB, TS, APE) - 0 MB bundle cost
3. **Strategic**: eBooks and Fonts - High demand, reasonable complexity

The FileConverter is already very comprehensive with 52 formats. Adding Subtitles, eBooks, and Fonts would make it competitive with major paid converters while maintaining the open-source, privacy-focused approach.
