"""
Phase 3 Personal Research Portal (PRP) — Streamlit UI.

Run: streamlit run src/app/main.py

Requires: make setup (or equivalent) to build index. GROQ_API_KEY in .env for generation.
"""

import os
import sys

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

import streamlit as st

st.set_page_config(page_title="Personal Research Portal", page_icon="📚", layout="wide")

# Lazy imports for RAG (heavy)
def _run_query(query_text: str, top_k: int = 5):
    from src.rag.query import run_query
    return run_query(query_text, top_k=top_k)

def _save_thread(query: str, chunks: list, answer: str):
    from src.threads.store import save_thread
    return save_thread(query=query, chunks=chunks, answer=answer)

def _load_threads():
    from src.threads.store import load_threads
    return load_threads()

def _build_evidence_table(thread: dict):
    from src.artifacts.evidence_table import (
        build_evidence_table,
        evidence_table_to_markdown,
        evidence_table_to_csv,
        evidence_table_to_html,
    )
    rows = build_evidence_table(thread)
    return (
        rows,
        evidence_table_to_markdown(rows),
        evidence_table_to_csv(rows),
        evidence_table_to_html(rows),
    )


def _get_eval_summary(log_path=None):
    from pathlib import Path
    from src.eval.summarize import load_eval_log, summarize, summarize_to_markdown
    logs_dir = REPO_ROOT / "logs"
    path = Path(log_path) if log_path else None
    if not path or not path.exists():
        paths = sorted(logs_dir.glob("eval_run_*.jsonl"), reverse=True)
        path = paths[0] if paths else None
    if not path or not path.exists():
        return None, "No evaluation logs found. Run evaluation first."
    entries = load_eval_log(path)
    if not entries:
        return None, "Empty log file."
    summary = summarize(entries)
    return summary, summarize_to_markdown(summary, path)


# --- Sidebar: navigation ---
st.sidebar.title("📚 Personal Research Portal")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigate",
    ["Ask", "Threads", "Artifacts", "Evaluation"],
    index=0,
)

# --- Page: Ask ---
if page == "Ask":
    st.header("Ask a research question")
    st.markdown("Enter your question to retrieve evidence from the corpus and generate a cited answer.")

    query = st.text_area("Question", placeholder="e.g., What does RAGAS measure for faithfulness?", height=80)
    top_k = st.slider("Top-k chunks", min_value=1, max_value=10, value=5)

    if st.button("Search & Generate", type="primary"):
        if not query.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Retrieving and generating..."):
                try:
                    result = _run_query(query.strip(), top_k=top_k)
                    st.session_state["last_result"] = result
                except FileNotFoundError as e:
                    st.error(f"Index not found. Run `make setup` first: {e}")
                except Exception as e:
                    st.error(str(e))

    if "last_result" in st.session_state:
        r = st.session_state["last_result"]
        st.markdown("### Answer")
        st.markdown(r["answer"])

        # Trust behavior: suggested next retrieval when evidence is missing
        answer_lower = (r.get("answer") or "").lower()
        if "corpus does not contain evidence" in answer_lower or "no evidence" in answer_lower:
            from src.rag.suggestions import format_suggestion_message
            st.info(format_suggestion_message())

        with st.expander("View retrieved sources"):
            for i, c in enumerate(r["chunks"], 1):
                st.markdown(f"**[{i}] {c['chunk_id']}** (score: {c.get('score', 0):.3f})")
                st.caption(f"Source: {c.get('source_id', '?')}")
                st.text(c.get("text", "")[:400] + ("..." if len(c.get("text", "")) > 400 else ""))
                st.markdown("---")

        col1, col2, _ = st.columns([1, 1, 2])
        with col1:
            if st.button("Save as thread"):
                thread = _save_thread(r["query"], r["chunks"], r["answer"])
                st.success(f"Saved as thread {thread['thread_id']}")
                st.session_state["threads_refresh"] = True

# --- Page: Threads ---
elif page == "Threads":
    st.header("Research threads")
    st.markdown("Saved query + evidence + answer history.")

    if st.button("Refresh"):
        st.session_state["threads_refresh"] = True

    threads = _load_threads()
    if not threads:
        st.info("No threads yet. Use **Ask** to run a query and save it as a thread.")
    else:
        for t in threads:
            q = t.get("query", "")
            q_display = (q[:80] + "...") if len(q) > 80 else q
            with st.expander(f"**{q_display}** — {t['thread_id']}", expanded=False):
                st.markdown("**Query:**")
                st.write(t["query"])
                st.markdown("**Answer:**")
                st.markdown(t["answer"])
                st.markdown("**Retrieved chunks:**")
                for c in t.get("retrieved_chunks", []):
                    st.caption(f"{c.get('chunk_id')} ({c.get('source_id')})")
                st.session_state[f"thread_{t['thread_id']}"] = t

# --- Page: Artifacts ---
elif page == "Artifacts":
    st.header("Research artifacts")
    st.markdown("Generate and export evidence tables from saved threads.")

    threads = _load_threads()
    if not threads:
        st.info("No threads yet. Save a thread from **Ask** first.")
    else:
        thread_options = {f"{t['thread_id']}: {(t.get('query','')[:60] + '...') if len(t.get('query','')) > 60 else t.get('query','')}" : t for t in threads}
        selected_label = st.selectbox("Select a thread", list(thread_options.keys()))
        selected_thread = thread_options[selected_label] if selected_label else None

        if selected_thread and st.button("Generate evidence table"):
            rows, md, csv_str, html_str = _build_evidence_table(selected_thread)
            st.markdown("### Evidence table preview")
            if not rows:
                st.info("No evidence rows could be extracted from this thread (answer may lack inline citations).")
            else:
                st.markdown(md)
                col1, col2, col3, _ = st.columns(4)
                with col1:
                    st.download_button(
                        "Download Markdown",
                        data=md,
                        file_name="evidence_table.md",
                        mime="text/markdown",
                    )
                with col2:
                    st.download_button(
                        "Download CSV",
                        data=csv_str,
                        file_name="evidence_table.csv",
                        mime="text/csv",
                    )
                with col3:
                    st.download_button(
                        "Download HTML (print to PDF)",
                        data=html_str,
                        file_name="evidence_table.html",
                        mime="text/html",
                    )
                st.caption("For PDF: download HTML → open in browser → File → Print → Save as PDF.")

# --- Page: Evaluation ---
elif page == "Evaluation":
    st.header("Evaluation")
    st.markdown("Run the evaluation query set and view summary metrics. Or load an existing eval run.")

    logs_dir = REPO_ROOT / "logs"
    eval_logs = sorted(logs_dir.glob("eval_run_*.jsonl"), reverse=True) if logs_dir.exists() else []

    if eval_logs:
        log_options = [str(p.name) for p in eval_logs]
        selected_log = st.selectbox("Select eval log to summarize", log_options, index=0)
        if st.button("Summarize selected log"):
            path = logs_dir / selected_log
            summary, md = _get_eval_summary(path)
            if summary is not None:
                st.markdown(md)
            else:
                st.warning(md)
    else:
        st.info("No eval logs found. Run evaluation from the command line: `make eval`")

    st.markdown("---")
    st.markdown("### Run evaluation (CLI)")
    st.code("make eval   # or: python -m src.eval.run_eval", language="bash")
    st.markdown("Run from terminal. Evaluation takes a few minutes (23 queries, LLM calls). Results appear in `logs/eval_run_*.jsonl`.")
