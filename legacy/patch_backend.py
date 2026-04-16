import os
import re

service_file = 'backend/services/risk_service.py'
with open(service_file, 'r') as f:
    code = f.read()

# 1. get_employee_global_risk
code = code.replace(
    "def get_employee_global_risk(user_email: str, days: int = 7) -> Optional[float]:",
    "def get_employee_global_risk(user_email: str, days: int = 7, start_date: str = None, end_date: str = None) -> Optional[float]:"
)
code = code.replace(
    "days,\n        global_mode=True,\n    )",
    "days,\n        global_mode=True,\n        start_date=start_date,\n        end_date=end_date,\n    )"
)

# 2. get_employee_project_risk
code = code.replace(
    "def get_employee_project_risk(\n    user_email: str,\n    project_id: int,\n    days: int = 7\n) -> Optional[float]:",
    "def get_employee_project_risk(\n    user_email: str,\n    project_id: int,\n    days: int = 7,\n    start_date: str = None,\n    end_date: str = None\n) -> Optional[float]:"
)
code = code.replace(
    "global_mode=False,\n    )",
    "global_mode=False,\n        start_date=start_date,\n        end_date=end_date,\n    )"
)

# 3. get_team_global_risk
code = code.replace(
    "def get_team_global_risk(team_id: int, days: int = 7) -> Dict[str, Any]:",
    "def get_team_global_risk(team_id: int, days: int = 7, start_date: str = None, end_date: str = None) -> Dict[str, Any]:"
)
code = code.replace(
    "risk_01 = get_employee_global_risk(email, days)",
    "risk_01 = get_employee_global_risk(email, days, start_date, end_date)"
)
code = code.replace(
    "\"projects\": get_member_projects_breakdown(email, days),",
    "\"projects\": get_member_projects_breakdown(email, days, start_date, end_date),"
)

# 4. get_project_tactical_risk
code = code.replace(
    "def get_project_tactical_risk(project_id: int, days: int = 7) -> Dict[str, Any]:",
    "def get_project_tactical_risk(project_id: int, days: int = 7, start_date: str = None, end_date: str = None) -> Dict[str, Any]:"
)
code = code.replace(
    "risk_01 = get_employee_project_risk(email, project_id, days)",
    "risk_01 = get_employee_project_risk(email, project_id, days, start_date, end_date)"
)

# 5. get_member_projects_breakdown
code = code.replace(
    "def get_member_projects_breakdown(user_email: str, days: int = 7) -> List[Dict[str, Any]]:",
    "def get_member_projects_breakdown(user_email: str, days: int = 7, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:"
)
code = code.replace(
    "risk_01 = get_employee_project_risk(user_email, project_id, days)",
    "risk_01 = get_employee_project_risk(user_email, project_id, days, start_date, end_date)"
)

# 6. get_employee_risk_trend
code = code.replace(
    "def get_employee_risk_trend(user_email: str, days: int = 30) -> Dict[str, Any]:",
    "def get_employee_risk_trend(user_email: str, days: int = 30, start_date: str = None, end_date: str = None) -> Dict[str, Any]:"
)
code = code.replace(
    ", global_mode=True)",
    ", global_mode=True, start_date=start_date, end_date=end_date)"
)

# 7. get_employee_full_profile
code = code.replace(
    "def get_employee_full_profile(user_email: str, days: int = 7) -> Dict[str, Any]:",
    "def get_employee_full_profile(user_email: str, days: int = 7, start_date: str = None, end_date: str = None) -> Dict[str, Any]:"
)
code = code.replace(
    "risk_01 = get_employee_global_risk(user_email, days)",
    "risk_01 = get_employee_global_risk(user_email, days, start_date, end_date)"
)
code = code.replace(
    "breakdown = get_member_projects_breakdown(user_email, days)",
    "breakdown = get_member_projects_breakdown(user_email, days, start_date, end_date)"
)

# 8. get_team_risk_trend
code = code.replace(
    "def get_team_risk_trend(team_id: int, days: int = 30) -> Dict[str, Any]:",
    "def get_team_risk_trend(team_id: int, days: int = 30, start_date: str = None, end_date: str = None) -> Dict[str, Any]:"
)

# 9. get_project_risk_trend
code = code.replace(
    "def get_project_risk_trend(project_id: int, days: int = 30) -> Dict[str, Any]:",
    "def get_project_risk_trend(project_id: int, days: int = 30, start_date: str = None, end_date: str = None) -> Dict[str, Any]:"
)

with open(service_file, 'w') as f:
    f.write(code)

print("risk_service.py patched!")

# Now patch main.py
main_file = 'backend/main.py'
with open(main_file, 'r') as f:
    main_code = f.read()

# Replace endpoints
main_code = main_code.replace(
    "async def project_risk(request: Request, project_id: int, days: int = 7):",
    "async def project_risk(request: Request, project_id: int, days: int = 7, start_date: str = None, end_date: str = None):"
)
main_code = main_code.replace(
    "get_project_tactical_risk(project_id, days)",
    "get_project_tactical_risk(project_id, days, start_date, end_date)"
)

main_code = main_code.replace(
    "async def project_trend(request: Request, project_id: int, days: int = 30):",
    "async def project_trend(request: Request, project_id: int, days: int = 30, start_date: str = None, end_date: str = None):"
)
main_code = main_code.replace(
    "get_project_risk_trend(project_id, days)",
    "get_project_risk_trend(project_id, days, start_date, end_date)"
)

main_code = main_code.replace(
    "async def team_risk(request: Request, team_id: int, days: int = 7):",
    "async def team_risk(request: Request, team_id: int, days: int = 7, start_date: str = None, end_date: str = None):"
)
main_code = main_code.replace(
    "get_team_global_risk(team_id, days)",
    "get_team_global_risk(team_id, days, start_date, end_date)"
)

main_code = main_code.replace(
    "async def team_trend(request: Request, team_id: int, days: int = 30):",
    "async def team_trend(request: Request, team_id: int, days: int = 30, start_date: str = None, end_date: str = None):"
)
main_code = main_code.replace(
    "get_team_risk_trend(team_id, days)",
    "get_team_risk_trend(team_id, days, start_date, end_date)"
)

main_code = main_code.replace(
    "async def team_member_breakdown(request: Request, user_email: str, days: int = 7):",
    "async def team_member_breakdown(request: Request, user_email: str, days: int = 7, start_date: str = None, end_date: str = None):"
)
main_code = main_code.replace(
    "get_member_projects_breakdown(user_email, days)",
    "get_member_projects_breakdown(user_email, days, start_date, end_date)"
)

main_code = main_code.replace(
    "async def employee_profile(request: Request, user_email: str, days: int = 7):",
    "async def employee_profile(request: Request, user_email: str, days: int = 7, start_date: str = None, end_date: str = None):"
)
main_code = main_code.replace(
    "get_employee_full_profile(user_email, days)",
    "get_employee_full_profile(user_email, days, start_date, end_date)"
)

main_code = main_code.replace(
    "async def employee_trend(request: Request, user_email: str, days: int = 30):",
    "async def employee_trend(request: Request, user_email: str, days: int = 30, start_date: str = None, end_date: str = None):"
)
main_code = main_code.replace(
    "get_employee_risk_trend(user_email, days)",
    "get_employee_risk_trend(user_email, days, start_date, end_date)"
)

with open(main_file, 'w') as f:
    f.write(main_code)

print("main.py patched!")

