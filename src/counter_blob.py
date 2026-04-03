
current_count = state.get('count', 0)
new_count = current_count + 1
state['count'] = new_count
result = f'Counter is now: {new_count}'

