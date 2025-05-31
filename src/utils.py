import os

def ensure_templates():
    os.makedirs('templates', exist_ok=True)
    template_content = """
<!DOCTYPE html>
<html>
<head>
    <title>BGP Status Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { text-align: center; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        tr:nth-child(even) { background-color: #f9f9f9; }
        tr:hover { background-color: #f5f5f5; }
    </style>
</head>
<body>
    <h1>BGP Status Dashboard</h1>
    {{ table | safe }}
</body>
</html>
"""
    with open('templates/dashboard.html', 'w') as f:
        f.write(template_content)
