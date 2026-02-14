def get_filtered_rmops_data(loader_data_collection, domain_filter=None, developer_filter=None): 
    """
    Fetches RMOPs data from loader_data collection based on domain and/or developer filter.
    Returns a dictionary of {mop_name: dev_name}
    """
    query_filter = {
        "mop_name": {"$exists": True, "$ne": None},
        "dev": {"$exists": True, "$ne": None}, 
        "total_sprint": {"$exists": True},
        "completed_sprints": {"$exists": True},
        "$expr": { "$ne": ["$total_sprint", "$completed_sprints"] }
    }

    if domain_filter and domain_filter != 'ALL':
        regex_pattern = f".*{domain_filter}.*"
        query_filter["mop_name"]["$regex"] = regex_pattern
        query_filter["mop_name"]["$options"] = "i"

    if developer_filter and developer_filter != 'ALL':
        query_filter["dev"] = developer_filter 

    cursor = loader_data_collection.find(query_filter, {"mop_name": 1, "dev": 1, "_id": 0})

    rmops_dict = {}
    for doc in cursor:
        if 'mop_name' in doc and 'dev' in doc:
            rmops_dict[doc['mop_name']] = doc['dev']
    return rmops_dict


def get_all_devs_with_rmop_counts(loader_data, developers_collection):

    pipeline = [
        {
            "$match": {
                "mop_name": {"$exists": True, "$ne": None},
                "dev": {"$exists": True, "$ne": None},
                "total_sprint": {"$exists": True},
                "completed_sprints": {"$exists": True},
                "$expr": { "$ne": ["$total_sprint", "$completed_sprints"] }
            }
        },
        {
            "$group": {
                "_id": "$dev",
                "rmop_count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "_id": 0,
                "developer_name": "$_id",
                "rmop_count": 1
            }
        },
        {
            "$sort": {
                "rmop_count": -1
            }
        }
    ]
    dev_counts_sorted = list(loader_data.aggregate(pipeline))

    sorted_devs_with_active_rmops = [d['developer_name'] for d in dev_counts_sorted]

    all_dev_names_from_collection = []
    for doc in developers_collection.find({}):
        if 'developer' in doc:
            if isinstance(doc['developer'], list):
                all_dev_names_from_collection.extend(doc['developer'])
            else:
                all_dev_names_from_collection.append(doc['developer'])
    all_dev_names_from_collection = sorted(list(set(all_dev_names_from_collection))) 

    final_sorted_devs_list = sorted_devs_with_active_rmops[:] 

    for dev_name in all_dev_names_from_collection:
        if dev_name not in final_sorted_devs_list: 
            final_sorted_devs_list.append(dev_name)

    return final_sorted_devs_list


