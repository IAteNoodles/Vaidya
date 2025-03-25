class Connect:
    def __init__(self):
        from pymongo import MongoClient

        # MongoDB connection URI (Specify authSource=admin)
        uri = "mongodb://Vaidya:123@localhost:27017/Vaidya?authSource=admin"

        # Connect to MongoDB
        client = MongoClient(uri)

        # Select the database
        self.db = client["Vaidya"]

        # Test connection
        try:
            # Fetch collections to check connection
            collections = self.db.list_collection_names()
            print("✅ Connection Successful!")
            print("Collections:", collections)
        except Exception as e:
            print("❌ Connection Failed:", e)


    def get_detailed_report(self, patient_id):
        """
        Get detailed report of a patient.
        :param patient_id: ID of the patient whose report is to be fetched.
        :return: Detailed report as JSON response.
        """
        # Use DetailedReport collection to fetch detailed report
        try:
            details = self.db.DetailedReport.find_one({"_id": patient_id})
            if not details:
                return None
            # Convert ObjectId and other non-serializable fields to strings
            details["patient_name"] = details.get("patient_name", "")
            details["date_of_birth"] = details.get("date_of_birth", "")
            details["gender"] = details.get("gender", "")
            details["blood_group"] = details.get("blood_group", "")
            details["contact_info"] = details.get("contact_info", "")
            details["summary"] = details.get("summary", "")
            details["detailed_history"] = details.get("detailed_history", {})
            details["medical_history"] = details.get("medical_history", {})
            details["medical_condition"] = details.get("medical_condition", {})
            details["current_medication"] = details.get("current_medication", {})
            details["test_results"] = details.get("test_results", {})
            details["lifestyle_risk_factors"] = details.get("lifestyle_risk_factors", {})
            return details
        except Exception as e:
            print(f"❌ Error fetching detailed report: {e}")
            return None

    def get_n_patients(self, doctor_id, n=0):
        """
        Endpoint to fetch all patients of a doctor.

        :param doctor_id: ID of the doctor whose patients are to be fetched.
        :param n: Number of patients to fetch. Default is 0, which fetches all patients.

        :return: List of patient id with name, and last appointment as JSON response.
        """
        try:
            if n == 0:
                # Fetch all patients of the doctor using the Connect class
                patients = self.db.Patients.find({"doctor_id": doctor_id})
            else:
                patients = self.db.Patients.find({"doctor_id": doctor_id}).limit(n)
            if not patients:
                return None

            # Convert ObjectId and other non-serializable fields to strings
            for patient in patients:
                patient["_id"] = str(patient["_id"])
                patient["name"] = str(patient["name"])
                patient["last_appointment"] = str(patient["last_appointment"])

            return patients
        except Exception as e:
            return None
        
    
    #DONE
    def get_n_appointments(self, doctor_id, n=0):
        """
        Endpoint to fetch all appointments of a doctor.

        :param doctor_id: ID of the doctor whose appointments are to be fetched.
        :param n: Number of appointments to fetch. Default is 0, which fetches all appointments.

        :return: List of appointment id with patient_id, and date as JSON response.
        """
        try:
            if n == 0:
                # Fetch all appointments of the doctor using the Connect class
                appointments = self.db.Appointments.find({"doctor_id": doctor_id})
            else:
                appointments = self.db.Appointments.find({"doctor_id": doctor_id}).limit(n)
            if not appointments:
                return None
            # Convert ObjectId and other non-serializable fields to strings
            main_appointment = list()
            
            for appointment in appointments:
                _appointment = dict()
                _appointment["_id"] = str(appointment["_id"])
                _appointment["patient_id"] = str(appointment["patient_id"])
                _appointment["date"] = str(appointment["date"])
                _appointment["name"] = appointment.get("name", "")
                _appointment["age"] = appointment.get("age", "")
                _appointment["sex"] = appointment.get("sex", "")
                main_appointment.append(_appointment)

            return main_appointment
        except Exception as e:
            print(e)
            return None
        
    def get_n_reports(self, patient_id, n=0):
        """
        Endpoint to fetch all reports of a patient.
        :param patient_id: ID of the patient whose reports are to be fetched.
        :param n: Number of reports to fetch. Default is 0, which fetches all reports.
        :return: List of report id with patient_id, and date as JSON response.
        """
        try:
            if n == 0:
                # Fetch all reports of the patient using the Connect class
                reports = self.db.Reports.find({"patient_id": patient_id})
            else:
                reports = self.db.Reports.find({"patient_id": patient_id}).limit(n)
            if not reports:
                return None
            # Convert ObjectId and other non-serializable fields to strings
            main_reports = list()
            for report in reports:
                _report = dict()
                _report["_id"] = str(report["_id"])
                _report["patient_id"] = str(report["patient_id"])
                _report["doctor_id"] = str(report["doctor_id"])
                _report["date"] = str(report["created_at"])
                _report["doctor_name"] = report["doctor_name"]
                _report["conclusion"] = report["summary"]
                _report["tests_id"] = report.get("tests_id", [])  # List of test IDs
                _report["prescriptions_id"] = report.get("prescriptions_id", [])  # List of prescription IDs
                _report["report_file"] = "Stored in GridFS"  # Assuming the file is in GridFS
                main_reports.append(_report)
            return main_reports
        except Exception as e:
            print(e)
            return None
##############################################
    def get_patient_details(self, id):
        try:
            # Fetch patient details from the database using id
            patient = self.db.Patients.find_one({"_id": id})
            return patient
        except Exception as e:
            return None
        
    def save_patient_details(self, **kwargs):
        """
        Save patient details to the database using the provided kwargs.
        """
        try:
            # Insert patient details into the database
            self.db.Patients.insert_one(kwargs)
            return True
        except Exception as e:
            print(f"❌ Error saving patient details: {e}")
            return False

    def get_doctor_details(self, id):
        try:
            # Fetch doctor details from the database using id
            doctor = self.db.Doctor.find_one({"_id": id})
            return doctor
        except Exception as e:
            return None

    def save_doctor_details(self, **kwargs):
        """
        Save doctor details to the database using the provided kwargs.
        """
        try:
            # Insert doctor details into the database
            self.db.Doctor.insert_one(kwargs)
            return True
        except Exception as e:
            print(f"❌ Error saving doctor details: {e}")
            return False

    def get_prescription_details(self, id):
        try:
            # Fetch prescription details from the database using id
            prescription = self.db.Prescription.find_one({"_id": id})
            return prescription
        except Exception as e:
            return None

    def save_prescription_details(self, **kwargs):
        """
        Save prescription details to the database using the provided kwargs.
        """
        try:
            # Insert prescription details into the database
            self.db.Prescription.insert_one(kwargs)
            return True
        except Exception as e:
            print(f"❌ Error saving prescription details: {e}")
            return False

    def get_report_details(self, id):
        try:
            # Fetch report details from the database using id
            report = self.db.Reports.find_one({"_id": id})
            return report
        except Exception as e:
            return None

    def save_report_details(self, **kwargs):
        """
        Save report details to the database using the provided kwargs.
        """
        try:
            # Insert report details into the database
            self.db.Reports.insert_one(kwargs)
            return True
        except Exception as e:
            print(f"❌ Error saving report details: {e}")
            return False

    def get_test_details(self, id):
        try:
            # Fetch test details from the database using id
            test = self.db.Tests.find_one({"_id": id})
            return test
        except Exception as e:
            return None

    def save_test_details(self, test):
        try:
            # Insert test details into the database
            self.db.Tests.insert_one(test)
            return True
        except Exception as e:
            return False
        
    def save_appointment_details(self, **kwargs):
        """
        Save appointment details to the database using the provided kwargs.
        """
        try:
            # Insert appointment details into the database
            self.db.Appointments.insert_one(kwargs)
            return True
        except Exception as e:
            print(f"❌ Error saving appointment details: {e}")
            return False


    def get_appointment_details(self, **kwargs):
        """
        Fetch appointment details from the database using filters provided in kwargs.
        """
        try:
            # Fetch appointment details using the provided filters
            appointment = self.db.Appointments.find_one(kwargs)
            return appointment
        except Exception as e:
            print(f"❌ Error fetching appointment details: {e}")
            return None
    
##############################################
connect = Connect()
print(connect.get_n_reports("65f8a123456789abcd123459", 2))