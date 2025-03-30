from app import app
import os

if __name__ == "__main__":
    # Make sure the DATABASE_URL environment variable is set
    if not os.environ.get("DATABASE_URL"):
        print("Warning: DATABASE_URL environment variable is not set")
    
    app.run(host="0.0.0.0", port=5000, debug=True)