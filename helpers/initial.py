import logging
import pymongo
import json
import os
from dotenv import load_dotenv
import gettext

load_dotenv()


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize gettext
def set_lang(locale, file):
    localedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'locales')
    translation = gettext.translation(file, localedir=localedir, languages=[locale], fallback=True
                                    #   , codeset='utf-8'
                                      )
    translation.install()
    return translation.gettext

def connect_to_database(db_con_string):
    print("trying to connect to db...")
    try: 
        db_client = pymongo.MongoClient(db_con_string)
        logging.info("Connected to the Database")
        return db_client
    except Exception as e:
        logging.error("Error Connecting to the Database!")
        logging.error(str(e))
        raise e

def get_secrets_config():
    env_variables = {key: os.environ.get(key) for key in os.environ.keys()}
    json_string = json.dumps(env_variables)
    Config = json.loads(json_string)

    with open(Config['secret_file'], 'r') as fp:
        secrets = json.load(fp)

    return (secrets, Config)
