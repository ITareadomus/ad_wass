Update data file paths
```python
def load_selected_cleaners():
    with open('data/sel_cleaners.json', 'r', encoding='utf-8') as f:
        return json.load(f).get('cleaners', [])


def load_apartments():
    with open('data/mock_apartments.json', 'r', encoding='utf-8') as f:
        return json.load(f).get('apt', [])
```
Update data file paths
```python
def load_selected_cleaners():
    with open('data/sel_cleaners.json', 'r', encoding='utf-8') as f:
        return json.load(f).get('cleaners', [])


def load_apartments():
    with open('data/mock_apartments.json', 'r', encoding='utf-8') as f:
        return json.load(f).get('apt', [])
```
Update output file paths
```python
with open('data/assignments.json', 'w', encoding='utf-8') as f:
        json.dump({'assignment': assignments}, f, indent=4, ensure_ascii=False)
    logging.info("Assegnazioni salvate in 'data/assignments.json'.")