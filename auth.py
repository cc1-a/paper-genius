def authenticate(username, password):
    if username == "amodh" and password == "amodh2006":
        return True, True  # Admin
    if username == "user" and password == "password":
        return True, False # Non-Admin
    return False, False