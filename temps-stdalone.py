from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime

# Create a FastAPI app
app = FastAPI()

# Sample data: timestamps and average temperatures
timestamps = [
    "2024-12-01 12:00", "2024-12-02 12:00", "2024-12-03 12:00",
    "2024-12-04 12:00", "2024-12-05 12:00"
]
temperatures = [15.5, 17.3, 14.8, 16.1, 15.9]

# Convert timestamps to datetime objects
timestamps = [datetime.strptime(ts, "%Y-%m-%d %H:%M") for ts in timestamps]

@app.get("/", response_class=HTMLResponse)
async def home():  # No arguments required unless you need to use them
    # Create a plot
    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, temperatures, marker='o', linestyle='-', color='b')
    plt.title("Average Temperatures Over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("Average Temperature (°C)")
    plt.grid(True)
    
    # Save the plot to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close()
    
    # Encode the plot to base64 to display it in HTML
    plot_url = base64.b64encode(img.getvalue()).decode("utf8")
    
    # Render the plot in HTML
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Temperature Chart</title>
    </head>
    <body>
        <h1>Temperature Chart</h1>
        <img src="data:image/png;base64,{plot_url}" alt="Temperature Chart">
    </body>
    </html>
    """
    return HTMLResponse(content=html)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
