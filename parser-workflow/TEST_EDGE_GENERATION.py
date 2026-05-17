"""
Test script to verify edge generation in the dependency graph
"""
import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        os.system("chcp 65001 > nul")
    except:
        pass

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dependency_extractor import parse_repository
from networkx_service import networkx_service

def test_edge_generation():
    """Test if edges are being generated correctly"""
    
    # Test with a simple mock repository structure
    test_repo = Path(__file__).parent / "_test_repo"
    
    if not test_repo.exists():
        print("❌ Test repository not found. Creating sample files...")
        test_repo.mkdir(exist_ok=True)
        
        # Create sample Python files with imports
        (test_repo / "main.py").write_text("""
import utils
from helpers import process_data

def main():
    utils.log("Starting")
    process_data()
""")
        
        (test_repo / "utils.py").write_text("""
def log(message):
    print(f"LOG: {message}")
""")
        
        (test_repo / "helpers.py").write_text("""
import utils

def process_data():
    utils.log("Processing")
    return True
""")
        
        print("✅ Created sample test repository")
    
    print("\n" + "="*60)
    print("TESTING EDGE GENERATION")
    print("="*60)
    
    # Parse the repository
    print(f"\nParsing repository: {test_repo}")
    parsed_files, dependencies, stats = parse_repository(test_repo)
    
    print(f"\nParse Results:")
    print(f"   Files: {len(parsed_files)}")
    print(f"   Dependencies: {len(dependencies)}")
    print(f"   Stats: {stats}")
    
    print(f"\nParsed Files:")
    for f in parsed_files:
        print(f"   - {f['file']} ({f['language']}): {len(f['imports'])} imports")
    
    print(f"\nDependencies:")
    for i, dep in enumerate(dependencies[:10], 1):
        print(f"   {i}. {dep['from']} -> {dep['to']} ({dep['type']}, resolved={dep.get('resolved', False)})")
    
    # Create NetworkX graph
    print(f"\nCreating NetworkX graph...")
    G = networkx_service.create_graph_from_dependencies(
        "test_repo",
        dependencies,
        parsed_files
    )
    
    print(f"\nGraph Statistics:")
    print(f"   Nodes: {G.number_of_nodes()}")
    print(f"   Edges: {G.number_of_edges()}")
    
    # Convert to Cytoscape format
    print(f"\nConverting to Cytoscape format...")
    cytoscape_data = networkx_service.to_cytoscape_format(G)
    
    elements = cytoscape_data.get("elements", [])
    nodes = [e for e in elements if "source" not in e.get("data", {})]
    edges = [e for e in elements if "source" in e.get("data", {})]
    
    print(f"\nCytoscape Data:")
    print(f"   Total elements: {len(elements)}")
    print(f"   Nodes: {len(nodes)}")
    print(f"   Edges: {len(edges)}")
    
    if edges:
        print(f"\nSUCCESS: Edges are being generated!")
        print(f"\nSample edges:")
        for i, edge in enumerate(edges[:5], 1):
            data = edge.get("data", {})
            print(f"   {i}. {data.get('source')} -> {data.get('target')} ({data.get('edge_type')})")
    else:
        print(f"\nPROBLEM: No edges in Cytoscape format!")
        print(f"\nDebugging info:")
        print(f"   NetworkX edges: {list(G.edges())[:5]}")
        print(f"\nSample elements:")
        for i, elem in enumerate(elements[:5], 1):
            print(f"   {i}. {elem}")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_edge_generation()

# Made with Bob
