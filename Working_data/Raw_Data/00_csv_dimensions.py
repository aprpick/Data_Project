from pathlib import Path
import csv
from datetime import datetime

# --- CONFIGURATION ---
SCRIPT_DIR = Path(__file__).parent
OUTPUT_FILE = SCRIPT_DIR / "00_csv_dimensions_report.md"

def get_csv_info(csv_path):
    """Get row count, column count, and file size for a CSV"""
    info = {
        'filename': csv_path.name,
        'size_mb': csv_path.stat().st_size / (1024 * 1024),
        'rows': 0,
        'columns': 0,
        'column_names': []
    }
    
    # Count rows and get headers
    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        info['column_names'] = next(reader)  # Header row
        info['columns'] = len(info['column_names'])
        info['rows'] = sum(1 for _ in reader)  # Count data rows
    
    return info

def generate_report():
    """Generate markdown report for all CSVs in the directory"""
    
    # Find all CSV files
    csv_files = sorted(SCRIPT_DIR.glob("*.csv"))
    
    if not csv_files:
        print("❌ No CSV files found in directory")
        return
    
    print(f"📊 Analyzing {len(csv_files)} CSV file(s)...\n")
    
    # Collect info
    results = []
    for csv_file in csv_files:
        print(f"📖 Processing: {csv_file.name}")
        info = get_csv_info(csv_file)
        results.append(info)
        print(f"   ✅ {info['rows']:,} rows × {info['columns']} columns ({info['size_mb']:.1f} MB)\n")
    
    # Generate markdown report
    report_lines = [
        "# CSV Dimensions Report",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n",
        "## Summary\n",
        "| Filename | Rows | Columns | Size (MB) |",
        "|----------|------|---------|-----------|"
    ]
    
    total_rows = 0
    total_size = 0
    
    for info in results:
        report_lines.append(
            f"| {info['filename']} | {info['rows']:,} | {info['columns']} | {info['size_mb']:.2f} |"
        )
        total_rows += info['rows']
        total_size += info['size_mb']
    
    report_lines.extend([
        f"| **TOTAL** | **{total_rows:,}** | — | **{total_size:.2f}** |\n",
        "## Detailed Breakdown\n"
    ])
    
    # Detailed section for each file
    for info in results:
        report_lines.extend([
            f"### {info['filename']}\n",
            f"- **Rows:** {info['rows']:,}",
            f"- **Columns:** {info['columns']}",
            f"- **File Size:** {info['size_mb']:.2f} MB",
            f"- **Avg bytes/row:** {(info['size_mb'] * 1024 * 1024 / max(info['rows'], 1)):.1f}\n",
            "**Columns:**"
        ])
        
        # List columns in a more compact format (3 per line)
        cols = info['column_names']
        for i in range(0, len(cols), 3):
            chunk = cols[i:i+3]
            report_lines.append("- " + " • ".join(f"`{c}`" for c in chunk))
        
        report_lines.append("")  # Blank line between files
    
    # Write report
    report_content = "\n".join(report_lines)
    OUTPUT_FILE.write_text(report_content, encoding='utf-8')
    
    print(f"✅ Report saved to: {OUTPUT_FILE.name}")
    print(f"📊 Total: {total_rows:,} rows across {len(results)} files ({total_size:.2f} MB)")

if __name__ == "__main__":
    print("📁 CSV Dimensions Analyzer\n")
    print(f"Directory: {SCRIPT_DIR}\n")
    generate_report()