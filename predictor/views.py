from django.shortcuts import render
from .models import Patient, Prediction
from django.views import View
import joblib
import numpy as np
from pathlib import Path

# Get the current file directory
model_path = Path(__file__).resolve().parent / 'cc_model.pkl'
model = joblib.load(model_path)

class HomeView(View):
    template_name = 'predictor/home.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        try:
            # Collect patient information
            patient_name = request.POST.get('patient_name')
            patient_age = request.POST.get('patient_age')
            patient_gender = request.POST.get('patient_gender')

            # Validate patient information
            if not patient_name or len(patient_name) > 100:
                return render(request, self.template_name, {
                    'error': 'Please provide a valid patient name (max 100 characters).'
                })
            try:
                patient_age = int(patient_age)
                if patient_age < 0 or patient_age > 150:
                    raise ValueError
            except (ValueError, TypeError):
                return render(request, self.template_name, {
                    'error': 'Please provide a valid age (0-150).'
                })
            if patient_gender not in ['M', 'F', 'O']:
                return render(request, self.template_name, {
                    'error': 'Please select a valid gender.'
                })

            # Collect feature values dynamically
            features = []
            i = 1
            while f'feature{i}' in request.POST:
                feature_value = request.POST[f'feature{i}']
                try:
                    features.append(float(feature_value))
                except ValueError:
                    return render(request, self.template_name, {
                        'error': f'Invalid value for Feature {i}. Please enter a valid number.'
                    })
                i += 1

            if not features:
                return render(request, self.template_name, {
                    'error': 'No feature values provided.'
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
                prediction = model.predict(feature_array)
                probability = model.predict_proba(feature_array)

                # Save prediction to database
                Prediction.objects.create(
                    patient=patient,
                    feature_name=f'Feature {i}',
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

            context = {
                'feature_predictions': feature_predictions,
                'patient': {
                    'name': patient_name,
                    'age': patient_age,
                    'gender': patient_gender
                }
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