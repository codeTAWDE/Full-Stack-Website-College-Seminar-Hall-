import os
from app import create_app

# Instantiate application
app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Run development server on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)