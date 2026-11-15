# export_utils.py
import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import streamlit as st
from config import get_config

class ExportManager:
    """Manages exporting of analysis results and conversation history."""

    def __init__(self, export_dir: str = "exports"):
        self.export_dir = export_dir
        self.ensure_export_dir()

    def ensure_export_dir(self):
        """Ensure export directory exists."""
        os.makedirs(self.export_dir, exist_ok=True)

    def export_repository_analysis(self, repo_url: str, analysis_data: Dict[str, Any]) -> str:
        """Export repository analysis data to JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        repo_name = self._extract_repo_name(repo_url)
        filename = f"analysis_{repo_name}_{timestamp}.json"

        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "repository_url": repo_url,
            "repository_name": repo_name,
            "analysis_data": analysis_data
        }

        filepath = os.path.join(self.export_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        return filepath

    def export_conversation_history(self, conversation_history: List[Dict[str, str]]) -> str:
        """Export conversation history to JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{timestamp}.json"

        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "conversation_history": conversation_history
        }

        filepath = os.path.join(self.export_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        return filepath

    def export_code_chunks_csv(self, documents: List, repo_url: str) -> str:
        """Export code chunks to CSV for analysis."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        repo_name = self._extract_repo_name(repo_url)
        filename = f"chunks_{repo_name}_{timestamp}.csv"

        filepath = os.path.join(self.export_dir, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['chunk_index', 'source_file', 'language', 'chunker_type', 'content_length', 'content_preview']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for doc in documents:
                metadata = doc.metadata
                content = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content

                writer.writerow({
                    'chunk_index': metadata.get('chunk_index', 0),
                    'source_file': metadata.get('source', ''),
                    'language': metadata.get('language', 'unknown'),
                    'chunker_type': metadata.get('chunker_type', 'unknown'),
                    'content_length': len(doc.page_content),
                    'content_preview': content.replace('\n', ' ').replace('\r', ' ')
                })

        return filepath

    def export_language_breakdown(self, documents: List, repo_url: str) -> str:
        """Export language breakdown statistics."""
        from collections import defaultdict

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        repo_name = self._extract_repo_name(repo_url)
        filename = f"languages_{repo_name}_{timestamp}.json"

        # Analyze language distribution
        language_stats = defaultdict(lambda: {'count': 0, 'total_chars': 0, 'files': set()})

        for doc in documents:
            metadata = doc.metadata
            lang = metadata.get('language', 'unknown')
            language_stats[lang]['count'] += 1
            language_stats[lang]['total_chars'] += len(doc.page_content)
            language_stats[lang]['files'].add(metadata.get('source', ''))

        # Convert sets to lists for JSON serialization
        for lang_data in language_stats.values():
            lang_data['files'] = list(lang_data['files'])
            lang_data['avg_chunk_size'] = lang_data['total_chars'] // lang_data['count'] if lang_data['count'] > 0 else 0

        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "repository_url": repo_url,
            "repository_name": repo_name,
            "language_statistics": dict(language_stats)
        }

        filepath = os.path.join(self.export_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        return filepath

    def _extract_repo_name(self, repo_url: str) -> str:
        """Extract repository name from URL."""
        from urllib.parse import urlparse
        parsed = urlparse(repo_url)
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) >= 2:
            return f"{path_parts[-2]}_{path_parts[-1]}"
        return "unknown_repo"

    def get_export_history(self) -> List[Dict[str, Any]]:
        """Get list of all exported files."""
        exports = []
        if os.path.exists(self.export_dir):
            for filename in os.listdir(self.export_dir):
                filepath = os.path.join(self.export_dir, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    exports.append({
                        'filename': filename,
                        'filepath': filepath,
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'type': self._get_export_type(filename)
                    })

        # Sort by creation time, newest first
        exports.sort(key=lambda x: x['created'], reverse=True)
        return exports

    def _get_export_type(self, filename: str) -> str:
        """Determine export type from filename."""
        if filename.startswith('analysis_'):
            return 'analysis'
        elif filename.startswith('conversation_'):
            return 'conversation'
        elif filename.startswith('chunks_'):
            return 'chunks'
        elif filename.startswith('languages_'):
            return 'languages'
        else:
            return 'unknown'

# Global export manager instance
_export_manager = None

def get_export_manager() -> ExportManager:
    """Get the global export manager instance."""
    global _export_manager
    if _export_manager is None:
        config = get_config()
        _export_manager = ExportManager(os.path.join(config.cache_dir, "exports"))
    return _export_manager

def create_export_ui():
    """Create Streamlit UI components for export functionality."""
    export_manager = get_export_manager()

    st.sidebar.header("📤 Export Options")

    # Export current analysis
    if st.session_state.get('rag_chain') is not None:
        st.sidebar.subheader("Export Current Analysis")

        if st.sidebar.button("📊 Export Analysis Summary"):
            # This would need to be implemented with actual analysis data
            st.sidebar.success("Analysis export feature coming soon!")

        if st.sidebar.button("💬 Export Conversation"):
            # This would need conversation history tracking
            st.sidebar.success("Conversation export feature coming soon!")

    # View export history
    st.sidebar.subheader("Export History")
    export_history = export_manager.get_export_history()

    if export_history:
        for export in export_history[:5]:  # Show last 5 exports
            with st.sidebar.expander(f"📄 {export['filename'][:30]}..."):
                st.write(f"**Type:** {export['type'].title()}")
                st.write(f"**Size:** {export['size']} bytes")
                st.write(f"**Created:** {export['created'][:19]}")

                # Download button
                with open(export['filepath'], 'rb') as f:
                    st.download_button(
                        label="⬇️ Download",
                        data=f,
                        file_name=export['filename'],
                        mime="application/octet-stream"
                    )
    else:
        st.sidebar.write("No exports yet")

if __name__ == "__main__":
    # Example usage
    export_manager = ExportManager()

    # Example data
    sample_analysis = {
        "file_count": 150,
        "chunk_count": 1200,
        "languages": {"python": 800, "javascript": 300, "markdown": 100}
    }

    filepath = export_manager.export_repository_analysis(
        "https://github.com/pallets/flask",
        sample_analysis
    )

    print(f"Exported analysis to: {filepath}")
