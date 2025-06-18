from .models import Medication, MedicationLog


def create_medication(user, name, dose, times_per_day, dose_times):
    medication = Medication.objects.create(
        user=user,
        name=name,
        dose=dose,
        times_per_day=times_per_day,
        dose_times=dose_times,
    )
    return medication


def update_medication(medication, name, dose, times_per_day, dose_times):
    medication.name = name
    medication.dose = dose
    medication.times_per_day = times_per_day
    medication.dose_times = dose_times
    medication.save()
    return medication


def delete_medication(medication):
    medication.delete()


def log_medication(user, medication, date, time_taken, dose_index):
    log = MedicationLog.objects.create(
        user=user,
        medication=medication,
        date=date,
        time_taken=time_taken,
        dose_index=dose_index,
    )
    return log
