from flask import Flask, request, jsonify
from openai import OpenAI
import google.generativeai as genai
import json
from pymongo import MongoClient
from datetime import datetime
import uuid
import requests
import json

app = Flask(__name__)

# Initialize OpenAI client (local LLM)
client = OpenAI(base_url="http://localhost:1234/v1", api_key="happy")
model = "hermes-3-llama-3.2-3b"
url = "http://192.168.28.168:5000/save_patient"

# Configure Gemini API
genai.configure(api_key="AIzaSyC_9O6jp--RJAxgVx-zz1N87BWrX0P_WzI")

# MongoDB setup
mongo_client = MongoClient("mongodb://Vaidya:123@192.168.28.168:27017/Vaidya?authSource=admin")  # Update with your MongoDB URI
db = mongo_client["Vaidya"]
patients_collection = db["Patients"]
appointments_collection = db["Appointments"]

# Generic questionnaire
generic_questionnaire = [
    {"id": 1, "category": "Detailed History", "question": "What brings you in today? (Chief Complaint)"},
    {"id": 2, "category": "Detailed History", "question": "How long have you been experiencing these symptoms?"},
    {"id": 3, "category": "Medical History", "question": "Do you have any chronic conditions (e.g., diabetes, hypertension)?"},
    {"id": 4, "category": "Medical History", "question": "Have you had any major surgeries or procedures in the past?"},
    {"id": 5, "category": "Medical History", "question": "Do you have any known allergies (medications, food, environmental)?"},
    {"id": 6, "category": "Medical History", "question": "Is there a history of any major diseases in your family?"},
    {"id": 7, "category": "Current Medication", "question": "Are you currently taking any prescribed medications?"},
    {"id": 8, "category": "Current Medication", "question": "Are you taking any over-the-counter drugs or supplements?"},
    {"id": 9, "category": "Test Results", "question": "Have you had any recent lab tests or imaging done?"},
    {"id": 10, "category": "Lifestyle & Risk Factors", "question": "How would you describe your diet and nutrition habits?"},
    {"id": 11, "category": "Lifestyle & Risk Factors", "question": "Do you smoke, drink alcohol, or use any substances?"},
    {"id": 12, "category": "Lifestyle & Risk Factors", "question": "How frequently do you exercise?"},
    {"id": 13, "category": "Lifestyle & Risk Factors", "question": "How has your mental health been recently?"}
]

# Temporary storage for user responses
user_data = {}

def process_aadhaar_image(image_data):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = """You are an advanced AI specialist with expertise in extracting data from images using optical character recognition techniques. Your task is to analyze the provided Aadhaar card image and extract the necessary information, returning it in a specified JSON format.
    Return the extracted information in the following JSON structure: { "aadhaar_info": { "name": "string", "aadhaar_number": "string", "date_of_birth": "string", "gender": "string", "address": "string or null" }, "source": "image" }
    Ensure that the output is valid JSON. If a field is not found in the image, use null for that value."""
    
    response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": image_data}])
    raw_output = response.text
    cleaned_output = raw_output.replace("```json", "").replace("```", "").strip()
    
    try:
        return json.loads(cleaned_output)
    except json.JSONDecodeError as e:
        return {"error": "JSON parsing error", "details": str(e)}

def generate_patient_id():
    return str(uuid.uuid4().hex)[:24]

def generate_appointment_id():
    return str(uuid.uuid4().hex)[:24]

@app.route('/upload_aadhaar', methods=['POST'])
def upload_aadhaar():
    if 'image' not in request.files or 'is_new_patient' not in request.form:
        return jsonify({"error": "Missing image file or is_new_patient field"}), 400
    
    image_file = request.files['image'].read()
    is_new_patient = request.form['is_new_patient'].lower() == 'true'
    
    aadhaar_data = process_aadhaar_image(image_file)
    if "error" in aadhaar_data:
        return jsonify(aadhaar_data), 500
    
    aadhaar_info = aadhaar_data["aadhaar_info"]
    patient_id = generate_patient_id()
    
    if is_new_patient:
        patient_data = {
            "_id": patient_id,
            "patient_name": aadhaar_info["name"],
            "date_of_birth": aadhaar_info["date_of_birth"],
            "gender": aadhaar_info["gender"],
            "aadhaar_number": aadhaar_info["aadhaar_number"],
            "blood_group": None,
            "contact_info": None,
            "summary": None,
            "detailed_history": {},
            "medical_history": {},
            "medical_condition": {},
            "current_medication": {},
            "test_results": {},
            "lifestyle_risk_factors": {}
        }
        response = requests.post(url, json=patient_data)

    print("Status:", response.status_code)
    print("Response:", response.json())
    
    user_data[patient_id] = {"aadhaar_info": aadhaar_info, "is_new_patient": is_new_patient}
    
    return jsonify({
        "patient_id": patient_id,
        "is_new_patient": is_new_patient,
        "message": "Please proceed with the questionnaire",
        "aadhaar_info": aadhaar_info  # Added processed Aadhaar details
    })

@app.route('/questionnaire', methods=['GET'])
def get_questionnaire():
    return jsonify({"questions": generic_questionnaire})

@app.route('/submit_responses', methods=['POST'])
def submit_responses():
    data = request.json
    patient_id = data.get("patient_id")
    responses = data.get("responses")
    
    if not patient_id or not responses:
        return jsonify({"error": "Missing patient_id or responses"}), 400
    
    user_data[patient_id]["first_stage_responses"] = responses
    
    prompt = f"""
    Based on the following patient responses, determine the next set of questions needed to complete their medical profile:
    {json.dumps(responses)}
    
    Provide the next questions in a structured JSON format like:
    [
        {{"category": "Category Name", "question": "New question here"}},
        ...
    ]
    """
    try:
        completion = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}])
        next_questions = json.loads(completion.choices[0].message.content)
        return jsonify({"next_questions": next_questions})
    except Exception as e:
        return jsonify({"error": f"Error generating next questions: {str(e)}"}), 500

def safe_json_loads(text):
    try:
        return json.loads(text)
    except Exception:
        return text  # return raw content if JSON parsing fails

@app.route('/submit_second_responses', methods=['POST'])
def submit_second_responses():
    data = request.json
    patient_id = data.get("patient_id")
    second_responses = data.get("responses")
    
    if not patient_id or not second_responses:
        return jsonify({"error": "Missing patient_id or second responses"}), 400
    
    if patient_id not in user_data:
        return jsonify({"error": "User data not found"}), 404
    
    user_data[patient_id]["second_stage_responses"] = second_responses
    
    # Step 1: Generate the detailed medical report
    report_prompt = f"""
    Generate a comprehensive medical report based on the following user responses:
    
    First-stage responses:
    {json.dumps(user_data[patient_id]["first_stage_responses"])}
    
    Second-stage responses:
    {json.dumps(second_responses)}
    
    Provide a detailed report summarizing the patient's medical history, current condition, lifestyle risks, and potential concerns.
    """
    report_completion = client.chat.completions.create(model=model, messages=[{"role": "user", "content": report_prompt}])
    final_report = report_completion.choices[0].message.content
    
    # Step 2: Generate individual fields based on the report
    try:
        # Summary
        summary_prompt = f"Based on this medical report: {final_report}, provide a brief conclusion about the patient's current health status, treatment progress, and doctor's recommendations in a string format."
        summary_completion = client.chat.completions.create(model=model, messages=[{"role": "user", "content": summary_prompt}])
        summary = summary_completion.choices[0].message.content
        
        # Detailed History
        detailed_history_prompt = f"Based on this medical report: {final_report}, extract and structure the detailed history into a JSON object."
        detailed_history_completion = client.chat.completions.create(model=model, messages=[{"role": "user", "content": detailed_history_prompt}])
        detailed_history = safe_json_loads(detailed_history_completion.choices[0].message.content)
        
        # Medical History
        medical_history_prompt = f"Based on this medical report: {final_report}, extract and structure the medical history into a JSON object."
        medical_history_completion = client.chat.completions.create(model=model, messages=[{"role": "user", "content": medical_history_prompt}])
        medical_history = safe_json_loads(medical_history_completion.choices[0].message.content)
        
        # Medical Condition
        medical_condition_prompt = f"Based on this medical report: {final_report}, extract and structure the current medical condition into a JSON object."
        medical_condition_completion = client.chat.completions.create(model=model, messages=[{"role": "user", "content": medical_condition_prompt}])
        medical_condition = safe_json_loads(medical_condition_completion.choices[0].message.content)
        
        # Current Medication
        current_medication_prompt = f"Based on this medical report: {final_report}, extract and structure the current medication into a JSON object."
        current_medication_completion = client.chat.completions.create(model=model, messages=[{"role": "user", "content": current_medication_prompt}])
        current_medication = safe_json_loads(current_medication_completion.choices[0].message.content)
        
        # Test Results
        test_results_prompt = f"Based on this medical report: {final_report}, extract and structure the test results into a JSON object."
        test_results_completion = client.chat.completions.create(model=model, messages=[{"role": "user", "content": test_results_prompt}])
        test_results = safe_json_loads(test_results_completion.choices[0].message.content)
        
        # Lifestyle Risk Factors
        lifestyle_risk_factors_prompt = f"Based on this medical report: {final_report}, extract and structure the lifestyle risk factors into a JSON object."
        lifestyle_risk_factors_completion = client.chat.completions.create(model=model, messages=[{"role": "user", "content": lifestyle_risk_factors_prompt}])
        lifestyle_risk_factors = safe_json_loads(lifestyle_risk_factors_completion.choices[0].message.content)
        
        # Step 3: Update patient record if new patient
        if user_data[patient_id]["is_new_patient"]:
            patient_update = {
                "summary": summary,
                "detailed_history": detailed_history,
                "medical_history": medical_history,
                "medical_condition": medical_condition,
                "current_medication": current_medication,
                "test_results": test_results,
                "lifestyle_risk_factors": lifestyle_risk_factors
            }

            # Recreate the post request using the prompt
            

            patient_data = ({"_id": patient_id}, {"$set": patient_update})
            response = requests.post(url, json=patient_data)  # DB operation commented out


        # Step 4: Generate appointment details
        appointment_prompt = f"""
        Based on this medical report: {final_report}, generate appointment details in a structured JSON format:
        {{
          "_id": "generate a unique 24-character ID",
          "doctor_id": "assign a default doctor ID: 661def789123456789abcd01",
          "patient_id": "{patient_id}",
          "date": "current date in YYYY-MM-DD format",
          "time": "suggest a suitable time (e.g., 10:00) based on the urgency in the report",
          "is_first_time": {user_data[patient_id]["is_new_patient"]},
          "status": "Scheduled",
          "reason": "extract the chief complaint or primary concern from the report",
          "created_at": "current timestamp in ISO format",
          "updated_at": "current timestamp in ISO format",
          "age": "calculate age from {user_data[patient_id]["aadhaar_info"]["date_of_birth"]}",
          "name": "{user_data[patient_id]["aadhaar_info"]["name"]}",
          "sex": "{user_data[patient_id]["aadhaar_info"]["gender"]}"
        }}
        """
        appointment_completion = client.chat.completions.create(model=model, messages=[{"role": "user", "content": appointment_prompt}])
        appointment_data = safe_json_loads(appointment_completion.choices[0].message.content)
        
        # Step 5: Insert appointment into the database
        # appointments_collection.insert_one(appointment_data)  # DB operation commented out
        ap_res = requests.post("http://192.168.28.168:5000/save_appointment", json=appointment_data)
        
        return jsonify({
            "final_report": final_report,
            "patient_details": {
                "summary": summary,
                "detailed_history": detailed_history,
                "medical_history": medical_history,
                "medical_condition": medical_condition,
                "current_medication": current_medication,
                "test_results": test_results,
                "lifestyle_risk_factors": lifestyle_risk_factors
            },
            "appointment_details": appointment_data
        })
    
    except Exception as e:
        return jsonify({"error": f"Error processing request: {str(e)}"}), 500





if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)