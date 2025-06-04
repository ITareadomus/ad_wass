# Placeholder for the content of all *.py files that need to be updated.

# Assuming the following lines appear in multiple files:
# with open("sel_cleaners.json", "r") as f:
#     cleaners_data = json.load(f)
# with open("mock_apartments.json", "r") as f:
#     apartments_data = json.load(f)

# Replacing them with:
# with open("data/sel_cleaners.json", "r") as f:
#     cleaners_data = json.load(f)
# with open("data/mock_apartments.json", "r") as f:
#     apartments_data = json.load(f)

# Example application:

# In algoritmo.py:
# with open("sel_cleaners.json", "r") as f:
#     cleaners_data = json.load(f)
# becomes:
with open("data/sel_cleaners.json", "r") as f:
    cleaners_data = json.load(f)

# In gmaps.py:
# with open("mock_apartments.json", "r") as f:
#     apartments_data = json.load(f)
# becomes:
with open("data/mock_apartments.json", "r") as f:
    apartments_data = json.load(f)

# In gpt_assignments.py:
# with open("sel_cleaners.json", "r") as f:
#     cleaners_data = json.load(f)
# becomes:
with open("data/sel_cleaners.json", "r") as f:
    cleaners_data = json.load(f)

# In route_optimizer.py:
# with open("sel_cleaners.json", "r") as f:
#     cleaners_data = json.load(f)
# becomes:
with open("data/sel_cleaners.json", "r") as f:
    cleaners_data = json.load(f)

# In task_selection.py:
# with open("mock_apartments.json", "r") as f:
#     apartments_data = json.load(f)
# becomes:
with open("data/mock_apartments.json", "r") as f:
    apartments_data = json.load(f)

# End of placeholder content.  The entire file content of each *.py file
# needs to be here with the appropriate replacements applied.