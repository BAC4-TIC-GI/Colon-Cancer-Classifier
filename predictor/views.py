from django.shortcuts import render
from .models import Patient, Prediction
from django.views import View
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

# Get the current file directory
model_path = Path(__file__).resolve().parent / 'cc_model_rf.pkl'
model = joblib.load(model_path)

class HomeView(View):
    template_name = 'predictor/home.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        try:
            # Collect all patient data
            patients_data = {}
            for key in request.POST:
                if key.startswith('patient'):
                    patient_num, field = key.split('_', 1)
                    if patient_num not in patients_data:
                        patients_data[patient_num] = {'features': []}
                    if field.startswith('feature'):
                        patients_data[patient_num]['features'].append((field, request.POST[key]))
                    else:
                        patients_data[patient_num][field] = request.POST[key]

            if not patients_data:
                return render(request, self.template_name, {
                    'error': 'No patient data provided.'
                })

            all_feature_predictions = []
            for patient_num, data in patients_data.items():
                # Validate patient information
                patient_name = data.get('name')
                patient_age = data.get('age')
                patient_gender = data.get('gender')

                if not patient_name or len(patient_name) > 100:
                    return render(request, self.template_name, {
                        'error': f'Invalid patient name for Patient {patient_num.replace("patient", "")}.'
                    })
                try:
                    patient_age = int(patient_age)
                    if patient_age < 0 or patient_age > 150:
                        raise ValueError
                except (ValueError, TypeError):
                    return render(request, self.template_name, {
                        'error': f'Invalid age for Patient {patient_num.replace("patient", "")}.'
                    })
                if patient_gender not in ['M', 'F', 'O']:
                    return render(request, self.template_name, {
                        'error': f'Invalid gender for Patient {patient_num.replace("patient", "")}.'
                    })

                # Validate and collect features
                features = []
                for feature_key, feature_value in sorted(data['features'], key=lambda x: x[0]):
                    try:
                        features.append(float(feature_value))
                    except ValueError:
                        return render(request, self.template_name, {
                            'error': f'Invalid feature value for Patient {patient_num.replace("patient", "")}.'
                        })

                if not features:
                    return render(request, self.template_name, {
                        'error': f'No features provided for Patient {patient_num.replace("patient", "")}.'
                    })

                # Save patient to database
                patient = Patient.objects.create(
                    name=patient_name,
                    age=patient_age,
                    gender=patient_gender
                )

                # Create and save predictions
                feature_predictions = []
                for i, feature_value in enumerate(features, start=1):
                    feature_array = np.array([[feature_value]])
                    features_reshaped = pd.DataFrame(feature_array, columns=["DAO"])

                    prediction = model.predict(features_reshaped)
                    probability = model.predict_proba(features_reshaped)
                    print("Prediction: ", prediction)

                    # Save prediction to database
                    Prediction.objects.create(
                        patient=patient,
                        feature_name=f'DAO {i}',
                        feature_value=feature_value,
                        prediction=prediction[0],
                        probability=max(probability[0]) * 100,
                        is_positive=prediction[0] == "normal"
                    )

                    # Prepare context for template
                    feature_predictions.append({
                        'name': f'Feature {i}',
                        'value': feature_value,
                        'prediction': prediction[0],
                        'probability': round(max(probability[0]) * 100, 2),
                        'is_positive': prediction[0] == "normal"
                    })

                all_feature_predictions.append({
                    'patient': {
                        'name': patient_name,
                        'age': patient_age,
                        'gender': patient_gender
                    },
                    'feature_predictions': feature_predictions
                })

            context = {
                'all_feature_predictions': all_feature_predictions
            }

            print(f"Context: {context}")
            return render(request, 'predictor/results.html', context)

        except Exception as e:
            return render(request, self.template_name, {
                'error': f'An error occurred: {str(e)}'
            })
    
class PredictionHistoryView(View):
    template_name = 'predictor/history.html'

    def get(self, request):
        patients = Patient.objects.all().prefetch_related('predictions').order_by('-created_at')
        context = {'patients': patients}
        return render(request, self.template_name, context)