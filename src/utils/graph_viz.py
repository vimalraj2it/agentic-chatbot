import os
from typing import Any
from src.core.logging_config import get_logger

logger = get_logger(__name__)

def save_graph_visualization(graph: Any, name: str, output_dir: str = "graph"):
    """
    Saves graph visualization (MD and PNG) to the specified directory.
    - graph: The compiled LangGraph instance.
    - name: Base name for the files (e.g., 'smalltalk', 'faq').
    - output_dir: Directory where files will be saved.
    """
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        # 1. Save Markdown (Mermaid)
        md_file = os.path.join(output_dir, f"{name}_flow.md")
        mermaid_content = graph.get_graph().draw_mermaid()
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(f"```mermaid\n{mermaid_content}\n```")
            logger.info(f"Graph visualization saved as Markdown: {md_file}")
            
        # 2. Save PNG
        try:
            png_data = graph.get_graph().draw_mermaid_png()
            png_file = os.path.join(output_dir, f"{name}_flow.png")
            with open(png_file, "wb") as f:
                f.write(png_data)
                logger.info(f"Graph visualization saved as PNG: {png_file}")
        except Exception as png_err:
            # Common if pygraphviz/pprint or node-mermaid isn't local
            logger.warning(f"Could not generate {name}_flow.png: {png_err}")

    except Exception as e:
        logger.error(f"Failed to generate visualization for '{name}': {e}")
