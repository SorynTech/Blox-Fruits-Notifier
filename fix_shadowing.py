import sys

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Replace html = in handle_health, handle_stats, handle_suspended
    # Use a more targeted approach to avoid accidental replacements if any

    new_content = content.replace('html = HEALTH_PAGE.format', 'response_html = HEALTH_PAGE.format')
    new_content = new_content.replace('text=html, content_type=\'text/html\'', 'text=response_html, content_type=\'text/html\'')
    new_content = new_content.replace('html = STATS_PAGE.format', 'response_html = STATS_PAGE.format')
    new_content = new_content.replace('html = SUSPENDED_PAGE.format', 'response_html = SUSPENDED_PAGE.format')

    with open(filepath, 'w') as f:
        f.write(new_content)

if __name__ == "__main__":
    fix_file('main.py')
