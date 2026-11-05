#!/data/data/com.termux/files/usr/bin/env python
from fontTools import subset
import sys
# Unicode blocks that carry Chinese (and CJK-shared) glyphs.
CJK_BLOCKS = [
    (0x2E80, 0x2EFF),  # CJK Radicals Supplement
    (0x2F00, 0x2FDF),  # Kangxi Radicals
    (0x3000, 0x303F),  # CJK Symbols and Punctuation
    (0x31C0, 0x31EF),  # CJK Strokes
    (0x3200, 0x32FF),  # Enclosed CJK Letters and Months
    (0x3300, 0x33FF),  # CJK Compatibility
    (0x3400, 0x4DBF),  # Unified Ideographs Ext. A
    (0x4E00, 0x9FFF),  # Unified Ideographs
    (0xF900, 0xFAFF),  # Compatibility Ideographs
    (0xFE30, 0xFE4F),  # CJK Compatibility Forms
    (0xFF00, 0xFFEF),  # Halfwidth/Fullwidth Forms
    (0x20000, 0x2A6DF),# Ext. B
    (0x2A700, 0x2EBEF),# Ext. C–F
    (0x2F800, 0x2FA1F),# Compatibility Ideographs Supplement
    (0x30000, 0x323AF),# Ext. G–H
]
# Add these if you also want Japanese/Korean out:
# (0x3040,0x30FF) kana, (0x3100,0x312F) bopomofo, (0xAC00,0xD7AF) hangul

def is_cjk(cp):
    return any(lo <= cp <= hi for lo, hi in CJK_BLOCKS)

SRC, DST = sys.argv[1], "out.ttf"

opts = subset.Options()
opts.layout_features = ["*"]      # keep GSUB/GPOS rules that survive
opts.name_IDs = ["*"]             # keep full name table
opts.name_languages = ["*"]
opts.notdef_outline = True
opts.recommended_glyphs = True    # space, nbsp, .notdef
opts.glyph_names = True

font = subset.load_font(SRC, opts)
keep = sorted(cp for cp in font.getBestCmap() if not is_cjk(cp))
print(f"keeping {len(keep):,} code points")

sub = subset.Subsetter(options=opts)
sub.populate(unicodes=keep)
sub.subset(font)
subset.save_font(font, DST, opts)
