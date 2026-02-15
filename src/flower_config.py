from dotenv import dotenv_values

env_config = dotenv_values(".env")

# Flower configuration
port = 5555
max_tasks = 10000
auto_refresh = True
# db = "flower.db"

basic_auth = [ f'admin:{env_config["CELERY_FLOWER_PASSWORD"]}' ]
