import threading
import uvicorn
from consumer import start_consumer

def run_api():
    uvicorn.run("api:app", host="0.0.0.0", port=8000)

if __name__ == "__main__":
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    
    start_consumer()
