import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import json
from outline_builder import OutlineBuilderFactory
import logging

def serialize_outline(outline):
    d = outline.__dict__.copy()
    # Convert headings to dicts if present
    if hasattr(outline, 'headings'):
        d['headings'] = [h.to_dict() for h in outline.headings]
    return d

def main():
    input_dir = "input"
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    log_path = os.path.join(output_dir, "processing.log")
    builder = OutlineBuilderFactory.create_basic_builder()
    with open(log_path, "a", encoding="utf-8") as logf:
        for filename in os.listdir(input_dir):
            if filename.lower().endswith(".pdf"):
                pdf_path = os.path.join(input_dir, filename)
                outline = builder.build_outline(pdf_path)
                result = outline.to_dict()
                out_name = os.path.splitext(filename)[0] + ".json"
                # Write schema-compliant output
                with open(os.path.join(output_dir, out_name), "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                # Write debug output (full details, serializable)
                debug_name = os.path.splitext(filename)[0] + "_debugoutput.json"
                with open(os.path.join(output_dir, debug_name), "w", encoding="utf-8") as f:
                    json.dump(serialize_outline(outline), f, ensure_ascii=False, indent=2)
                # Append to single log file
                logf.write(f"Processed {filename}: output -> {out_name}, debug -> {debug_name}, headings: {len(result.get('outline', []))}\n")

if __name__ == "__main__":
    main() 