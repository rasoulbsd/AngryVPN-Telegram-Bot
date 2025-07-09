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

users = [
    {
        "id": 224744156,
        "name": "qazule",
        "discount": 100
    },
    {
        "id": 75788887,
        "name": "arman",
        "discount": 100
    },
    {
        "id": 6131742028,
        "name": "mohsen_dayi",
        "discount": 100
    },
    {
        "id": 432080595,
        "name": "me",
        "discount": 100
    },
    {
        "id": 171114612,
        "name": "maman",
        "discount": 100
    },
    {
        "id": 5290997645,
        "name": "nasim_khale",
        "discount": 100
    },
    {
        "id": 129064798,
        "name": "bahar_mostafavi",
        "discount": 100
    },
    {
        "id": 105308049,
        "name": "zahra_mostafavi",
        "discount": 100
    },
    {
        "id": 420168264,
        "name": "parsa",
        "discount": 100
    },
    {
        "id": 221955281,
        "name": "moein",
        "discount": 100
    },
    {
        "id": 0,
        "name": "atefeh",
        "discount": 100
    },
    {
        "id": 0,
        "name": "sobi",
        "discount": 100
    },
    {
        "id": 104795032,
        "name": "mostafa",
        "discount": 100
    },
    {
        "id": 84648621,
        "name": "dr.zali",
        "discount": 100
    },
    {
        "id": 0,
        "name": "dr.manshaee",
        "discount": 100
    },
    {
        "id": 112465938,
        "name": "dr.hosseini",
        "discount": 100
    },
    {
        "id": 244506620,
        "name": "dr.javadi",
        "discount": 100
    },
    {
        "id": 684630739,
        "name": "ali",
        "discount": 100
    },
    {
        "id": 1952566514,
        "name": "asal",
        "discount": 100
    },
    {
        "id": 0,
        "name": "ali_maman",
        "discount": 100
    },
    {
        "id": 94201223,
        "name": "mona",
        "discount": 100
    },
    {
        "id": 89435337,
        "name": "negin",
        "discount": 100
    },
    {
        "id": 229091667,
        "name": "negeen",
        "discount": 100
    },
    {
        "id": 660536913,
        "name": "yasi",
        "discount": 100
    },
    {
        "id": 129626021,
        "name": "ala",
        "discount": 50
    },
    {
        "id": 136366233,
        "name": "ava",
        "discount": 50
    },
    {
        "id": 0,
        "name": "arman_baba",
        "discount": 100
    },
    {
        "id": 77178073,
        "name": "arman_maman",
        "discount": 100
    },
    {
        "id": 1368589203,
        "name": "radman",
        "discount": 100
    },
    {
        "id": 5753272636,
        "name": "zohreh_zandayi",
        "discount": 100
    },
    {
        "id": 57571674,
        "name": "mehrdad",
        "discount": 100
    },
    {
        "id": 542965396,
        "name": "sepehr",
        "discount": 100
    },
    {
        "id": 5867996338,
        "name": "hossein_dayi",
        "discount": 100
    },
    {
        "id": 2140306805,
        "name": "berke",
        "discount": 60
    },
    {
        "id": 5625430736,
        "name": "midori",
        "discount": 50
    },
    # 
    {
        "id": 800378944,
        "name": "mehrasa",
        "discount": 50
    },
    {
        "id": 283394016,
        "name": "alireza_nobakht",
        "discount": 50
    },
    {
        "id": 94342199,
        "name": "sana",
        "discount": 50
    },
    {
        "id": 86881412,
        "name": "eshagh",
        "discount": 50
    },
    {
        "id": 467071375,
        "name": "reihaneh",
        "discount": 50
    },
    {
        "id": 66678955,
        "name": "Arvin",
        "discount": 20
    },
    {
        "id": 0,
        "name": "nima",
        "discount": 20
    },
    {
        "id": 0,
        "name": "shakiba",
        "discount": 50
    },
    {
        "id": 0,
        "name": "amir_foxy",
        "discount": 50
    },
    {
        "id": 293068156,
        "name": "sara_soltani",
        "discount": 10
    },
    {
        "id": 253431075,
        "name": "arash_mary",
        "discount": 20
    },
    {
        "id": 497948290,
        "name": "jalali",
        "discount": 100
    },
    {
        "id": 469144590,
        "name": "maryam",
        "discount": 50
    },
    {
        "id": 187960083,
        "name": "bahar_nimbus",
        "discount": 20
    },
    {
        "id": 456997375,
        "name": "mehdi_fire_born",
        "discount": 20
    },
    {
        "id": 1047598451,
        "name": "soroush",
        "discount": 50
    },
    {
        "id": 0,
        "name": "mahdi_abbasi",
        "discount": 100
    },
]


for user in users:
    # db_client[secrets['DBName']].users.update_one({'user_id': user['id']}, {"$set": {f"orgs.{org_name}": {"expires": (datetime.datetime.now()+datetime.timedelta(days=62)).isoformat()}}})
    if (user['id'] == 0):
        continue
    db_client[secrets['DBName']].users.update_one(
        {'user_id': user['id']},
        {'$set': {'discount': user['discount']}}
    )
    print(f'User {user["name"]} updated with discount {user["discount"]}')
    # db_client[secrets['DBName']].users.update
# users_objects = db_client[secrets['DBName']].users.find({
#     "org": "rahbazkon-vip",
#     "user_id": {"$in": users}
# })

# total = 0
# number = 0
# for user_obj in users_objects:
#     user_ob

db_client.close()

# def __main__ 
