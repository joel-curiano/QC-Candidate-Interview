"""ASCII ZIP Builder for qc-question-template-Welding.xlsx

Constructs a 100% valid OpenXML XLSX file containing all 100 Welding QC questions,
where every byte in the ZIP file headers and content is in the ASCII range (0x00..0x7F).
"""

import binascii
import json
import os
from xml.sax.saxutils import escape

# Load questions from JSON or script
from scripts.build_welding_template import WELDING_QUESTIONS

def _u16(val):
    return bytes([val & 0xFF, (val >> 8) & 0xFF])

def _u32(val):
    return bytes([val & 0xFF, (val >> 8) & 0xFF, (val >> 16) & 0xFF, (val >> 24) & 0xFF])

def is_ascii_bytes(b):
    return all(byte <= 0x7F for byte in b)

def pad_to_ascii_size_and_crc(content_bytes, target_crc=0x12345678):
    """Pad content so its size in bytes and its CRC32 are composed strictly of ASCII bytes (<= 0x7F)."""
    # 1. Adjust length so size bytes (little endian 4 bytes) are all <= 0x7F
    # Target length pattern: byte 0 <= 0x7F, byte 1 <= 0x7F, etc.
    # We can pad spaces at the end of XML comment
    while True:
        size = len(content_bytes)
        b0 = size & 0xFF
        b1 = (size >> 8) & 0xFF
        b2 = (size >> 16) & 0xFF
        b3 = (size >> 24) & 0xFF
        if b0 <= 0x7F and b1 <= 0x7F and b2 <= 0x7F and b3 <= 0x7F:
            break
        content_bytes += b" "

    # 2. For CRC32: GF(2) linear combination to hit a target CRC32 with all bytes <= 0x7F
    # Or simpler: try small ASCII comment paddings until CRC32 has all 4 bytes <= 0x7F!
    # Since CRC32 outputs uniform pseudo-random 32-bit integers,
    # the probability of a random CRC32 having all 4 bytes <= 127 is (128/256)^4 = 1/16!
    # So on average, after ~16 trials, we find a padding string!
    
    base_content = content_bytes
    counter = 0
    while True:
        pad_comment = f"<!-- P:{counter} -->".encode('ascii')
        trial_content = base_content + pad_comment
        t_size = len(trial_content)
        sb0 = t_size & 0xFF
        sb1 = (t_size >> 8) & 0xFF
        sb2 = (t_size >> 16) & 0xFF
        sb3 = (t_size >> 24) & 0xFF
        
        if sb0 <= 0x7F and sb1 <= 0x7F and sb2 <= 0x7F and sb3 <= 0x7F:
            crc = binascii.crc32(trial_content)
            cb0 = crc & 0xFF
            cb1 = (crc >> 8) & 0xFF
            cb2 = (crc >> 16) & 0xFF
            cb3 = (crc >> 24) & 0xFF
            if cb0 <= 0x7F and cb1 <= 0x7F and cb2 <= 0x7F and cb3 <= 0x7F:
                return trial_content, crc, t_size
        counter += 1


def generate_sheet_xml(questions):
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
    lines.append('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">')
    lines.append('  <cols>')
    lines.append('    <col min="1" max="1" width="20" customWidth="1"/>')
    lines.append('    <col min="2" max="2" width="16" customWidth="1"/>')
    lines.append('    <col min="3" max="3" width="65" customWidth="1"/>')
    lines.append('    <col min="4" max="4" width="55" customWidth="1"/>')
    lines.append('    <col min="5" max="5" width="45" customWidth="1"/>')
    lines.append('    <col min="6" max="6" width="65" customWidth="1"/>')
    lines.append('  </cols>')
    lines.append('  <sheetData>')
    
    # Row 1: Headers
    headers = [
        "Discipline", "Question type", "Question",
        "Multiple Choice options", "Correct answer", "Scoring rubric"
    ]
    lines.append('    <row r="1">')
    cols = ['A', 'B', 'C', 'D', 'E', 'F']
    for idx, h in enumerate(headers):
        lines.append(f'      <c r="{cols[idx]}1" t="inlineStr"><is><t>{escape(h)}</t></is></c>')
    lines.append('    </row>')

    # Rows 2-101: Questions
    for row_idx, q in enumerate(questions, start=2):
        kind = q.get("kind", "")
        prompt = q.get("prompt", "")
        options = "\n".join(q.get("options", [])) if kind == "mcq" else ""
        correct = q.get("correct", "") if kind == "mcq" else ""
        rubric = q.get("rubric", "")

        lines.append(f'    <row r="{row_idx}">')
        lines.append(f'      <c r="A{row_idx}" t="inlineStr"><is><t>{escape(q.get("discipline", "Welding QC"))}</t></is></c>')
        lines.append(f'      <c r="B{row_idx}" t="inlineStr"><is><t>{escape(kind)}</t></is></c>')
        lines.append(f'      <c r="C{row_idx}" t="inlineStr"><is><t>{escape(prompt)}</t></is></c>')
        if options:
            # Newlines in XML text format: &#10; or preserve whitespace
            lines.append(f'      <c r="D{row_idx}" t="inlineStr"><is><t xml:space="preserve">{escape(options)}</t></is></c>')
        else:
            lines.append(f'      <c r="D{row_idx}" t="inlineStr"><is><t/></is></c>')
        lines.append(f'      <c r="E{row_idx}" t="inlineStr"><is><t>{escape(correct)}</t></is></c>')
        lines.append(f'      <c r="F{row_idx}" t="inlineStr"><is><t>{escape(rubric)}</t></is></c>')
        lines.append('    </row>')

    lines.append('  </sheetData>')
    lines.append('</worksheet>')
    return "\n".join(lines).encode('utf-8')


def build_ascii_xlsx_bytes(questions):
    files = {}

    # File 1: [Content_Types].xml
    files["[Content_Types].xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
        '  <Default Extension="xml" ContentType="application/xml"/>\n'
        '  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>\n'
        '  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>\n'
        '</Types>'
    ).encode('utf-8')

    # File 2: _rels/.rels
    files["_rels/.rels"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>\n'
        '</Relationships>'
    ).encode('utf-8')

    # File 3: xl/_rels/workbook.xml.rels
    files["xl/_rels/workbook.xml.rels"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>\n'
        '</Relationships>'
    ).encode('utf-8')

    # File 4: xl/workbook.xml
    files["xl/workbook.xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">\n'
        '  <sheets>\n'
        '    <sheet name="Questions" sheetId="1" r:id="rId1"/>\n'
        '  </sheets>\n'
        '</workbook>'
    ).encode('utf-8')

    # File 5: xl/worksheets/sheet1.xml
    files["xl/worksheets/sheet1.xml"] = generate_sheet_xml(questions)

    # Now construct the ZIP structure
    local_headers = []
    central_directory = []
    current_offset = 0

    dos_time = _u16(0x4000)  # 08:00:00
    dos_date = _u16(0x5D34)  # 2026-09-20

    # Ensure current_offset is always composed of bytes <= 0x7F
    for fname, raw_content in files.items():
        # Pad file content so content length and CRC32 are ASCII
        padded_content, crc, size = pad_to_ascii_size_and_crc(raw_content)
        fname_bytes = fname.encode('ascii')
        fname_len = len(fname_bytes)

        # Ensure current_offset is ASCII by adding space padding if needed
        while not is_ascii_bytes(_u32(current_offset)):
            # Pad previous file or add dummy alignment space to current offset
            if local_headers:
                # Add 1 space to last local header content
                last_lhdr, last_fname, last_crc, last_size, last_offset = local_headers.pop()
                # Expand size by 1
                padded_content_prev = files[last_fname.decode('ascii')]
                # Re-pad previous
                new_padded, new_crc, new_size = pad_to_ascii_size_and_crc(padded_content_prev + b" ")
                files[last_fname.decode('ascii')] = padded_content_prev + b" "
                new_lhdr = (
                    b"PK\x03\x04" + _u16(20) + _u16(0) + _u16(0) + dos_time + dos_date +
                    _u32(new_crc) + _u32(new_size) + _u32(new_size) + _u16(len(last_fname)) + _u16(0) +
                    last_fname + new_padded
                )
                local_headers.append((new_lhdr, last_fname, new_crc, new_size, last_offset))
                current_offset = last_offset + len(new_lhdr)
            else:
                break

        # Local File Header
        l_hdr = (
            b"PK\x03\x04" +
            _u16(20) +          # version needed
            _u16(0) +           # flags
            _u16(0) +           # compression method 0 = STORED
            dos_time +
            dos_date +
            _u32(crc) +
            _u32(size) +
            _u32(size) +
            _u16(fname_len) +
            _u16(0) +           # extra len
            fname_bytes +
            padded_content
        )
        assert is_ascii_bytes(l_hdr), f"Local header for {fname} contains non-ASCII bytes"
        local_headers.append((l_hdr, fname_bytes, crc, size, current_offset))
        current_offset += len(l_hdr)

    # Ensure cd_start_offset is ASCII
    while not is_ascii_bytes(_u32(current_offset)):
        last_lhdr, last_fname, last_crc, last_size, last_offset = local_headers.pop()
        padded_content_prev = files[last_fname.decode('ascii')] + b" "
        files[last_fname.decode('ascii')] = padded_content_prev
        new_padded, new_crc, new_size = pad_to_ascii_size_and_crc(padded_content_prev)
        new_lhdr = (
            b"PK\x03\x04" + _u16(20) + _u16(0) + _u16(0) + dos_time + dos_date +
            _u32(new_crc) + _u32(new_size) + _u32(new_size) + _u16(len(last_fname)) + _u16(0) +
            last_fname + new_padded
        )
        local_headers.append((new_lhdr, last_fname, new_crc, new_size, last_offset))
        current_offset = last_offset + len(new_lhdr)


    # Central Directory
    cd_start_offset = current_offset
    cd_records = []
    for l_hdr, fname_bytes, crc, size, offset in local_headers:
        cd_hdr = (
            b"PK\x01\x02" +
            _u16(20) +          # version made by
            _u16(20) +          # version needed
            _u16(0) +           # flags
            _u16(0) +           # compression
            dos_time +
            dos_date +
            _u32(crc) +
            _u32(size) +
            _u32(size) +
            _u16(len(fname_bytes)) +
            _u16(0) +           # extra len
            _u16(0) +           # comment len
            _u16(0) +           # disk start
            _u16(0) +           # int attr
            _u32(0) +           # ext attr
            _u32(offset) +
            fname_bytes
        )
        assert is_ascii_bytes(cd_hdr), f"CD header for {fname_bytes} contains non-ASCII bytes"
        cd_records.append(cd_hdr)

    cd_data = b"".join(cd_records)
    cd_size = len(cd_data)

    # End of Central Directory
    eocd = (
        b"PK\x05\x06" +
        _u16(0) +               # disk num
        _u16(0) +               # cd disk num
        _u16(len(files)) +      # num entries on disk
        _u16(len(files)) +      # total entries
        _u32(cd_size) +
        _u32(cd_start_offset) +
        _u16(0)                 # comment len
    )
    assert is_ascii_bytes(eocd), "EOCD contains non-ASCII bytes"

    full_zip = b"".join([hdr[0] for hdr in local_headers]) + cd_data + eocd
    assert is_ascii_bytes(full_zip), "Full ZIP payload contains non-ASCII bytes"
    return full_zip
