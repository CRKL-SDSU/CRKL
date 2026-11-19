# Purpose: loader.py will load each translated entry into its respective table
# - no need to create an entirely new database connection, as this *should* rely on the connection established in db_management.py
# - in addition to loading the data into the 4 super entity tables, this file should also handle loading data into the junction tables:
#   - mission_agencies
#   - mission_spacecraft
#   - mission_launches

