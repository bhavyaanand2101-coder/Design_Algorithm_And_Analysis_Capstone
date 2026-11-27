"""
generate_pdf_report.py
Generates a comprehensive, publication-grade academic PDF report titled "Report.pdf".
"""

import os
import base64
import subprocess
import shutil

def get_base64_image(image_path: str) -> str:
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/png;base64,{encoded}"
    return ""

def main():
    print("📄 Reading HTML Template...")
    with open("report/report_template.html", "r") as f:
        html = f.read()

    print("🖼️  Embedding Base64 High-Resolution Visual Charts...")
    html = html.replace("{{IMG_CITY_ROUTE}}", get_base64_image("output/charts/city_route_map.png"))
    html = html.replace("{{IMG_CITY_DP}}", get_base64_image("output/charts/city_dp_heatmap.png"))
    html = html.replace("{{IMG_SORTING}}", get_base64_image("output/charts/sorting_runtime_comparison.png"))
    html = html.replace("{{IMG_KNAPSACK}}", get_base64_image("output/charts/knapsack_runtime_comparison.png"))
    html = html.replace("{{IMG_TSP}}", get_base64_image("output/charts/tsp_runtime_comparison.png"))
    html = html.replace("{{IMG_PIPELINE}}", get_base64_image("output/charts/pipeline_latency_breakdown.png"))

    temp_html_path = os.path.abspath("output/report_temp.html")
    with open(temp_html_path, "w") as f:
        f.write(html)

    pdf_output_path = os.path.abspath("Report.pdf")
    print(f"🖨️  Rendering PDF via Google Chrome Headless engine to {pdf_output_path}...")

    chrome_cmd = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={pdf_output_path}",
        "--no-pdf-header-footer",
        temp_html_path
    ]

    res = subprocess.run(chrome_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if os.path.exists(pdf_output_path):
        size_kb = os.path.getsize(pdf_output_path) / 1024.0
        print(f"✅ Successfully generated {pdf_output_path} ({size_kb:.1f} KB)!")
        
        # Also copy to report/Report.pdf
        shutil.copyfile(pdf_output_path, "report/Report.pdf")
        print("✅ Copied to report/Report.pdf")
    else:
        print("❌ Error: Failed to generate PDF.")
        print(res.stderr)

if __name__ == "__main__":
    main()
