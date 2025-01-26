import streamlit as st
from internal_link_optimizer import AsyncScraper, InternalLinkOptimizer
import pandas as pd
import asyncio

st.set_page_config(page_title="Internal Link Optimizer", layout="wide")

# Sidebar Controls
with st.sidebar:
    st.header("Settings")
    openai_key = st.text_input("OpenAI API Key", type="password")
    max_links = st.slider("Max Links Per Page", 1, 10, 3)
    exclude_patterns = st.text_area("Exclude URL Patterns (regex)", "/login\n/signup\n/author")
    base_url = st.text_input("Website Base URL", "https://example.com")

# Main Interface
st.title("🚀 Internal Link Optimizer")
uploaded_file = st.file_uploader("Upload SEO Report (CSV)", type=["csv"])

if uploaded_file and base_url:
    df = pd.read_csv(uploaded_file)
    optimizer = InternalLinkOptimizer(openai_api_key=openai_key)
    
    with st.status("Processing...", expanded=True) as status:
        # Step 1: Scrape Content
        st.write("🕸️ Scraping page content...")
        scraper = AsyncScraper()
        scraped_content = asyncio.run(scraper.scrape_urls(base_url, df['URL'].tolist()))
        df['Body Content'] = df['URL'].map(scraped_content)
        
        # Step 2: Analysis
        st.write("🔍 Analyzing content...")
        results = asyncio.run(optimizer.analyze_with_context(df, max_links=max_links))
        
        # Step 3: Filtering
        st.write("🎯 Prioritizing recommendations...")
        filtered = results[
            (results['Priority Score'] > 0.7) & 
            (results['Similarity Score'] > 0.65)
        ].head(500)
        
        status.update(label="Analysis complete!", state="complete")

    # Results Display
    st.subheader(f"Top {len(filtered)} Recommendations")
    st.dataframe(
        filtered.sort_values('Priority Score', ascending=False),
        column_config={
            "Priority Score": st.column_config.ProgressColumn(
                format="%.2f", 
                min_value=0, 
                max_value=filtered['Priority Score'].max()
            )
        },
        use_container_width=True
    )
    
    # Download
    st.download_button(
        label="📥 Download CSV",
        data=filtered.to_csv(index=False),
        file_name="linking_suggestions.csv"
    )
