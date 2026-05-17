"""
Fix import paths in parser-workflow files
Converts app.module imports to direct imports
"""

import os
import re
from pathlib import Path

# Files to fix and their import replacements
IMPORT_FIXES = {
    'main.py': [
        ('from app.core.config import', 'from config import'),
        ('from app.core.logger import', 'from logger import'),
        ('from app.routes import chroma_router, parser_router, repository_router', ''),
        ('from app.routes.cytoscape_routes import', 'from cytoscape_routes import'),
        ('from app.routes.upload_routes import', 'from upload_routes import'),
    ],
    'chroma_routes.py': [
        ('from app.schemas.chroma_schema import', 'from chroma_schema import'),
        ('from app.services.chroma_service import', 'from chroma_service import'),
        ('from app.core.logger import', 'from logger import'),
    ],
    'parser_routes.py': [
        ('from app.schemas.parser_schema import', 'from parser_schema import'),
        ('from app.services.parser_service import', 'from parser_service import'),
    ],
    'repository_routes.py': [
        ('from app.schemas.repository_schema import', 'from repository_schema import'),
        ('from app.services.repository_service import', 'from repository_service import'),
    ],
    'cytoscape_routes.py': [
        ('from app.services.networkx_service import', 'from networkx_service import'),
        ('from app.services.analytics_service import', 'from analytics_service import'),
        ('from app.core.logger import', 'from logger import'),
    ],
    'upload_routes.py': [
        ('from app.services.repository_service import', 'from repository_service import'),
        ('from app.core.logger import', 'from logger import'),
    ],
    'parser_service.py': [
        ('from app.connectors.treesitter_connector import', 'from treesitter_connector import'),
        ('from app.schemas.parser_schema import', 'from parser_schema import'),
    ],
    'repository_service.py': [
        ('from app.schemas.repository_schema import', 'from repository_schema import'),
        ('from app.utils.file_handler import', 'from file_handler import'),
    ],
}

def fix_file(filepath: Path, replacements: list):
    """Fix imports in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        for old_import, new_import in replacements:
            if old_import in content:
                if new_import:
                    content = content.replace(old_import, new_import)
                    print(f"  Fixed: {old_import} -> {new_import}")
                else:
                    # Remove the line entirely
                    lines = content.split('\n')
                    lines = [line for line in lines if old_import not in line]
                    content = '\n'.join(lines)
                    print(f"  Removed: {old_import}")
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] Fixed {filepath.name}")
            return True
        else:
            print(f"  No changes needed for {filepath.name}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error fixing {filepath.name}: {e}")
        return False

def main():
    print("=" * 60)
    print("Fixing parser-workflow import paths...")
    print("=" * 60)
    
    script_dir = Path(__file__).parent
    fixed_count = 0
    
    for filename, replacements in IMPORT_FIXES.items():
        filepath = script_dir / filename
        if filepath.exists():
            print(f"\nProcessing {filename}...")
            if fix_file(filepath, replacements):
                fixed_count += 1
        else:
            print(f"  File not found: {filename}")
    
    print("\n" + "=" * 60)
    print(f"Fixed {fixed_count} files")
    print("=" * 60)
    print("\nNow you can start the backend with:")
    print("  python start_backend.py")

if __name__ == "__main__":
    main()

# Made with Bob
