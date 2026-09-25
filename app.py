import os
import re
from typing import List, Dict, Any

import streamlit as st
from dotenv import load_dotenv

from agents import build_search_agent, writer_chain, critic_chain
from tools import scrape_url

load_dotenv()


st.set_page_config(
    page_title="Research Intelligence Console",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --bg: #101526;
        --panel: #12151d;
        --panel-alt: #161a24;
        --surface: #1a1f2b;
        --border: #262b3a;
        --border-soft: #1e2330;
        --text: #f1f3f9;
        --muted: #939bb0;
        --accent: #7c8cff;
        --accent-strong: #a3b0ff;
        --accent-soft: rgba(124, 140, 255, 0.14);
        --success: #34d399;
        --warning: #f5a94e;
        --shadow: rgba(0, 0, 0, 0.55);
        --glow: rgba(124, 140, 255, 0.18);
    }

    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background: radial-gradient(1200px 600px at 15% -10%, rgba(124, 140, 255, 0.18) 0%, rgba(124, 140, 255, 0) 60%),
                    linear-gradient(180deg, #151b31 0%, #11182a 45%, #0d1322 100%);
        color: var(--text);
        font-family: 'Inter', sans-serif;
    }

    /* Neutralize Streamlit's native top toolbar so it can't render as a
       stray light bar clashing with the dark theme. */
    [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"] {
        background: var(--bg) !important;
        background-image: none !important;
    }

    /* Force every native text element (widget labels, st.write, captions,
       list items) to the dark-theme palette, regardless of the viewer's
       OS/browser color-scheme preference. */
    [data-testid="stAppViewContainer"] p,
    [data-testid="stAppViewContainer"] li,
    [data-testid="stAppViewContainer"] span,
    [data-testid="stAppViewContainer"] label,
    [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] li,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    [data-testid="stWidgetLabel"] p {
        color: var(--text) !important;
    }

    [data-testid="stCaptionContainer"], .stCaption, small {
        color: var(--muted) !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #171e34 0%, #10172a 100%) !important;
        border-right: 1px solid var(--border);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    .metric-card {
        background: linear-gradient(180deg, #161a24 0%, #10131a 100%);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1rem 1.1rem;
        box-shadow: 0 18px 36px var(--shadow), inset 0 1px 0 rgba(255, 255, 255, 0.04);
    }

    .glass-panel {
        background: linear-gradient(180deg, #151923 0%, #10131a 100%);
        border: 1px solid var(--border);
        border-radius: 18px;
        box-shadow: 0 20px 44px var(--shadow), inset 0 1px 0 rgba(255, 255, 255, 0.04);
        padding: 1rem 1.1rem;
    }

    h1, h2, h3, h4 {
        color: var(--text) !important;
        letter-spacing: -0.03em;
    }

    h1 {
        text-shadow: 0 0 40px var(--glow);
    }

    .stTabs [role="tablist"] {
        gap: 0.6rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1rem;
    }

    .stTabs [role="tab"] {
        background: var(--panel);
        border: 1px solid var(--border);
        border-bottom: none;
        border-radius: 10px 10px 0 0;
        padding: 0.65rem 0.9rem;
        color: var(--muted);
    }

    .stTabs [role="tab"][aria-selected="true"] {
        background: var(--accent-soft);
        color: var(--accent-strong) !important;
        border-color: rgba(124, 140, 255, 0.4);
    }

    .stAlert {
        border-radius: 14px;
    }

    .stButton > button {
        background: linear-gradient(180deg, #8b98ff 0%, #5a67e8 100%) !important;
        border: none !important;
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.92rem;
        padding: 0.6rem 0.9rem;
        box-shadow: 0 14px 28px rgba(90, 103, 232, 0.38);
        white-space: nowrap;
    }

    .stButton > button p, .stButton > button span, .stButton > button div {
        color: #08090d !important;
        font-weight: 700;
    }

    .stButton > button:hover {
        background: linear-gradient(180deg, #9ba6ff 0%, #6c78ef 100%) !important;
        box-shadow: 0 16px 34px rgba(90, 103, 232, 0.5);
        filter: none;
    }

    .stButton > button[kind="secondary"] {
        background: var(--panel-alt) !important;
        border: 1px solid var(--border) !important;
        box-shadow: none;
    }

    .stButton > button[kind="secondary"] p,
    .stButton > button[kind="secondary"] span,
    .stButton > button[kind="secondary"] div {
        color: var(--accent-strong) !important;
        font-weight: 600;
    }

    .stTextInput input, [data-testid="stTextInput"] div[data-baseweb="input"] {
        background: var(--panel-alt) !important;
        color: var(--text) !important;
        border-color: var(--border) !important;
        border-radius: 10px;
    }

    .stTextInput input::placeholder {
        color: var(--muted) !important;
        opacity: 1;
    }

    [data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 0.2rem var(--glow);
    }

    hr {
        border-color: var(--border) !important;
    }

    a {
        color: var(--accent-strong) !important;
        text-decoration: none;
    }

    a:hover {
        text-decoration: underline;
        color: #c3caff !important;
    }

    .source-link {
        display: block;
        padding: 0.7rem 0.8rem;
        border: 1px solid var(--border);
        border-radius: 10px;
        background: var(--panel-alt);
        margin: 0.4rem 0;
    }

    .info-pill {
        display: inline-block;
        background: var(--accent-soft);
        border: 1px solid rgba(124, 140, 255, 0.35);
        border-radius: 999px;
        padding: 0.32rem 0.7rem;
        font-size: 0.74rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    .info-pill, .info-pill * {
        color: var(--accent-strong) !important;
    }

    div[data-baseweb="input"] > div:last-child {
        display: none !important;
    }

    [data-testid="stAlert"] p, [data-testid="stAlert"] span {
        color: inherit !important;
    }

    code, .stCode, [data-testid="stCodeBlock"] {
        background: var(--panel-alt) !important;
        border: 1px solid var(--border) !important;
        color: #d7dcef !important;
    }

    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }

    ::-webkit-scrollbar-track {
        background: var(--bg);
    }

    ::-webkit-scrollbar-thumb {
        background: #2a3042;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #363d54;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def ensure_requirements() -> None:
    missing = []
    if not os.getenv("GROQ_API_KEY"):
        missing.append("GROQ_API_KEY")
    if not os.getenv("TAVILY_API_KEY"):
        missing.append("TAVILY_API_KEY")

    if missing:
        st.sidebar.warning(
            "Missing environment variables: " + ", ".join(missing) + ". Add them to the .env file before generating research."
        )


def parse_search_results(search_text: str) -> List[Dict[str, str]]:
    if not search_text:
        return []

    blocks = [block.strip() for block in search_text.split("\n----\n") if block.strip()]
    results: List[Dict[str, str]] = []

    for block in blocks:
        title_match = re.search(r"Title:\s*(.*?)(?:\n|$)", block)
        url_match = re.search(r"URL:\s*(https?://\S+)", block)
        snippet_match = re.search(r"Snippet:\s*(.*)", block, re.S)

        title = title_match.group(1).strip() if title_match else "Untitled result"
        url = url_match.group(1).strip() if url_match else "#"
        snippet = snippet_match.group(1).strip() if snippet_match else "No summary available."

        results.append({
            "title": title,
            "url": url.rstrip(".,;)") if url != "#" else url,
            "snippet": snippet.strip()
        })

    return results


def extract_urls(text: str) -> List[str]:
    if not text:
        return []
    urls = re.findall(r"https?://[^\s)\]>]+", text)
    unique: List[str] = []
    for url in urls:
        cleaned = url.rstrip(".,;!?)")
        if cleaned not in unique:
            unique.append(cleaned)
    return unique


def invoke_search_agent(topic: str) -> str:
    search_agent = build_search_agent()
    response = search_agent.invoke({
        "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
    })

    if isinstance(response, dict) and "messages" in response and response["messages"]:
        return str(response["messages"][-1].content)

    return str(response)


def resolve_best_url(search_text: str) -> str:
    urls = extract_urls(search_text)
    if not urls:
        return ""
    return urls[0]


def invoke_reader_agent(topic: str, search_text: str) -> str:
    url = resolve_best_url(search_text)
    if not url:
        return "No valid URL was found in the search results to scrape."

    try:
        result = scrape_url.invoke({"url": url})
        return str(result)
    except Exception as exc:
        return f"Could not scrape the selected source: {exc}"


def run_research_process(topic: str) -> Dict[str, Any]:
    search_results = invoke_search_agent(topic)
    scraped_content = invoke_reader_agent(topic, search_results)

    combined_research = (
        f"SEARCH RESULTS:\n{search_results}\n\n"
        f"DETAILED SCRAPED CONTENT:\n{scraped_content}"
    )

    report = writer_chain.invoke({
        "topic": topic,
        "research": combined_research,
    })

    feedback = critic_chain.invoke({
        "report": report,
    })

    return {
        "search_results": search_results,
        "scraped_content": scraped_content,
        "report": report,
        "feedback": feedback,
    }


def render_search_results(search_text: str) -> None:
    results = parse_search_results(search_text)

    if not results:
        st.info("No structured search results were returned. The raw response is shown below.")
        st.code(search_text[:5000], language="text")
        return

    for item in results:
        with st.container():
            st.markdown(
                f"""
                <div class="glass-panel">
                    <div style="display:flex; justify-content:space-between; align-items:center; gap:1rem; flex-wrap:wrap;">
                        <h4 style="margin:0;">{item['title']}</h4>
                    </div>
                    <div style="margin-top:0.55rem;">
                        <a href="{item['url']}" target="_blank" rel="noopener noreferrer">{item['url']}</a>
                    </div>
                    <p style="margin-top:0.8rem; color:var(--muted); line-height:1.6;">{item['snippet']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_report(report_text: str) -> None:
    st.markdown(report_text)


def render_feedback(feedback_text: str) -> None:
    st.markdown(feedback_text)


def main() -> None:
    ensure_requirements()

    st.title("Research Intelligence Console")
    st.caption("Web research, source extraction, briefing generation, and critical review in one workflow.")

    with st.sidebar:
        st.header("Research Control")
        topic = st.text_input(
            "Target topic",
            value="",
            help=None,
            label_visibility="collapsed",
        )

        col1, col2 = st.columns(2)
        with col1:
            generate = st.button("Generate report", use_container_width=True)
        with col2:
            clear = st.button("Clear", use_container_width=True, type="secondary")

        st.markdown("---")
        st.subheader("Workflow")
        st.write("1. Search the web")
        st.write("2. Extract the most relevant source")
        st.write("3. Draft a professional report")
        st.write("4. Critique the report")

    if clear:
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    if generate and not topic.strip():
        st.warning("Please enter a research topic before generating the report.")
        return

    if generate and topic.strip():
        with st.spinner("Gathering sources and synthesizing findings..."):
            result = run_research_process(topic.strip())
        st.session_state["research_result"] = result

    if "research_result" not in st.session_state:
        st.info("Enter a topic on the left and click Generate report to begin.")
        st.markdown(
            """
            ### Research briefing overview
            This interface combines four steps in a single professional research workflow:
            - source discovery
            - web content extraction
            - structured report writing
            - critical review
            """
        )
        return

    result = st.session_state["research_result"]
    sources = extract_urls(result["report"]) + extract_urls(result["search_results"])
    unique_sources = []
    for item in sources:
        if item not in unique_sources:
            unique_sources.append(item)

    st.markdown("<div class='info-pill'>Research session active</div>", unsafe_allow_html=True)

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.markdown(
            """
            <div class='metric-card'>
                <div style='color:var(--muted); font-size:0.75rem; font-weight:600; text-transform:uppercase;'>Search result count</div>
                <div style='font-size:2rem; font-weight:800; margin-top:0.4rem;'>%s</div>
            </div>
            """ % (len(parse_search_results(result["search_results"])),),
            unsafe_allow_html=True,
        )
    with metric_col2:
        st.markdown(
            """
            <div class='metric-card'>
                <div style='color:var(--muted); font-size:0.75rem; font-weight:600; text-transform:uppercase;'>Extracted sources</div>
                <div style='font-size:2rem; font-weight:800; margin-top:0.4rem;'>%s</div>
            </div>
            """ % (len(unique_sources),),
            unsafe_allow_html=True,
        )
    with metric_col3:
        report_length = len(result["report"].split())
        st.markdown(
            """
            <div class='metric-card'>
                <div style='color:var(--muted); font-size:0.75rem; font-weight:600; text-transform:uppercase;'>Report length</div>
                <div style='font-size:2rem; font-weight:800; margin-top:0.4rem;'>%s</div>
            </div>
            """ % (report_length,),
            unsafe_allow_html=True,
        )

    st.markdown("---")

    st.subheader(f"Topic: {topic.strip()}")
    st.write(
        "This workflow searched for recent information, prioritized the most relevant source, synthesized a structured report, and then reviewed the output for quality and clarity."
    )

    source_links = "\n".join(f"- [{url}]({url})" for url in unique_sources[:6])
    st.markdown("### Source references")
    st.markdown(source_links or "No source URLs were extracted.")

    st.markdown("---")
    st.subheader("Final research brief")
    render_report(result["report"])

    st.markdown("---")
    st.subheader("Critic review")
    render_feedback(result["feedback"])


if __name__ == "__main__":
    main()
