import json
from pymongo import MongoClient

# MongoDB connection URI (Specify authSource=admin)
uri = "mongodb://Vaidya:123@localhost:27017/Vaidya?authSource=admin"

# Connect to MongoDB
client = MongoClient(uri)

# Select the database
db = client["Vaidya"]

# Function to retrieve all data from a collection
def get_all_data(collection):
    try:
        # Fetch all documents from the collection
        data = list(collection.find())
        return data
    except Exception as e:
        print(f"❌ Failed to retrieve data from {collection.name}: {e}")
        return []

# Retrieve data from all collections
patients = get_all_data(db.Patients)
doctors = get_all_data(db.Doctor)
prescriptions = get_all_data(db.Prescription)
reports = get_all_data(db.Reports)
tests = get_all_data(db.Tests)

# Pretty print the data
print("\nAll Patients:")
print(json.dumps(patients, indent=4, default=str))

print("\nAll Doctors:")
print(json.dumps(doctors, indent=4, default=str))

print("\nAll Prescriptions:")
print(json.dumps(prescriptions, indent=4, default=str))

print("\nAll Reports:")
print(json.dumps(reports, indent=4, default=str))

print("\nAll Tests:")
print(json.dumps(tests, indent=4, default=str))