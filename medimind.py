import pyrebase
import streamlit as st
import google.generativeai as genai
from PIL import Image
import PyPDF2
import tempfile
import os
from google.api_core import exceptions
from dotenv import load_dotenv
import time

firebaseConfig = {
  'apiKey': "AIzaSyAKjy4rbgpRz26IkzZ5JTMq0RQMKW0CdCc",
  'authDomain': "medimind-7de22.firebaseapp.com",
  'projectId': "medimind-7de22",
  'databaseURL' :"https://medimind-7de22-default-rtdb.europe-west1.firebasedatabase.app/",
  'storageBucket': "medimind-7de22.firebasestorage.app",
  'messagingSenderId': "227540571996",
  'appId': "1:227540571996:web:037227e0cb7f48ab435399",
  'measurementId': "G-6PNV56CM06"
}


firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

db = firebase.database()
storage = firebase.storage()

if "page" not in st.session_state:
    st.session_state.page = 1

def page1():

    st.set_page_config(
        page_title="Medimind-login_page",
        page_icon="👩🏽‍⚕"
    )
    
    st.markdown(
        """
        <style>
            .header {
                text-align: center;
                font-size: 32px;
                font-weight: bold;
                color: #CC5500;
                font-family: 'Poppins', sans-serif;
            }
            .subheader {
            text-align: center;
            font-size: 20px;
            color: white ;
            font-family: 'Open Sans', sans-serif;
            }
            p{
            text-align: center;
            color: white;
            font-family: 'Raleway', sans-serif;
            color : #7DF9FF;
            }
        </style>
        <div class="header">Welcome to Medimind</div>
        <div class="subheader">Your Medical Report Simplified!</div>
        <p style="color : #228B22;">hello there!!</p>
        """,
        unsafe_allow_html=True
    )
    
    choice = st.selectbox('Login/Signup',['Login','Signup'])

    email = st.text_input('Enter your email address: ')

    password = st.text_input('Enter your password: ', type = 'password')

    if choice == 'Signup':
        handle = st.text_input('Please Enter your unique user name:' )
        submit = st.button('Create my account')

        if submit:
            try:
                user = auth.create_user_with_email_and_password(email,password)
                st.success(f'Hii,{handle} your account created successfully!!')
                st.write('Go back and login to your account!!')
                
                user = auth.sign_in_with_email_and_password(email,password)
                db.child(user['localId']).child("handle").set(handle)
                db.child(user['localId']).child("ID").set(user['localId'])
                st.session_state.page = 2
                st.rerun()
            except Exception as e:
                st.error("please fill all the required fields or check You may already have an Account!! try to log in")

    if choice == 'Login':
        login = st.button('Login')
        if login:
            try:
                user = auth.sign_in_with_email_and_password(email,password)
                st.session_state.page = 2
                st.rerun()
            except Exception as e:
                st.error('Please Enter required fields with valid infromation')
def page2():
    
    load_dotenv()

    #'''Configure the Gemini AI model
    #api_key = os.getenv("GEMINI_API_KEY")
    #st.stop()
    #st.stop()
    #if not api_key:
    #st.error("Gemini API key not found. Please set the GEMINI_API_KEY environment variable.")


    genai.configure(api_key="AIzaSyAKLcXDFZFhn-Yi5CbF3xcIedxII1PHOAg")
    model = genai.GenerativeModel('gemini-1.5-flash')

    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds

    def analyze_medical_report(content, content_type):
        prompt = "Analyze this medical report concisely. Provide key findings, diagnoses, and recommendations:"
        
        for attempt in range(MAX_RETRIES):
            try:
                if content_type == "image":
                    response = model.generate_content([prompt, content])
                else:  # text
                    # Gemini 1.5 Flash can handle larger inputs, so we'll send the full text
                    response = model.generate_content(f"{prompt}\n\n{content}")
                
                return response.text
            except exceptions.GoogleAPIError as e:
                if attempt < MAX_RETRIES - 1:
                    st.warning(f"An error occurred. Retrying in {RETRY_DELAY} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(RETRY_DELAY)
                else:
                    st.error(f"Failed to analyze the report after {MAX_RETRIES} attempts. Error: {str(e)}")
                    return fallback_analysis(content, content_type)

    def fallback_analysis(content, content_type):
        st.warning("Using fallback analysis method due to API issues.")
        if content_type == "image":
            return "Unable to analyze the image due to API issues. Please try again later or consult a medical professional for accurate interpretation."
        else:  # text
            word_count = len(content.split())
            return f"""
            Fallback Analysis:
            1. Document Type: Text-based medical report
            2. Word Count: Approximately {word_count} words
            3. Content: The document appears to contain medical information, but detailed analysis is unavailable due to technical issues.
            4. Recommendation: Please review the document manually or consult with a healthcare professional for accurate interpretation.
            5. Note: This is a simplified analysis due to temporary unavailability of the AI service. For a comprehensive analysis, please try again later.
            """

    def extract_text_from_pdf(pdf_file):
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text

    def main():
        st.set_page_config(
            page_title="Medimind",
            page_icon="🩺",
            initial_sidebar_state="collapsed"
        )
        st.title("MEDIMIND👩🏽‍⚕")
        st.write("Your intelligent medical report analyser :wave:")
        st.write("Upload a medical report (image or PDF) for analysis")

        file_type = st.radio("Select file type:", ("Image:camera_with_flash:", "PDF📄"))

        if file_type == "Image:camera_with_flash:":
            uploaded_file = st.file_uploader("Choose a medical report image", type=["jpg", "jpeg", "png"])
            if uploaded_file is not None:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name

                image = Image.open(tmp_file_path)
                st.image(image, caption="Uploaded Medical Report✅", width=200)

                if st.button("Analyze Image Report🔍"):
                    with st.spinner("Analyzing the medical report image...🔍"):
                        analysis = analyze_medical_report(image, "image")
                        st.subheader("Analysis Results:")
                        st.write(analysis)

                os.unlink(tmp_file_path)

        else:  # PDF
            uploaded_file = st.file_uploader("Choose a medical report PDF", type=["PDF"])
            if uploaded_file is not None:
                st.write("PDF uploaded successfully✅")

                if st.button("Analyze PDF Report"):
                    with st.spinner("Analyzing the medical report PDF..."):
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_file_path = tmp_file.name

                        with open(tmp_file_path, 'rb') as pdf_file:
                            pdf_text = extract_text_from_pdf(pdf_file)

                        analysis = analyze_medical_report(pdf_text, "text")
                        st.subheader("Analysis Results:🩺")
                        st.write(analysis)

                        os.unlink(tmp_file_path)

    if __name__ == "__main__":
        main()
if st.session_state.page == 1:
    page1()
if st.session_state.page == 2:
    page2()







