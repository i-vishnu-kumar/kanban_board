from datetime import datetime
curr_date = datetime.now().date()
curr_datetime = datetime.combine(curr_date, datetime.min.time())

def loader_data_manipulator(request, developer_name, loader_data_collection):
    """
    Handles MOP and total sprint count data.
    `loader_data_collection` is the MongoDB collection for loader data.
    """
    sprint_num_str = request.form.get("sprint_num")
    temp_name = request.form.get("temp_name")

    if not sprint_num_str or not temp_name:
        raise ValueError("Missing sprint number or MOP name for loader data.")

    sprint_num = int(sprint_num_str)

    existing_entry = loader_data_collection.find_one({"mop_name": temp_name})
    # if existing_entry:
    #     loader_data_collection.update_one(
    #         {"mop_name": temp_name},
    #         {"$set": {"total_sprint": sprint_num}}
    #     )
    #     print(f"Updated total sprints for MOP '{temp_name}' to {sprint_num}.")
    if not existing_entry:
        loader_data_collection.insert_one({
            "dev": developer_name,
            "mop_name": temp_name,
            "date": curr_datetime,
            "total_sprint": sprint_num,
            "completed_sprints": 0 
        })
        print(f"Inserted new loader entry for MOP '{temp_name}' with {sprint_num} sprints.")

    return temp_name, sprint_num_str 


def new_detailed_sprints_entry(developer_name, temp_name, sprint_num_str, det_entries_collection):
    """
    Creates a new detailed sprints entry in the database for a given MOP and developer.
    `det_entries_collection` is the MongoDB collection for detailed sprint data.
    """
    sprint_num = int(sprint_num_str)
    existing_entry = det_entries_collection.find_one({"dev_name": developer_name, "mop_name": temp_name})

    # if existing_entry:
    #     det_entries_collection.delete_one({"_id": existing_entry["_id"]})
    #     print(f"Detailed entry for {developer_name} - {temp_name} already exists. First deleting and creating new.")

    if not existing_entry:
        sprints_array = []
        for i in range(sprint_num):
            sprints_array.append({
                "sprint_index": i+1,
                "isSprint": False, 
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "DelayReason": "",
                "Completed": { 
                    "Title": "",
                    "Date": ""
                },
                "Incomplete_History": []
            })

        det_entries_collection.insert_one({
            "mop_name": temp_name,
            "dev_name": developer_name,
            "sprints": sprints_array
        })
        print(f"Created new detailed entry for {developer_name} - {temp_name} with {sprint_num} sprints.")

def edit_detailed_sprints_entry(developer_name, mop_name, det_entries_collection, request, loader_data_collection, curr_login_dev = ""):
    sprint_index = int(request.form.get("sprint_index"))  
    sprint_done = request.form.get("sprint_done") == "yes" 
    selected_date = request.form.get("selected_date")
    delay_reason = request.form.get("delay_reason")
    check_dev = det_entries_collection.find_one({"mop_name": mop_name})
    curr_dev = check_dev["dev_name"]
    print(curr_dev, curr_login_dev)
    if (curr_dev != curr_login_dev):
        return
    
    current_db_date_str = datetime.now().strftime("%Y-%m-%d")

    query = {"dev_name": developer_name, "mop_name": mop_name}

    if sprint_done:
        update_fields = {
            f"sprints.{sprint_index}.isSprint": True, 
            f"sprints.{sprint_index}.Completed.Title": f"Sprint {sprint_index + 1}",
            f"sprints.{sprint_index}.Completed.Date": selected_date,
            f"sprints.{sprint_index}.Date": selected_date
        }
        det_entries_collection.update_one(query, {"$set": update_fields})
        print(f"Sprint {sprint_index + 1} for {developer_name} - {mop_name} marked as COMPLETED.")
        loader_data_complete_manipulator(mop_name, loader_data_collection)
    else:
        update_fields = {
            f"sprints.{sprint_index}.isSprint": False,
            f"sprints.{sprint_index}.Date": selected_date, 
            f"sprints.{sprint_index}.DelayReason": delay_reason
        }
        det_entries_collection.update_one(query, {"$set": update_fields})

        if delay_reason and delay_reason.strip():
            det_entries_collection.update_one(
                query,
                {"$push": {f"sprints.{sprint_index}.Incomplete_History": {
                    "Date": current_db_date_str, 
                    "Reason": delay_reason.strip()
                }}}
            )
            print(f"Sprint {sprint_index + 1} for {developer_name} - {mop_name} updated. Delay reason added to history.")
        else:
            print(f"Sprint {sprint_index + 1} for {developer_name} - {mop_name} updated (no new delay reason).")

def loader_data_complete_manipulator(mop_name, loader_data_collection):
    existing_entry = loader_data_collection.find_one({"mop_name": mop_name})
    if existing_entry:
        completed_sprints = existing_entry["completed_sprints"]
        loader_data_collection.update_one(
            {"mop_name": mop_name},
            {"$set": {"completed_sprints": completed_sprints+1}}
        )
        print(f"Updated completed sprints from MOP '{completed_sprints-1}' to {completed_sprints}.")
