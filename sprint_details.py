def get_cons_sprint_list(developer_name, sprint_data):
    pipeline = [
        {
            "$match": {
                "dev": developer_name  
            }
        },
        {
            "$group": {
                "_id": "$mop_name",  
                "max_completed_sprints": {
                    "$max": "$completed_sprints"  
                },
                "total_sprint": {
                    "$first": "$total_sprint"
                },
                "date": {
                    "$first": "$date" 
                }
            }
        },
        {
            "$project": {
                "_id": 0, 
                "mop_name": "$_id", 
                "max_completed_sprints": 1,
                "total_sprint": 1,
                "date": 1
            }
        }
    ]
    
    result = list(sprint_data.aggregate(pipeline))
    for sprint in result:
        sprint['date'] = sprint['date'].strftime("%Y-%m-%d")
    return result
