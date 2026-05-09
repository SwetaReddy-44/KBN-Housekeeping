import requests

plantuml_code = """
@startuml

skinparam class {
    BackgroundColor #F4F4FF
    BorderColor #A0A0D0
    ArrowColor #333333
    FontName Arial
}
skinparam shadowing false
skinparam defaultFontName Arial

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

' Layout hints
DatabaseConnector -[hidden]right- SystemAdmin

' Relationships top to bottom
SystemAdmin --> BookingManager : uses
SystemAdmin --> EmployeeManager : uses
SystemAdmin --> PayrollManager : uses

' Relationships bottom to top
BookingManager -up-> DatabaseConnector : uses
EmployeeManager -up-> DatabaseConnector : uses
PayrollManager -up-> DatabaseConnector : uses

@enduml
"""

response = requests.post('https://kroki.io/plantuml/png', data=plantuml_code.encode('utf-8'))
if response.status_code == 200:
    with open('class_diagram_styled.png', 'wb') as f:
        f.write(response.content)
    print('Successfully generated class_diagram_styled.png')
else:
    print('Failed:', response.status_code, response.text)
