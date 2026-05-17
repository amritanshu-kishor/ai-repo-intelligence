"""
Universal import fixer for parser-workflow
Replaces all app.* imports with direct imports
"""

import os
import re

def fix_imports_in_file(filepath):
    """Fix all app.* imports in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Replace all app.* imports with direct imports
        # Pattern: from app.anything.module import -> from module import
        content = re.sub(
            r'from app\.[a-zA-Z_\.]+\.([a-zA-Z_]+) import',
            r'from \1 import',
            content
        )
        
        # Pattern: from app.module import -> from module import  
        content = re.sub(
            r'from app\.([a-zA-Z_]+) import',
            r'from \1 import',
            content
        )
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    print("=" * 60)
    print("Fixing ALL app.* imports in parser-workflow")
    print("=" * 60)
    
    fixed_count = 0
    
    for filename in os.listdir('.'):
        if filename.endswith('.py') and filename not in ['fix_imports.py', 'fix_all_imports.py']:
            filepath = os.path.join('.', filename)
            if fix_imports_in_file(filepath):
                print(f"[OK] Fixed {filename}")
                fixed_count += 1
    
    print("=" * 60)
    print(f"Fixed {fixed_count} files")
    print("=" * 60)
    print("\nNow start the backend with:")
    print("  python start_backend.py")

if __name__ == "__main__":
    main()

# Made with Bob
