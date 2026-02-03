# ORM Texture Combiner

A simple drag-and-drop application to combine three texture maps into a single ORM (Occlusion-Roughness-Metallic) texture.

## What it does

Combines three texture files into a single ORM (Occlusion-Roughness-Metallic) texture:
- AO/Occlusion map → Red channel
- Roughness map → Green channel  
- Metallic map → Blue channel

**Now with Batch Processing!** Process hundreds of texture sets at once!

The tool automatically detects common texture suffixes including:
- **AO/Occlusion**: _AO, _ao, _O, _o, _OCC, _occ, _Occlusion, _occlusion, _ambientocclusion
- **Roughness**: _ROUGH, _rough, _R, _r, _Roughness, _roughness, _GLOSS, _gloss, _Glossiness
- **Metallic**: _METAL, _metal, _MET, _met, _M, _m, _Metallic, _metallic, _Metalness, _metalness

Output files: `(BaseName)_ORM.png` (saved in same directory as source files)

## Installation

1. Make sure you have Python 3.7 or later installed
2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python orm_combiner.py
```
or just double-click `run_orm_combiner.bat`

2. Drag and drop texture files or entire folders into the window
   - Files can have any common AO, Roughness, or Metallic suffix (see list above)
   - Files are automatically grouped by base name
   - You can drop multiple files or entire folders at once!

3. Review the detected texture sets in the list
   - ✓ = Complete set (all three maps found)
   - ✗ = Missing maps
   - Green text = Ready to process
   - Orange text = Incomplete set (will be skipped)

4. Click "Combine All Textures" to process all complete sets

5. ORM files will be saved in the same directory as their source files

## Examples

**Single texture set:**
- Drop: `wood_ao.png`, `wood_rough.png`, `wood_metal.png`
- Creates: `wood_ORM.png`

**Batch processing:**
- Drop an entire folder containing 200+ textures
- All matching sets are automatically detected and grouped
- Click once to process all sets at once!

## Requirements

- Python 3.7+
- Pillow (PIL)
- tkinterdnd2

## Notes

- All three images must have the same dimensions
- The application extracts the **red channel** from each input image and combines them into RGB channels
- Output is saved as PNG format
