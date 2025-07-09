from initial import get_secrets_config, connect_to_database


############################# GLOBALS #############################

(secrets, Config) = get_secrets_config()

############################# Functions #############################


############## Get New Server and Vmess ##############
# async def get_vmess_start():
# try: 
db_client = connect_to_database(secrets['DBConString'])
# except Exception as e:
#     print("Failed to connect to the database!")

excluded_user_ids = ["user_id_1713825573", #reis
                     "user_id_5086060259", #@vvvpppnnnn#  
                     "user_id_432080595", #me 
                     ]


payments = db_client[secrets['DBName']].payments.find({
    "org": "rhvp-reis",
    "user_id": {"$nin": excluded_user_ids}
})

total = 0
number = 0
for amount in payments:
    number += 1
    total += int(amount['amount'])

print(total)
print(number)

db_client.close()

# def __main__ 
