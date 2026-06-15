import os
import streamlit as st
from dotenv import load_dotenv
import config
from analyzer_engine import ResumeAnalyzerEngine

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="Estimated Resume Compatibility Analyzer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App Title & Description
st.title("🛡️ Estimated Resume Compatibility Analyzer")
st.write("Match your resume with any target job description and get optimization suggestions powered by AI.")

# Configure API status warning
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("⚠️ GOOGLE_API_KEY environment variable is missing. Please configure your API key in the `.env` file to start analyzing resumes.")
    st.stop()

# Initialize the modular analysis engine
@st.cache_resource
def get_engine():
    return ResumeAnalyzerEngine()

engine = get_engine()

# Initialize session state for persistent results
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "job_description" not in st.session_state:
    st.session_state.job_description = ""
if "current_step" not in st.session_state:
    st.session_state.current_step = 1

# Progress Tracker CSS & HTML
def render_step_tracker():
    step = st.session_state.current_step
    
    steps = [
        {"num": 1, "label": "Upload Resume"},
        {"num": 2, "label": "AI Parsing"},
        {"num": 3, "label": "Section Analysis"},
        {"num": 4, "label": "STAR Optimizer"}
    ]
    
    steps_html = []
    for i, s in enumerate(steps):
        s_num = s["num"]
        label = s["label"]
        
        # Determine step state styles
        if s_num < step:
            # Completed
            circle_style = "background-color: #10b981; color: white; border: 2px solid #10b981;"
            circle_content = "✓"
            label_style = "color: #10b981; font-weight: 600;"
        elif s_num == step:
            # Active
            circle_style = "background-color: #3b82f6; color: white; border: 2px solid #3b82f6; box-shadow: 0 0 12px rgba(59, 130, 246, 0.6);"
            circle_content = str(s_num)
            label_style = "color: #3b82f6; font-weight: bold;"
        else:
            # Pending
            circle_style = "background-color: #1e293b; color: #64748b; border: 2px solid #334155;"
            circle_content = str(s_num)
            label_style = "color: #64748b;"
            
        step_item = f"""
        <div style="display: flex; flex-direction: column; align-items: center; flex: 1; position: relative;">
            <div style="width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 15px; font-weight: bold; margin-bottom: 8px; transition: all 0.3s ease; {circle_style}">
                {circle_content}
            </div>
            <span style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; text-align: center; {label_style}">{label}</span>
        </div>
        """
        steps_html.append(step_item)
        
        if i < len(steps) - 1:
            line_color = "#10b981" if s_num < step else "#334155"
            line_html = f"""
            <div style="flex: 1; height: 3px; background-color: {line_color}; margin-bottom: 24px; min-width: 20px;"></div>
            """
            steps_html.append(line_html)
            
    tracker_html = f"""
    <div style="display: flex; align-items: center; justify-content: space-between; margin: 10px 0 35px 0; background-color: #1e293b; padding: 20px; border-radius: 10px; border: 1px solid #334155; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
        {"".join(steps_html)}
    </div>
    """
    st.markdown(tracker_html, unsafe_allow_html=True)

render_step_tracker()

# Sidebar settings info
with st.sidebar:
    st.markdown("### ⚙️ Engine Configurations")
    st.markdown(f"**Model In Use:** `{config.GEMINI_MODEL}`")
    st.markdown("---")
    st.markdown("#### ⚖️ Scoring Weights")
    st.markdown(f"- **Keyword Alignment:** `{int(config.WEIGHT_KEYWORD_ALIGNMENT * 100)}%`")
    st.markdown(f"- **Experience Relevance:** `{int(config.WEIGHT_EXPERIENCE_RELEVANCE * 100)}%`")
    st.markdown(f"- **Formatting & Structure:** `{int(config.WEIGHT_FORMATTING_HEALTH * 100)}%`")
    st.markdown("---")
    st.caption("Weights are automatically normalized and can be configured via environment variables in the `.env` file.")
    
    # Render Navigation links in the sidebar if results are present
    if st.session_state.analysis_results:
        st.markdown("### 🗺️ Navigation")
        if st.button("Step 1: Upload & Input", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()
        if st.button("Step 3: Section Analysis", use_container_width=True):
            st.session_state.current_step = 3
            st.rerun()
        if st.button("Step 4: STAR Optimizer", use_container_width=True):
            st.session_state.current_step = 4
            st.rerun()

# Step 1: Upload & Input Job Description
if st.session_state.current_step == 1:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📁 1. Upload Resume")
        uploaded_file = st.file_uploader("Upload your resume in PDF format:", type=["pdf"])
    with col2:
        st.markdown("### 💼 2. Target Job Description")
        st.session_state.job_description = st.text_area(
            "Enter target Job Description:",
            value=st.session_state.job_description,
            placeholder="Paste the job description or target role requirements here...",
            height=180
        )
    
    # Analysis trigger button
    st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)
    trigger_col_1, trigger_col_2 = st.columns([1, 4])
    with trigger_col_1:
        btn_disabled = uploaded_file is None
        analyze_btn = st.button("Analyze Resume", disabled=btn_disabled, use_container_width=True)
        
    if uploaded_file is None:
        st.info("💡 Please upload a PDF resume in section 1 to begin.")
        
    # Triggering analysis
    if analyze_btn and uploaded_file:
        # Save uploaded file locally for parsing
        with open("uploaded_resume.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Visually set step to AI Parsing (2) on frontend first
        st.session_state.current_step = 2
        st.rerun()

# Step 2: AI Parsing (Transitional Loading View)
elif st.session_state.current_step == 2:
    st.markdown("### 🤖 Running AI Parsing & Analysis")
    with st.spinner("Analyzing resume content against job description details..."):
        try:
            # Extract text and run engine compatibility evaluation
            resume_text = engine.extract_text_from_pdf("uploaded_resume.pdf")
            if not resume_text.strip():
                st.error("Could not extract any readable text from the uploaded PDF. Please make sure the file is not corrupted.")
                st.session_state.current_step = 1
            else:
                results = engine.analyze_compatibility(resume_text, st.session_state.job_description)
                if "error" in results:
                    st.error(results["error"])
                    st.session_state.current_step = 1
                else:
                    st.session_state.analysis_results = results
                    st.session_state.current_step = 3
                    st.success("Analysis complete!")
                    st.rerun()
        except Exception as e:
            st.error(f"An unexpected error occurred during processing: {str(e)}")
            st.session_state.current_step = 1

# Step 3: Section Analysis
elif st.session_state.current_step == 3:
    if not st.session_state.analysis_results:
        st.warning("⚠️ No analysis results found. Redirecting to Step 1.")
        st.session_state.current_step = 1
        st.rerun()
        
    res = st.session_state.analysis_results
    
    # ── Score Header ───────────────────────────────────
    st.markdown("## 📊 Compatibility Analysis Results")
    
    score_col, details_col = st.columns([1, 2])
    
    with score_col:
        # Determine gauge color based on score
        score = res.get("overall_compatibility_score", 0)
        if score >= 75:
            gauge_color = "#10b981" # Emerald Green
        elif score >= 50:
            gauge_color = "#f59e0b" # Amber Orange
        else:
            gauge_color = "#ef4444" # Red
            
        st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; flex-direction: column; padding: 20px;">
          <div style="position: relative; width: 170px; height: 170px; border-radius: 50%; background: conic-gradient({gauge_color} {score}%, #334155 0); display: flex; justify-content: center; align-items: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <div style="position: absolute; width: 136px; height: 136px; border-radius: 50%; background: #0f172a; display: flex; justify-content: center; align-items: center; color: white; font-size: 30px; font-weight: bold; flex-direction: column;">
              <span>{score}%</span>
              <span style="font-size: 10px; color: #94a3b8; font-weight: normal; margin-top: 4px; text-transform: uppercase; letter-spacing: 1px;">Compatibility</span>
            </div>
          </div>
          <p style="margin-top: 15px; font-size: 14px; font-weight: bold; color: {gauge_color}; text-align: center;">
            Estimated Compatibility Rating
          </p>
        </div>
        """, unsafe_allow_html=True)
        
    with details_col:
        st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)
        # Visual metric cards for sub-scores
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.markdown(f"""
            <div style="background-color: #1e293b; padding: 18px; border-radius: 10px; text-align: center; border-left: 5px solid #3b82f6; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
              <p style="margin: 0; font-size: 13px; color: #94a3b8; text-transform: uppercase; font-weight: bold;">Skills Match</p>
              <p style="margin: 5px 0 0 0; font-size: 26px; font-weight: bold; color: #f8fafc;">{res.get('keyword_score', 0)}%</p>
            </div>
            """, unsafe_allow_html=True)
        with m_col2:
            st.markdown(f"""
            <div style="background-color: #1e293b; padding: 18px; border-radius: 10px; text-align: center; border-left: 5px solid #a855f7; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
              <p style="margin: 0; font-size: 13px; color: #94a3b8; text-transform: uppercase; font-weight: bold;">Experience</p>
              <p style="margin: 5px 0 0 0; font-size: 26px; font-weight: bold; color: #f8fafc;">{res.get('experience_score', 0)}%</p>
            </div>
            """, unsafe_allow_html=True)
        with m_col3:
            st.markdown(f"""
            <div style="background-color: #1e293b; padding: 18px; border-radius: 10px; text-align: center; border-left: 5px solid #14b8a6; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
              <p style="margin: 0; font-size: 13px; color: #94a3b8; text-transform: uppercase; font-weight: bold;">Formatting</p>
              <p style="margin: 5px 0 0 0; font-size: 26px; font-weight: bold; color: #f8fafc;">{res.get('formatting_score', 0)}%</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<div style='padding-top: 15px;'></div>", unsafe_allow_html=True)
        st.info("📌 Note: The Estimated Compatibility Score represents an AI-driven comparison with target roles. Actual ATS systems vary by employer and system configuration.")

    # ── Skill Gap Matrix ──────────────────────────────────
    st.markdown("### 🔀 Skill Match Gap Matrix")
    sk_col1, sk_col2 = st.columns(2)
    
    with sk_col1:
        st.markdown("#### ✅ Matched Skills & Technologies")
        matched = res.get("matched_skills", [])
        if not matched:
            st.caption("No matching target skills identified.")
        else:
            matched_badges = "".join([
                f'<span style="background-color: rgba(16, 185, 129, 0.12); color: #10b981; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin: 4px; display: inline-block; border: 1px solid rgba(16, 185, 129, 0.3);">{skill}</span>'
                for skill in matched
            ])
            st.markdown(matched_badges, unsafe_allow_html=True)
            
    with sk_col2:
        st.markdown("#### ❌ Missing Skills & Keywords")
        missing = res.get("missing_skills", [])
        if not missing:
            st.caption("No missing keywords identified.")
        else:
            missing_badges = "".join([
                f'<span style="background-color: rgba(245, 158, 11, 0.12); color: #f59e0b; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin: 4px; display: inline-block; border: 1px solid rgba(245, 158, 11, 0.3);">{skill}</span>'
                for skill in missing
            ])
            st.markdown(missing_badges, unsafe_allow_html=True)

    # ── Actionable Recommendations ──────────────────────────
    st.markdown("<div style='padding-top: 15px;'></div>", unsafe_allow_html=True)
    st.markdown("### ⚙️ Actionable Optimization Recommendations")
    
    tab1, tab2, tab3 = st.tabs([
        "📁 Formatting & Layout", 
        "💼 Section Improvements", 
        "🎓 Course Suggestions"
    ])
    
    with tab1:
        format_issues = res.get("formatting_issues", [])
        if not format_issues:
            st.success("🎉 No structural or layout issues detected. Good job!")
        else:
            st.markdown("#### 🛠️ Structural Enhancements Required")
            for issue in format_issues:
                st.markdown(f"- ⚠️ **{issue}**")
                
    with tab2:
        suggestions = res.get("suggestions", [])
        if not suggestions:
            st.success("🎉 No content deficiencies found in specific sections!")
        else:
            st.markdown("#### 💼 Section-by-Section Content Refinement")
            for idx, sugg in enumerate(suggestions):
                st.markdown(f"##### **{idx+1}. {sugg.get('section', 'General')} Section**")
                st.markdown(f"- **Identified Deficiency:** {sugg.get('issue')}")
                st.markdown(f"- **Suggested Action:**")
                st.info(sugg.get('remediation'))
                st.markdown("<div style='padding-top: 5px; border-bottom: 1px solid #334155; margin-bottom: 15px;'></div>", unsafe_allow_html=True)
                
    with tab3:
        courses = res.get("course_recommendations", [])
        if not courses:
            st.success("🎉 All core keywords match! No additional courses suggested.")
        else:
            st.markdown("#### 🎓 Recommended Learning Roadmap")
            for course in courses:
                st.markdown(f"""
                <div style="background-color: #1e293b; padding: 12px 18px; border-radius: 8px; border-left: 4px solid #10b981; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                  <p style="margin: 0; font-size: 14px; font-weight: bold; color: #f8fafc;">{course.get('course_title')}</p>
                  <p style="margin: 3px 0 0 0; font-size: 12px; color: #94a3b8;">Skill Area: <b>{course.get('skill')}</b> | Platform: <i>{course.get('platform')}</i></p>
                </div>
                """, unsafe_allow_html=True)

    # Navigation buttons
    st.markdown("---")
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button("⬅️ Adjust Inputs / Re-upload", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()
    with nav_col2:
        if st.button("➡️ Proceed to STAR Optimizer", use_container_width=True):
            st.session_state.current_step = 4
            st.rerun()

# Step 4: STAR Optimizer
elif st.session_state.current_step == 4:
    if not st.session_state.analysis_results:
        st.warning("⚠️ No analysis results found. Redirecting to Step 1.")
        st.session_state.current_step = 1
        st.rerun()
        
    res = st.session_state.analysis_results
    score = res.get("overall_compatibility_score", 0)
    format_issues = res.get("formatting_issues", [])
    courses = res.get("course_recommendations", [])
    
    st.markdown("## 📝 STAR-method Experience Optimizer")
    st.write("Paste a single bullet point from your resume to rewrite it to highlight impact, metrics, and integrate target skills.")
    
    with st.form("opt_form", clear_on_submit=False):
        bullet_input = st.text_input("Enter bullet point to optimize:", placeholder="e.g., Assisted in developing classification models for forecasting data")
        submitted = st.form_submit_button("Optimize Bullet Point", use_container_width=True)
        
        if submitted and bullet_input:
            if not bullet_input.strip():
                st.warning("Please enter some text to optimize.")
            else:
                with st.spinner("Optimizing bullet point using STAR framework..."):
                    optimized_text = engine.optimize_bullet_point(bullet_input, res.get("missing_skills", []))
                    st.markdown("**Original Bullet Point:**")
                    st.caption(bullet_input)
                    st.markdown("**AI Optimized Bullet Point:**")
                    st.success(optimized_text)

    # Construction of markdown report
    report_text = f"""# Estimated Resume Compatibility Report
## Target JD Match: {score}%

### 1. Dimension Breakdown
- **Skills Match:** {res.get('keyword_score', 0)}%
- **Experience:** {res.get('experience_score', 0)}%
- **Formatting:** {res.get('formatting_score', 0)}%

### 2. Skill Matrix
- **Matched Skills:** {', '.join(res.get('matched_skills', []))}
- **Missing Skills:** {', '.join(res.get('missing_skills', []))}

### 3. Formatting & Structural Feedback
{chr(10).join([f'- {issue}' for issue in format_issues]) if format_issues else 'No issues detected.'}

### 4. Course Recommendations
{chr(10).join([f'- **{c.get("course_title")}** ({c.get("platform")}) for {c.get("skill")}' for c in courses]) if courses else 'No courses recommended.'}
"""

    st.markdown("<div style='padding-top: 25px;'></div>", unsafe_allow_html=True)
    st.download_button(
        label="📥 Download Detailed Analysis Report (Markdown)",
        data=report_text,
        file_name="resume_compatibility_report.md",
        mime="text/markdown",
        use_container_width=True
    )

    # Navigation buttons
    st.markdown("---")
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button("⬅️ Back to Analysis Results", use_container_width=True):
            st.session_state.current_step = 3
            st.rerun()
    with nav_col2:
        if st.button("🔄 Start New Scan", use_container_width=True):
            st.session_state.analysis_results = None
            st.session_state.current_step = 1
            st.rerun()

# Footer
st.markdown("---")
st.markdown(
    f"""<p style='text-align: center;'>Powered by <b>Streamlit</b> and <b>Google Gemini AI</b> | Model: <code>{config.GEMINI_MODEL}</code> | Developed by <a href="https://www.linkedin.com/in/dutta-sujoy/" target="_blank" style='text-decoration: none; color: #3b82f6;'><b>Sujoy Dutta</b></a></p>""",
    unsafe_allow_html=True
)
