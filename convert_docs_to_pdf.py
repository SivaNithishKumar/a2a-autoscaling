#!/usr/bin/env python3
"""
Convert all markdown files in the docs folder to a comprehensive PDF.
This script combines all documentation into a single PDF for easy reading and sharing.
"""

import os
import glob
import markdown
import pdfkit
from pathlib import Path
import re
from datetime import datetime

class DocsToePDFConverter:
    def __init__(self, docs_dir="docs", output_file="AI_Ops_Complete_Documentation.pdf"):
        self.docs_dir = docs_dir
        self.output_file = output_file
        self.combined_html = ""
        self.css_styles = self._get_css_styles()
        
    def _get_css_styles(self):
        """Get CSS styles for better PDF formatting."""
        return """
        <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 40px;
            font-size: 12px;
        }
        
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 30px;
            font-size: 24px;
            page-break-before: always;
        }
        
        h2 {
            color: #34495e;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 5px;
            margin-top: 25px;
            font-size: 20px;
        }
        
        h3 {
            color: #34495e;
            margin-top: 20px;
            font-size: 16px;
        }
        
        h4 {
            color: #7f8c8d;
            margin-top: 15px;
            font-size: 14px;
        }
        
        code {
            background-color: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 11px;
            color: #e74c3c;
        }
        
        pre {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 5px;
            padding: 15px;
            overflow-x: auto;
            margin: 15px 0;
            font-size: 10px;
            line-height: 1.4;
        }
        
        pre code {
            background: none;
            padding: 0;
            color: #2c3e50;
        }
        
        blockquote {
            border-left: 4px solid #3498db;
            margin: 20px 0;
            padding: 10px 20px;
            background-color: #f8f9fa;
            font-style: italic;
        }
        
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
            font-size: 11px;
        }
        
        table, th, td {
            border: 1px solid #bdc3c7;
        }
        
        th, td {
            padding: 8px;
            text-align: left;
        }
        
        th {
            background-color: #ecf0f1;
            font-weight: bold;
        }
        
        ul, ol {
            margin: 10px 0;
            padding-left: 30px;
        }
        
        li {
            margin: 5px 0;
        }
        
        .document-header {
            background-color: #3498db;
            color: white;
            padding: 20px;
            text-align: center;
            margin: -40px -40px 30px -40px;
            border-radius: 0;
        }
        
        .document-title {
            font-size: 28px;
            margin: 0;
            font-weight: bold;
        }
        
        .document-subtitle {
            font-size: 16px;
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        
        .toc {
            background-color: #f8f9fa;
            border: 2px solid #dee2e6;
            border-radius: 5px;
            padding: 20px;
            margin: 30px 0;
        }
        
        .toc h2 {
            margin-top: 0;
            color: #2c3e50;
            border-bottom: 1px solid #bdc3c7;
        }
        
        .toc ul {
            list-style-type: none;
            padding-left: 0;
        }
        
        .toc li {
            margin: 8px 0;
            padding: 5px;
        }
        
        .toc a {
            text-decoration: none;
            color: #3498db;
            font-weight: 500;
        }
        
        .file-separator {
            border-top: 3px solid #e74c3c;
            margin: 40px 0;
            padding-top: 20px;
        }
        
        .warning {
            background-color: #fff3cd;
            border: 1px solid #ffeeba;
            color: #856404;
            padding: 10px;
            border-radius: 5px;
            margin: 15px 0;
        }
        
        .info {
            background-color: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
            padding: 10px;
            border-radius: 5px;
            margin: 15px 0;
        }
        
        @media print {
            body { margin: 20px; }
            h1 { page-break-before: always; }
            pre, blockquote { page-break-inside: avoid; }
        }
        </style>
        """
    
    def get_markdown_files(self):
        """Get all markdown files in the docs directory, sorted appropriately."""
        patterns = [
            f"{self.docs_dir}/**/*.md",
            f"{self.docs_dir}/*.md"
        ]
        
        md_files = []
        for pattern in patterns:
            md_files.extend(glob.glob(pattern, recursive=True))
        
        # Sort files to ensure proper order (interview-prep files first, then others)
        def sort_key(filepath):
            filename = os.path.basename(filepath)
            # Prioritize interview-prep files
            if 'interview-prep' in filepath:
                if filename.startswith(('01-', '02-', '03-', '04-', '05-', '06-', '07-', '08-', '09-', '10-')):
                    return (0, filename)
                else:
                    return (1, filename)
            else:
                return (2, filename)
        
        md_files.sort(key=sort_key)
        return md_files
    
    def read_markdown_file(self, filepath):
        """Read and return the content of a markdown file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return f"# Error Reading File\n\nCould not read {filepath}: {e}\n\n"
    
    def markdown_to_html(self, markdown_content):
        """Convert markdown content to HTML."""
        # Configure markdown extensions for better formatting
        md = markdown.Markdown(extensions=[
            'extra',           # Tables, code blocks, etc.
            'codehilite',      # Syntax highlighting
            'toc',             # Table of contents
            'fenced_code',     # Fenced code blocks
            'tables'           # Table support
        ])
        
        return md.convert(markdown_content)
    
    def create_title_page(self):
        """Create a title page for the PDF."""
        title_page = f"""
        <div class="document-header">
            <h1 class="document-title">AI Ops Complete Documentation</h1>
            <p class="document-subtitle">Comprehensive Guide for Enterprise AI Operations</p>
            <p class="document-subtitle">Generated on {datetime.now().strftime('%B %d, %Y')}</p>
        </div>
        """
        return title_page
    
    def create_table_of_contents(self, md_files):
        """Create a table of contents for all documents."""
        toc_html = '<div class="toc"><h2>📚 Table of Contents</h2><ul>'
        
        for i, filepath in enumerate(md_files, 1):
            filename = os.path.basename(filepath)
            # Extract title from filename or first heading
            title = self._extract_title_from_file(filepath)
            relative_path = os.path.relpath(filepath, self.docs_dir)
            
            toc_html += f'<li><strong>{i:02d}.</strong> <a href="#{self._create_anchor(title)}">{title}</a><br><small>{relative_path}</small></li>'
        
        toc_html += '</ul></div>'
        return toc_html
    
    def _extract_title_from_file(self, filepath):
        """Extract title from the first H1 heading in the file."""
        content = self.read_markdown_file(filepath)
        
        # Look for first H1 heading
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        
        # Fallback to filename
        filename = os.path.basename(filepath)
        return filename.replace('.md', '').replace('-', ' ').title()
    
    def _create_anchor(self, title):
        """Create a URL-safe anchor from title."""
        return re.sub(r'[^a-zA-Z0-9]', '-', title.lower()).strip('-')
    
    def process_all_files(self):
        """Process all markdown files and combine them into HTML."""
        md_files = self.get_markdown_files()
        
        if not md_files:
            print(f"No markdown files found in {self.docs_dir} directory!")
            return False
        
        print(f"Found {len(md_files)} markdown files:")
        for f in md_files:
            print(f"  - {f}")
        
        # Start building the combined HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>AI Ops Complete Documentation</title>
            {self.css_styles}
        </head>
        <body>
        """
        
        # Add title page
        html_content += self.create_title_page()
        
        # Add table of contents
        html_content += self.create_table_of_contents(md_files)
        
        # Process each markdown file
        for i, filepath in enumerate(md_files, 1):
            print(f"Processing {i}/{len(md_files)}: {filepath}")
            
            # Add file separator
            title = self._extract_title_from_file(filepath)
            relative_path = os.path.relpath(filepath, self.docs_dir)
            
            html_content += f'''
            <div class="file-separator">
                <h1 id="{self._create_anchor(title)}">{title}</h1>
                <p><em>Source: {relative_path}</em></p>
            </div>
            '''
            
            # Read and convert markdown
            markdown_content = self.read_markdown_file(filepath)
            
            # Remove the first H1 heading since we already added it
            lines = markdown_content.split('\n')
            if lines and lines[0].startswith('# '):
                markdown_content = '\n'.join(lines[1:])
            
            html_body = self.markdown_to_html(markdown_content)
            html_content += html_body
        
        html_content += "</body></html>"
        
        self.combined_html = html_content
        return True
    
    def save_html_file(self, html_filename="temp_combined_docs.html"):
        """Save the combined HTML to a temporary file."""
        try:
            with open(html_filename, 'w', encoding='utf-8') as file:
                file.write(self.combined_html)
            print(f"HTML file saved: {html_filename}")
            return html_filename
        except Exception as e:
            print(f"Error saving HTML file: {e}")
            return None
    
    def convert_to_pdf(self, html_filename):
        """Convert HTML to PDF using wkhtmltopdf."""
        try:
            # PDF options compatible with unpatched Qt version
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'quiet': '',
            }
            
            print(f"Converting to PDF: {self.output_file}")
            pdfkit.from_file(html_filename, self.output_file, options=options)
            print(f"✅ PDF successfully created: {self.output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error converting to PDF: {e}")
            print("Make sure wkhtmltopdf is installed:")
            print("  Ubuntu/Debian: sudo apt-get install wkhtmltopdf")
            print("  macOS: brew install wkhtmltopdf")
            print("  Or install via: https://wkhtmltopdf.org/downloads.html")
            return False
    
    def cleanup(self, html_filename):
        """Clean up temporary files."""
        try:
            if os.path.exists(html_filename):
                os.remove(html_filename)
                print(f"Cleaned up temporary file: {html_filename}")
        except Exception as e:
            print(f"Warning: Could not clean up {html_filename}: {e}")
    
    def convert(self):
        """Main conversion process."""
        print("🚀 Starting conversion of docs to PDF...")
        print(f"📁 Source directory: {self.docs_dir}")
        print(f"📄 Output file: {self.output_file}")
        print("-" * 50)
        
        # Process all markdown files
        if not self.process_all_files():
            print("❌ Failed to process markdown files")
            return False
        
        # Save temporary HTML file
        html_filename = "temp_combined_docs.html"
        if not self.save_html_file(html_filename):
            print("❌ Failed to save HTML file")
            return False
        
        # Convert to PDF
        success = self.convert_to_pdf(html_filename)
        
        # Cleanup
        self.cleanup(html_filename)
        
        if success:
            print("-" * 50)
            print(f"✅ Conversion completed successfully!")
            print(f"📄 PDF file: {os.path.abspath(self.output_file)}")
            
            # Show file size
            if os.path.exists(self.output_file):
                file_size = os.path.getsize(self.output_file) / (1024 * 1024)  # MB
                print(f"📊 File size: {file_size:.2f} MB")
        else:
            print("❌ Conversion failed")
        
        return success

def main():
    """Main function to run the conversion."""
    converter = DocsToePDFConverter(
        docs_dir="docs",
        output_file="AI_Ops_Complete_Documentation.pdf"
    )
    
    success = converter.convert()
    
    if success:
        print("\n🎉 Your AI Ops documentation is now available as a comprehensive PDF!")
        print("📚 Perfect for offline reading, sharing, or interview preparation.")
    else:
        print("\n💡 If you encounter issues, make sure you have the required dependencies:")
        print("   pip install markdown pdfkit")
        print("   sudo apt-get install wkhtmltopdf  # On Ubuntu/Debian")

if __name__ == "__main__":
    main()