import streamlit as st
import google.generativeai as genai
import PyPDF2
import io
import json
import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configure the page
st.set_page_config(page_title="AI Career Advisor", page_icon="🚀", layout="wide")

# Initialize Gemini AI
genai.configure(api_key="AIzaSyBHiuLjXp3gtW8QK6xqfJgaHtL4APKfGaQ")

# Initialize session state
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = ""
if 'analysis' not in st.session_state:
    st.session_state.analysis = {}
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = []

# Helper functions
def get_gemini_response(prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text

def extract_text_from_pdf(uploaded_file):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def analyze_resume(resume_text):
    prompt = f"""
    Analyze this resume and extract key information:
    {resume_text}
    
    Return a JSON object with:
    1. "skills": list of technical and soft skills
    2. "experience": summary of work experience
    3. "education": educational background
    4. "strengths": 3-5 key strengths
    5. "improvement_areas": 3-5 areas for improvement
    6. "current_role": current or most recent job title
    7. "experience_years": years of experience
    
    Format the response as valid JSON only.
    """
    try:
        response = get_gemini_response(prompt)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {"skills": [], "experience": "", "education": "", "strengths": [], "improvement_areas": []}
    except:
        return {"skills": [], "experience": "", "education": "", "strengths": [], "improvement_areas": []}

def generate_recommendations(analysis):
    prompt = f"""
    Based on this resume analysis: {json.dumps(analysis)}
    
    Generate career recommendations with:
    1. "next_role": suggested next career move
    2. "reason": why this role is a good fit
    3. "skills_match": percentage match with current skills (0-100)
    4. "skills_to_develop": list of skills needed for this role
    5. "learning_resources": suggested resources to acquire these skills
    6. "salary_range": expected salary range for this role
    7. "job_growth": job market outlook for this role
    
    Return the response as a valid JSON array with 3 recommendations.
    """
    try:
        response = get_gemini_response(prompt)
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return []
    except:
        return []

def calculate_resume_score(analysis):
    base_score = 70
    skills = analysis.get('skills', [])
    experience = analysis.get('experience', '')
    education = analysis.get('education', '')
    
    # Score based on number of skills
    if len(skills) > 10:
        base_score += 10
    elif len(skills) > 5:
        base_score += 5
    
    # Score based on experience description
    if len(experience) > 100:
        base_score += 10
    elif len(experience) > 50:
        base_score += 5
        
    # Ensure score is between 0-100
    return min(100, base_score)

def get_job_market_data():
    return {
        "high_demand_skills": [
            "Python", "Machine Learning", "Cloud Computing", "Data Analysis", 
            "AI Development", "Cybersecurity", "DevOps", "React", "SQL"
        ],
        "growing_fields": [
            "Artificial Intelligence", "Data Science", "Cloud Engineering",
            "Cybersecurity", "Digital Marketing", "UX/UI Design"
        ],
        "salary_trends": {
            "Data Scientist": "$120,000 - $180,000",
            "Software Engineer": "$110,000 - $170,000",
            "AI Engineer": "$130,000 - $190,000",
            "Cloud Architect": "$130,000 - $200,000",
            "DevOps Engineer": "$120,000 - $180,000"
        }
    }

# UI Components
def render_header():
    st.title("🤖 AI Career Advisor")
    st.markdown("Upload your resume and get personalized career guidance for the evolving job market")
    st.markdown("---")

def render_resume_upload():
    st.header("📄 Upload Your Resume")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        with st.spinner("Extracting text from resume..."):
            resume_text = extract_text_from_pdf(uploaded_file)
            st.session_state.resume_text = resume_text
            
        with st.spinner("Analyzing resume..."):
            st.session_state.analysis = analyze_resume(resume_text)
            
        with st.spinner("Generating recommendations..."):
            st.session_state.recommendations = generate_recommendations(st.session_state.analysis)
        
        st.success("Resume analysis complete!")

def render_resume_score():
    if not st.session_state.analysis:
        return
        
    score = calculate_resume_score(st.session_state.analysis)
    
    st.header("📊 Resume Score")
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Overall Resume Score"},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightcoral"},
                {'range': [50, 80], 'color': "lightyellow"},
                {'range': [80, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✅ Strengths")
        for strength in st.session_state.analysis.get('strengths', []):
            st.success(f"• {strength}")
    
    with col2:
        st.subheader("📈 Improvement Areas")
        for area in st.session_state.analysis.get('improvement_areas', []):
            st.info(f"• {area}")

def render_skills_analysis():
    if not st.session_state.analysis:
        return
        
    skills = st.session_state.analysis.get('skills', [])
    job_market_data = get_job_market_data()
    high_demand_skills = job_market_data['high_demand_skills']
    
    matched_skills = [skill for skill in skills if skill in high_demand_skills]
    missing_skills = [skill for skill in high_demand_skills if skill not in skills]
    
    st.header("🔧 Skills Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Your Skills")
        for skill in skills:
            if skill in high_demand_skills:
                st.success(f"• {skill} ✅ (High Demand)")
            else:
                st.write(f"• {skill}")
    
    with col2:
        st.subheader("High Demand Skills You're Missing")
        for skill in missing_skills[:5]:
            st.error(f"• {skill} ⚠️")
        
        if len(missing_skills) > 5:
            st.info(f"Plus {len(missing_skills) - 5} more high-demand skills")

def render_career_recommendations():
    if not st.session_state.recommendations:
        return
        
    st.header("🚀 Career Recommendations")
    
    for i, rec in enumerate(st.session_state.recommendations):
        with st.expander(f"{rec.get('next_role', 'Unknown Role')} - {rec.get('skills_match', 0)}% Match", expanded=i==0):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader(rec.get('next_role', ''))
                st.write(f"**Why this role:** {rec.get('reason', '')}")
                
                st.write("**Skills to Develop:**")
                for skill in rec.get('skills_to_develop', [])[:3]:
                    st.write(f"- {skill}")
                
                st.write("**Learning Resources:**")
                for resource in rec.get('learning_resources', [])[:2]:
                    st.write(f"- {resource}")
            
            with col2:
                st.metric("Salary Range", rec.get('salary_range', ''))
                st.metric("Job Growth", rec.get('job_growth', ''))
                
                # Skills match gauge
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = rec.get('skills_match', 0),
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Skills Match"},
                    gauge = {
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightcoral"},
                            {'range': [50, 80], 'color': "lightyellow"},
                            {'range': [80, 100], 'color': "lightgreen"}
                        ]
                    }
                ))
                fig.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig, use_container_width=True)

def render_job_market_insights():
    job_market_data = get_job_market_data()
    
    st.header("📈 Job Market Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("High Demand Skills")
        for skill in job_market_data['high_demand_skills']:
            st.write(f"• {skill}")
    
    with col2:
        st.subheader("Growing Fields")
        for field in job_market_data['growing_fields']:
            st.write(f"• {field}")
    
    st.subheader("Salary Trends")
    salary_data = []
    for role, salary in job_market_data['salary_trends'].items():
        # Extract average salary for visualization
        avg_salary = int(''.join(filter(str.isdigit, salary.split('-')[0]))) / 1000
        salary_data.append({'Role': role, 'Average Salary (K)': avg_salary})
    
    if salary_data:
        df = pd.DataFrame(salary_data)
        fig = px.bar(df, x='Role', y='Average Salary (K)', title='Average Salary by Role')
        st.plotly_chart(fig, use_container_width=True)

def render_career_path():
    if not st.session_state.analysis:
        return
        
    current_role = st.session_state.analysis.get('current_role', 'Current Position')
    
    st.header("🧭 Career Path Projection")
    
    # Create a simple career path visualization
    path_data = {
        'Stage': ['Current', 'Next 1-2 Years', 'Next 3-5 Years', 'Future'],
        'Role': [
            current_role,
            st.session_state.recommendations[0]['next_role'] if st.session_state.recommendations else 'Mid-level Position',
            'Senior Position',
            'Leadership Position'
        ],
        'Focus': [
            'Master Current Role',
            'Develop New Skills',
            'Gain Specialization',
            'Strategic Leadership'
        ]
    }
    
    df = pd.DataFrame(path_data)
    
    fig = px.scatter(df, x='Stage', y='Role', size=[10, 15, 20, 25], 
                     hover_data=['Focus'], title='Suggested Career Path')
    st.plotly_chart(fig, use_container_width=True)

# Main app
def main():
    render_header()
    
    tab1, tab2, tab3 = st.tabs(["Resume Analysis", "Career Recommendations", "Job Market"])
    
    with tab1:
        render_resume_upload()
        if st.session_state.resume_text:
            render_resume_score()
            render_skills_analysis()
    
    with tab2:
        if st.session_state.resume_text:
            render_career_recommendations()
            render_career_path()
        else:
            st.info("Upload your resume to get career recommendations")
    
    with tab3:
        render_job_market_insights()

if __name__ == "__main__":
    main()
