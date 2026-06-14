import os
import json
import logging
import pdfplumber
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import google.generativeai as genai
import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeAnalyzerEngine:
    def __init__(self):
        # Configure API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY is not set in environment variables.")
        genai.configure(api_key=api_key)
        self.model_name = config.GEMINI_MODEL
        logger.info(f"Initialized ResumeAnalyzerEngine with model: {self.model_name}")

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a PDF file using pdfplumber, falling back to OCR if empty."""
        text = ""
        try:
            # Try direct text extraction
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text

            if text.strip():
                logger.info("Direct PDF text extraction succeeded.")
                return text.strip()
        except Exception as e:
            logger.error(f"Direct text extraction failed: {e}")

        # Fallback to OCR for scanned/image-based PDFs
        logger.info("Falling back to OCR (pytesseract) for image-based PDF.")
        try:
            images = convert_from_path(pdf_path)
            for image in images:
                page_text = pytesseract.image_to_string(image)
                text += page_text + "\n"
        except Exception as e:
            logger.error(f"OCR text extraction failed: {e}")

        return text.strip()

    def analyze_compatibility(self, resume_text: str, job_description: str) -> dict:
        """Call Gemini to get a structured JSON breakdown of resume-JD alignment."""
        if not resume_text:
            return {"error": "Resume text is empty or could not be extracted."}
        
        # Prepare target job description fallback
        jd_text = job_description.strip() if job_description else "General Technical/Corporate Resume Review"

        prompt = f"""
        You are an expert corporate recruiter and ATS (Applicant Tracking System) reviewer.
        Analyze the provided resume and evaluate its compatibility with the target Job Description (JD).
        
        Resume:
        {resume_text}
        
        Job Description:
        {jd_text}
        
        Evaluate the resume across three dimensions and return a strict JSON object with the following schema:
        {{
          "keyword_score": <integer 0-100, representing keyword overlap and core tech skill coverage>,
          "experience_score": <integer 0-100, representing job role context, years of experience, and educational relevance>,
          "formatting_score": <integer 0-100, representing section readability, structure, and general formatting health>,
          "matched_skills": [<list of strings representing key skills/technologies found in both JD and resume>],
          "missing_skills": [<list of strings representing important skills/technologies found in JD but missing from resume>],
          "formatting_issues": [<list of strings of design/formatting issues, e.g., 'No phone number', 'Length is too long'>],
          "suggestions": [
            {{
              "section": "<section name like 'Experience', 'Projects', 'Skills', 'Header'>",
              "issue": "<detailed explanation of what is lacking or weak>",
              "remediation": "<a concrete example of how to rewrite or fix this issue>"
            }}
          ],
          "course_recommendations": [
            {{
              "skill": "<missing skill or area needing improvement>",
              "course_title": "<suggested online course name, e.g. 'Docker & Kubernetes Complete Bootcamp'>",
              "platform": "<suggested learning platform, e.g. 'Udemy', 'Coursera', 'Kaggle'>"
            }}
          ]
        }}
        
        Return ONLY valid JSON. Do not include markdown headers, blockquotes, or markdown code blocks (e.g. do NOT wrap output in ```json).
        """

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={"response_mime_type": "application/json"}
            )
            response = model.generate_content(prompt)
            data = json.loads(response.text.strip())
            
            # Programmatically calculate overall compatibility score using configurable weights
            keyword_alignment = data.get("keyword_score", 0)
            experience_relevance = data.get("experience_score", 0)
            formatting_health = data.get("formatting_score", 0)
            
            weighted_score = (
                (keyword_alignment * config.WEIGHT_KEYWORD_ALIGNMENT) +
                (experience_relevance * config.WEIGHT_EXPERIENCE_RELEVANCE) +
                (formatting_health * config.WEIGHT_FORMATTING_HEALTH)
            )
            
            data["overall_compatibility_score"] = round(weighted_score, 1)
            return data
            
        except json.JSONDecodeError as jde:
            logger.error(f"Failed to parse JSON from Gemini response: {jde}")
            # Try to recover or return parsing error
            return {"error": "Received malformed analysis output from Gemini. Please try again."}
        except Exception as e:
            logger.error(f"Gemini API analysis failed: {e}")
            return {"error": f"Analysis failed: {str(e)}"}

    def optimize_bullet_point(self, bullet_point: str, missing_skills: list) -> str:
        """Call Gemini to rewrite a resume bullet point to make it more impactful (STAR method)."""
        skills_context = f" incorporating these target skills/keywords: {', '.join(missing_skills)}" if missing_skills else ""
        prompt = f"""
        You are a professional resume writer. Rewrite the following single bullet point to make it highly impactful, action-oriented, and metric-driven using the STAR method (Situation, Task, Action, Result).
        {skills_context}
        
        Original Bullet Point:
        "{bullet_point}"
        
        Provide ONLY the rewritten bullet point text starting with an action verb. Do not include any explanations, introduction, or conversational filler.
        """
        
        try:
            model = genai.GenerativeModel(model_name=self.model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Bullet point optimization failed: {e}")
            return f"Error: Could not optimize bullet point. ({str(e)})"
