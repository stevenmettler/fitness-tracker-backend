import json
from src.models import create_session



def import_json(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            print(data)
            return create_session(data)
    except FileNotFoundError:
        return f'Error: file not found at path {file_path}'
    except json.JSONDecodeError:
        return "Error: Invalid JSON format in file"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

def add_workout():
    response = import_json("test/sample_workout.json")
    for workout in response.workouts:
        print(workout)
        print("\n---------\n")
    return response
