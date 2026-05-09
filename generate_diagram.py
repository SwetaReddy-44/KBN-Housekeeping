import requests

plantuml_code = """
@startuml

class DatabaseConnector {
    -connectionString : String
    -connection : Object
    +get_db_connection() : Object
    +init_db() : void
}

class SystemAdmin {
    -adminId : int
    -username : String
    -password : String
    +login(password : String) : boolean
    +logout() : void
    +viewReports() : void
}

class BookingManager {
    -bookingList : List
    +createBooking(data : Object) : void
    +fetchBookings() : List
}

class EmployeeManager {
    -employeeList : List
    +addEmployee(data : Object) : void
    +deleteEmployee(id : int) : void
}

class PayrollManager {
    -salaryRecords : List
    -attendanceRecords : List
    +addSalaryRecord(data : Object) : void
    +logAttendance(data : Object) : void
}

' Relationships
SystemAdmin --> BookingManager : uses
SystemAdmin --> EmployeeManager : uses
SystemAdmin --> PayrollManager : uses

BookingManager --> DatabaseConnector : uses
EmployeeManager --> DatabaseConnector : uses
PayrollManager --> DatabaseConnector : uses

@enduml
"""

response = requests.post('https://kroki.io/plantuml/png', data=plantuml_code.encode('utf-8'))
if response.status_code == 200:
    with open('class_diagram.png', 'wb') as f:
        f.write(response.content)
    print('Successfully generated class_diagram.png')
else:
    print('Failed:', response.status_code, response.text)
