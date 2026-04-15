import json
import os
from datetime import datetime

DATA_FILE = "data/users.json"

DEFAULT_USERS = [
    {
        "email": "john.doe@company.com",
        "name": "John Doe",
        "role": "employee",
        "department": "Engineering",
        "status": "active",
        "license": "Microsoft 365 E3",
        "created_at": "2024-01-10",
        "password_reset_at": None,
    },
    {
        "email": "jane.smith@company.com",
        "name": "Jane Smith",
        "role": "admin",
        "department": "IT",
        "status": "active",
        "license": "Microsoft 365 E5",
        "created_at": "2023-06-15",
        "password_reset_at": None,
    },
    {
        "email": "bob.johnson@company.com",
        "name": "Bob Johnson",
        "role": "contractor",
        "department": "Marketing",
        "status": "inactive",
        "license": "None",
        "created_at": "2024-03-20",
        "password_reset_at": None,
    },
    {
        "email": "sarah.lee@company.com",
        "name": "Sarah Lee",
        "role": "employee",
        "department": "HR",
        "status": "active",
        "license": "Microsoft 365 E1",
        "created_at": "2024-02-05",
        "password_reset_at": None,
    },
]


def load_users():
    if not os.path.exists(DATA_FILE):
        save_users(DEFAULT_USERS)
        return DEFAULT_USERS
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=2)


def find_user(email: str):
    for u in load_users():
        if u["email"].lower() == email.lower():
            return u
    return None


def user_exists(email: str) -> bool:
    return find_user(email) is not None


def create_user(
    email: str,
    name: str,
    role: str = "employee",
    department: str = "",
    license_type: str = "None",
) -> dict:
    users = load_users()
    user = {
        "email": email,
        "name": name,
        "role": role,
        "department": department,
        "status": "active",
        "license": license_type,
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "password_reset_at": None,
    }
    users.append(user)
    save_users(users)
    return user


def reset_password(email: str) -> bool:
    users = load_users()
    for u in users:
        if u["email"].lower() == email.lower():
            u["password_reset_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_users(users)
            return True
    return False


def disable_user(email: str) -> bool:
    users = load_users()
    for u in users:
        if u["email"].lower() == email.lower():
            u["status"] = "inactive"
            save_users(users)
            return True
    return False


def enable_user(email: str) -> bool:
    users = load_users()
    for u in users:
        if u["email"].lower() == email.lower():
            u["status"] = "active"
            save_users(users)
            return True
    return False


def delete_user(email: str) -> bool:
    users = load_users()
    filtered = [u for u in users if u["email"].lower() != email.lower()]
    if len(filtered) < len(users):
        save_users(filtered)
        return True
    return False


def assign_license(email: str, license_type: str) -> bool:
    users = load_users()
    for u in users:
        if u["email"].lower() == email.lower():
            u["license"] = license_type
            save_users(users)
            return True
    return False


def assign_role(email: str, role: str) -> bool:
    users = load_users()
    for u in users:
        if u["email"].lower() == email.lower():
            u["role"] = role
            save_users(users)
            return True
    return False
