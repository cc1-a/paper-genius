import google.generativeai as genai

# PASTE YOUR KEY HERE
MY_KEY = "AIzaSyDZ0BGY6OMHsU9T1bXxz4h2cl_m9-54zJc" 

genai.configure(api_key=MY_KEY)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error connecting: {e}")