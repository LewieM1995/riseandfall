from database_operations import database_operations
from routes import army

def get_all_test_service():
    test_result = database_operations.get_all_test()
    return test_result

def check_army_route():
    return army.army_bp()
    