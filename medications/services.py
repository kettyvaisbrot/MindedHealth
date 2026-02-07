from .models import Medication

def delete_medication(medication: Medication) -> None:
    medication.delete()
