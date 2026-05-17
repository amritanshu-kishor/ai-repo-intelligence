"""
Simple backend starter for parser-workflow
Runs the FastAPI server directly without complex imports
"""

import sys
import uvicorn

# Add parser-workflow to path
sys.path.insert(0, ".")

if __name__ == "__main__":
    print("=" * 60)
    print("Starting parser-workflow backend...")
    print("=" * 60)
    print("API will be available at: http://127.0.0.1:8001")
    print("Swagger docs at: http://127.0.0.1:8001/docs")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="info"
    )

# Made with Bob
