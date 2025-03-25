from flask import Flask, request, jsonify
from langchain_core.language_models.llms import LLM
from openai import OpenAI

app = Flask(__name__)

# Initialize the OpenAI client
client = OpenAI(base_url="http://localhost:1234/v1", api_key="happy")
model = "hermes-3-llama-3.2-3b"

# Define the system prompt
system_prompt = """You are a robust AI assistant designed to support doctors in diagnosing patients by providing accurate information based on patient data. 
Your task is to assist the doctor with their queries regarding patient information. 
Context : {context}

Once you have the context, respond to the doctor's query with facts strictly derived from the provided patient information. It's crucial that you do not provide diagnostic recommendations or answers that are not substantiated by the context, as accuracy is paramount to avoid misinformation. 

Make sure to verify the context first before responding and clearly indicate whether the information is available or not. 

Examples of queries could include:

"What is the patient's medical history?"
"Can you provide information on the patient's allergies?"

Provide clear and concise responses based solely on the context given and refrain from introducing any assumptions or unverified claims.
"""

# Define a simple LLM class for memory summarization
class LocalLLM(LLM):
    def _llm_type(self):
        return "local_llm"
    
    def _call(self, prompt, stop=None, run_manager=None, **kwargs):
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return completion.choices[0].message.content

@app.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint to process a chat request.
    
    Expected JSON payload:
    {
        "context": "Patient medical information here...",
        "conversation": [
            {"role": "system", "content": "Initial system message"},
            {"role": "user", "content": "Doctor's first question"},
            {"role": "assistant", "content": "AI's first response"},
            ...
            {"role": "user", "content": "Current question"}
        ]
    }
    
    Returns:
    {
        "response": "AI's response to the current question",
        "conversation": [
            ... (previous conversation) ...,
            {"role": "assistant", "content": "AI's new response"}
        ]
    }
    """
    data = request.json
    
    if not data or 'context' not in data or 'conversation' not in data:
        return jsonify({"error": "Missing required parameters"}), 400
    
    context = data['context']
    conversation = data['conversation']
    
    # Check if there's a conversation and if the last message is from the user
    if not conversation or conversation[-1]['role'] != 'user':
        return jsonify({"error": "Conversation must end with a user message"}), 400
    
    try:
        # Prepare the system prompt with context
        adjusted_system_prompt = system_prompt.format(context=context)
        
        # Prepare messages for the API call
        messages = [{"role": "system", "content": adjusted_system_prompt}]
        
        # Add the conversation history (excluding the system message if it exists)
        for msg in conversation:
            if msg['role'] != 'system':  # Skip system messages from conversation history
                messages.append({"role": msg['role'], "content": msg['content']})
        
        # Generate the response
        completion = client.chat.completions.create(
            model=model,
            messages=messages
        )
        
        response = completion.choices[0].message.content
        
        # Add the response to the conversation history
        updated_conversation = conversation.copy()
        updated_conversation.append({"role": "assistant", "content": response})
        
        return jsonify({
            "response": response,
            "conversation": updated_conversation
        })
    
    except Exception as e:
        return jsonify({"error": f"Error generating response: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

# Enable CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)