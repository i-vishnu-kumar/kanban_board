import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
from bson.objectid import ObjectId
import sprint_loader, sprint_details, domain_loader, login, report_generator

load_dotenv()

mongo_db_user = os.environ.get("mongo_db_user")
mongo_db_pass = os.environ.get("mongo_db_pass")

uri = f"mongodb+srv://{Your_Mongo_DB_URI}"
client = MongoClient(uri, server_api=ServerApi('1'))

db = client.loader
login_creds = db.login_creds
loader_data = db.mops_status
detailed_sprints = db.detailed_sprints
developers_collection = db.developers
domains_collection = db.domains
weekly_reports = db.weekly_reports

app = Flask(__name__)
app.secret_key = 'currentsecret123'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'
login_manager.login_message_category = 'info'

class User(UserMixin):
    def __init__(self, user_id, username_login, display_name):
        self.id = user_id
        self.username = username_login 
        self.name = display_name      

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    try:
        user_data = login_creds.find_one({"_id": ObjectId(user_id)})
        if user_data:
            if 'username' not in user_data or 'name' not in user_data:
                print(f"Warning: User data for ID {user_id} missing 'username' or 'name' key in DB.")
                return None
            return User(user_data['_id'], user_data['username'], user_data['name']) 
    except Exception as e:
        print(f"Error loading user with ID {user_id}: {e}")
    return None

def get_all_dev_names():
    all_dev_names = []
    for doc in developers_collection.find({}):
        if 'developer' in doc:
            if isinstance(doc['developer'], list):
                all_dev_names.extend(doc['developer'])
            else:
                all_dev_names.append(doc['developer'])
    return sorted(list(set(all_dev_names)))

# --- Routes ---

@app.route("/", methods=["GET", "POST"])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('all_collections'))

    if request.method == "POST":
        username_input = request.form.get("username")
        password_input = request.form.get("password")

        user_doc = login.login_authorised(username_input, password_input, login_creds)

        if user_doc:
            user = User(user_doc['_id'], user_doc['username'], user_doc['name'])
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('all_collections'))
        else:
            flash('Invalid username or password.', 'danger')
            return render_template("login.html")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login_page'))


@app.route("/loader/<dev_name>", methods=["GET", "POST"])
@login_required
def loader(dev_name):
    if current_user.name != dev_name:
        flash("You are not authorized to load for this developer.", "warning")
        return redirect(url_for('all_collections'))
    try:
        return render_template("loader.html", dev_name=dev_name)
    except Exception as e:
        print(f"Exception in loader function: {str(e)}")
        flash(f"Error loading page: {str(e)}", 'danger')
        return redirect(url_for('all_collections'))


@app.route("/loader", methods=["GET", "POST"])
@login_required
def loader2():
    try:
        if request.method == "POST":
            current_developer_name = current_user.name
            temp_name, sprint_num_str = sprint_loader.loader_data_manipulator(request, current_developer_name, loader_data_collection=loader_data)
            sprint_loader.new_detailed_sprints_entry(current_developer_name, temp_name, sprint_num_str, detailed_sprints)
            flash(f"MOP '{temp_name}' created successfully!", 'success')
            return redirect(url_for('home', dev_name=current_developer_name, temp_name=temp_name))
    except Exception as e:
        print(f"Exception in loader2 function: {str(e)}")
        flash(f"Error in loader process: {str(e)}", 'danger')
    return redirect(url_for('all_collections'))


@app.route("/home/<dev_name>/<temp_name>")
@login_required
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

        return render_template(
            "home.html",
            dev_name=dev_name,
            temp_name=temp_name,
            sprints_data=sprints_data,
            completed_sprints=completed_sprints,
            current_user_display_name=current_user.name
        )
    except Exception as e:
        print(f"Error in home route: {str(e)}")
        flash(f"Error loading home page: {str(e)}", 'danger')
        return redirect(url_for('all_collections'))


@app.route("/home/<dev_name>/<temp_name>", methods=["POST"])
@login_required
def home_page(dev_name, temp_name):
    try:
        if current_user.name != dev_name:
            flash("You do not have permission to modify this MOP.", "danger")
            return redirect(url_for('home', dev_name=dev_name, temp_name=temp_name))

        sprint_loader.edit_detailed_sprints_entry(dev_name, temp_name, detailed_sprints, request, loader_data_collection=loader_data, curr_login_dev=current_user.name)
        flash("Sprint updated successfully!", 'success')
        return redirect(url_for('home', dev_name=dev_name, temp_name=temp_name))
    except Exception as e:
        print(f"Error in home_page POST: {str(e)}")
        flash(f"Error updating sprint: {str(e)}", 'danger')
        return redirect(url_for('home', dev_name=dev_name, temp_name=temp_name))


@app.route("/remove_sprint/<dev_name>/<temp_name>", methods=["POST"])
@login_required
def remove_sprint(dev_name, temp_name):
    try:
        if current_user.name != dev_name:
            return jsonify({"status": "error", "message": "You do not have access to modify it!"}), 403

        sprint_document = detailed_sprints.find_one({"dev_name": dev_name, "mop_name": temp_name})

        if sprint_document and sprint_document.get("sprints"):
            sprints_list = sprint_document["sprints"]
            if len(sprints_list) > 0:
                detailed_sprints.update_one({"dev_name": dev_name, "mop_name": temp_name}, {"$pop": {"sprints": 1}})
                loader_data.update_one({"mop_name": temp_name}, {"$inc": {"total_sprint": -1}})
                flash(f"Last sprint removed for {temp_name}.", 'success')
                return jsonify({"status": "success", "message": "Sprint removed successfully!"}), 200
            else:
                return jsonify({"status": "error", "message": "No sprints to remove"}), 400
        else:
            return jsonify({"status": "error", "message": "No sprint data found"}), 404
    except Exception as e:
        print(f"Error removing sprint: {str(e)}")
        flash(f"Error removing sprint: {str(e)}", 'danger')
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/add_sprint/<dev_name>/<temp_name>", methods=["POST"])
@login_required
def add_sprint(dev_name, temp_name):
    try:
        if current_user.name != dev_name:
            return jsonify({"status": "error", "message": "You do not have access to modify it!"}), 403

        sprint_document = detailed_sprints.find_one({"dev_name": dev_name, "mop_name": temp_name})

        if sprint_document:
            sprints_list = sprint_document.get("sprints", [])
            next_sprint_index = len(sprints_list) + 1
            new_sprint = {
                "sprint_index": next_sprint_index,
                "isSprint": False,
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "DelayReason": "",
                "Completed": {"Title": "", "Date": ""},
                "Incomplete_History": []
            }
            detailed_sprints.update_one({"dev_name": dev_name, "mop_name": temp_name}, {"$push": {"sprints": new_sprint}})
            loader_data.update_one({"mop_name": temp_name}, {"$inc": {"total_sprint": 1}})
            flash(f"Sprint {next_sprint_index} added for {temp_name}.", 'success')
            return jsonify({"status": "success", "message": "Sprint added successfully!"}), 200
        else:
            return jsonify({"status": "error", "message": "No sprint data found"}), 404
    except Exception as e:
        print(f"Error adding sprint: {str(e)}")
        flash(f"Error adding sprint: {str(e)}", 'danger')
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/kanban_board")
@login_required
def all_collections():
    devs_lst = domain_loader.get_all_devs_with_rmop_counts(loader_data, developers_collection)

    try:
        all_domains_doc = domains_collection.find_one({})
        all_domains = all_domains_doc.get('domain', []) if all_domains_doc else []
        if 'ALL' not in all_domains:
             all_domains.insert(0, 'ALL')
    except Exception as e:
        print(f"Error fetching domains: {e}")
        all_domains = ['ALL']

    mop_names_dict = domain_loader.get_filtered_rmops_data(loader_data, domain_filter='ALL')

    return render_template('collection_page.html', devs=devs_lst, rmops=mop_names_dict, domains=all_domains)


@app.route("/filter_rmops")
@login_required
def filter_rmops():
    selected_domain = request.args.get('domain', 'ALL')
    selected_developer = request.args.get('developer', 'ALL')

    print(f"Filtering RMOPS for domain: {selected_domain}, developer: {selected_developer}")

    filtered_rmops = domain_loader.get_filtered_rmops_data(
        loader_data,
        domain_filter=selected_domain,
        developer_filter=selected_developer
    )
    return jsonify(filtered_rmops=filtered_rmops)

@app.route("/developers")
@login_required
def devs_page():
    all_dev_names = get_all_dev_names()
    return render_template("developers.html", developers=all_dev_names)

@app.route("/developers/<dev_name>")
@login_required
def dev_page(dev_name):
    sprint_data = db.mops_status
    all_sprints = sprint_details.get_cons_sprint_list(dev_name, sprint_data)

    today = datetime.now().strftime("%Y-%m-%d")
    existing_report = weekly_reports.find_one({"dev_name": dev_name, "date": today})
    
    return render_template("dev_page.html", dev_name=dev_name, sprint_data = all_sprints, has_today_report=bool(existing_report))

@app.route("/generate_report/<dev_name>")
@login_required
def generate_report(dev_name):
    if current_user.name != dev_name:
        flash("You are not authorized to generate a report for this developer.", "danger")
        return redirect(url_for('all_collections'))
    
    report_content = report_generator.generate_report_content(
        dev_name, 
        loader_data, 
        detailed_sprints
    )

    today_date = datetime.now().strftime("%Y-%m-%d")
    existing_report_doc = weekly_reports.find_one({"dev_name": dev_name, "date": today_date})
    
    if existing_report_doc:
        report_content = existing_report_doc.get("report_content", report_content) 

    return render_template(
        "report.html", 
        dev_name=dev_name, 
        report_content=report_content,
        report_date=today_date 
    )

@app.route("/save_report", methods=["POST"])
@login_required
def save_report():
    dev_name = request.form.get("dev_name")
    report_date = request.form.get("report_date")
    report_content = request.form.get("report_content")

    if current_user.name != dev_name:
        flash("You are not authorized to save this report.", "danger")
        return redirect(url_for('all_collections'))

    if not dev_name or not report_date or report_content is None:
        flash("Missing report data.", "danger")
        return redirect(url_for('generate_report', dev_name=dev_name))

    weekly_reports.update_one(
        {"dev_name": dev_name, "date": report_date},
        {"$set": {"report_content": report_content, "last_updated": datetime.now()}},
        upsert=True 
    )
    flash("Weekly report saved successfully!", "success")
    return redirect(url_for('dev_page', dev_name=dev_name))

if __name__ == "__main__":
    app.run(debug=True)
