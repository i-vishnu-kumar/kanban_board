def login_authorised(request, login_creds):
    username = request.form.get("username")
    password = request.form.get("password")
    data_creds = list(login_creds.find({}))

    for data in data_creds:
        if (str(username) == data["id"] and str(password) == data["pass"]):
            return True, data["name"]

    return False, ""
    
