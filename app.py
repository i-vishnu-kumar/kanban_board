
from flask import Flask, render_template, request, redirect, url_for, session
# from pymongo import MongoClient (Use in case of using MongoDB locally)
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import sprint_loader, sprint_details, login

uri = "Your MongoDB URI"

client = MongoClient(uri, server_api=ServerApi('1')) #Or use your local MongoDB client

developer_name = ""
db = client.loader
login_creds = db.login_creds
loader_data = db.mops_status
detailed_sprints = db.detailed_sprints

app = Flask(__name__)
app.secret_key = 'blabla123'

@app.route("/", methods = ["GET", "POST"])
def login_page():
    global developer_name
    login_status = None
    if request.method == "POST":
        login_status, developer_name =  login.login_authorised(request, login_creds)
        session["developer_name"] = developer_name
    try:
        if login_status:
            return redirect(url_for('loader', dev_name=developer_name))
    except Exception as e:
        print(f"Got an exception as {str(e)}")
    return render_template("login.html", login_status = login_status)

@app.route("/loader/<dev_name>", methods = ["GET", "POST"])
def loader(dev_name):
    try:
        print(request.method)
        return render_template("loader.html", dev_name=dev_name) 
    except Exception as e:
        print("Exception in loader function", str(e))

@app.route("/loader", methods = ["GET", "POST"])
def loader2():
    try:
        if (request.method == "POST"):
            temp_name, sprint_num = sprint_loader.loader_data_manipulator(request, developer_name, loader_data_collection=loader_data)
            current_dev_name = session.get("developer_name")
            session["temp_name"] = temp_name
            session["sprint_num"] = sprint_num
            sprint_loader.new_detailed_sprints_entry(developer_name, temp_name, sprint_num, detailed_sprints)
            return redirect(url_for('home', dev_name=current_dev_name, temp_name = temp_name))
    except Exception as e:
        print("Exception in loader function", str(e))
        return redirect(url_for('home', dev_name=developer_name, temp_name = ""))


@app.route("/home/<dev_name>/<temp_name>")
def home(dev_name, temp_name):
    try:
        sprint_document = detailed_sprints.find_one({
            "dev_name": dev_name, 
            "mop_name": temp_name
        })
        
        if sprint_document:
            sprints_data = sprint_document.get("sprints", [])
            completed_sprints = [sprint for sprint in sprints_data if sprint.get("isSprint", False)]
        else:
            sprints_data = []
            completed_sprints = []
            
        print(f"Found {len(sprints_data)} sprints for {dev_name} - {temp_name}")
        
        return render_template(
            "home.html", 
            dev_name=dev_name, 
            temp_name=temp_name, 
            sprint_num=session.get("sprint_num"),
            sprints_data=sprints_data,
            completed_sprints=completed_sprints
        )
    except Exception as e:
        print(f"Error in home route: {str(e)}")
        return render_template(
            "home.html", 
            dev_name=dev_name, 
            temp_name=temp_name, 
            sprint_num=session.get("sprint_num"),
            sprints_data=[],
            completed_sprints=[]
        )

@app.route("/home/<dev_name>/<temp_name>", methods=["POST"])
def home_page(dev_name, temp_name):
    try:
        sprint_loader.edit_detailed_sprints_entry(dev_name, temp_name, detailed_sprints, request, loader_data_collection=loader_data, curr_login_dev = session.get("developer_name"))
        return redirect(url_for('home', dev_name=dev_name, temp_name=temp_name))
    except Exception as e:
        print(f"Error in home_page POST: {str(e)}")
        return redirect(url_for('home', dev_name=dev_name, temp_name=temp_name))
    
@app.route("/remove_sprint/<dev_name>/<temp_name>", methods=["POST"])
def remove_sprint(dev_name, temp_name):
    try:
        # Find the document
        sprint_document = detailed_sprints.find_one({
            "dev_name": dev_name, 
            "mop_name": temp_name
        })
        
        if (session.get("developer_name") != dev_name):
            return {"status": "error", "message": "You do not have access to modify it!"}, 301
        
        if sprint_document and sprint_document.get("sprints"):
            sprints_list = sprint_document["sprints"]
            
            if len(sprints_list) > 0:
                detailed_sprints.update_one(
                    {"dev_name": dev_name, "mop_name": temp_name},
                    {"$pop": {"sprints": 1}} 
                )
                
                loader_data.update_one(
                    {"mop_name": temp_name},
                    {"$inc": {"total_sprint": -1}}
                )
                
                print(f"Removed last sprint for {dev_name} - {temp_name}")
                return {"status": "success"}, 200
            else:
                return {"status": "error", "message": "No sprints to remove"}, 400
        else:
            return {"status": "error", "message": "No sprint data found"}, 404
            
    except Exception as e:
        print(f"Error removing sprint: {str(e)}")
        return {"status": "error", "message": str(e)}, 500

@app.route("/add_sprint/<dev_name>/<temp_name>", methods=["POST"])
def add_sprint(dev_name, temp_name):
    try:
        # Find the document
        sprint_document = detailed_sprints.find_one({
            "dev_name": dev_name, 
            "mop_name": temp_name
        })
        if (session.get("developer_name") != dev_name):
            return {"status": "error", "message": "You do not have access to modify it!"}, 301
        
        if sprint_document:
            sprints_list = sprint_document.get("sprints", [])
            next_sprint_index = len(sprints_list) + 1
            
            # Create new sprint object (same structure as in new_detailed_sprints_entry)
            new_sprint = {
                "sprint_index": next_sprint_index,
                "isSprint": False, 
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "DelayReason": "",
                "Completed": { 
                    "Title": "",
                    "Date": ""
                },
                "Incomplete_History": []
            }
            
            # Add the new sprint to the end of the array
            detailed_sprints.update_one(
                {"dev_name": dev_name, "mop_name": temp_name},
                {"$push": {"sprints": new_sprint}}
            )
            
            # Also update the total sprint count in loader_data
            loader_data.update_one(
                {"mop_name": temp_name},
                {"$inc": {"total_sprint": 1}}  # Increase total sprint count by 1
            )
            
            print(f"Added new sprint {next_sprint_index} for {dev_name} - {temp_name}")
            return {"status": "success"}, 200
        else:
            return {"status": "error", "message": "No sprint data found"}, 404
            
    except Exception as e:
        print(f"Error adding sprint: {str(e)}")
        return {"status": "error", "message": str(e)}, 500


developers = db.developers
dev = developers.find({})[0]['developer']
@app.route("/developers")
def devs():
    return render_template("developers.html", developers = dev)

@app.route("/developers/<dev_name>")
def dev_page(dev_name):
    sprint_data = db.mops_status
    all_sprints = sprint_details.get_cons_sprint_list(dev_name, sprint_data)
    return render_template("dev_page.html", dev_name=dev_name, sprint_data = all_sprints)

if __name__ == "__main__":
    app.run(debug=True)
