# Installation Guide for LinkedIn Content Creator AI

This document provides step-by-step instructions for setting up and running the LinkedIn Content Creator AI application.

## System Requirements

- Python 3.11 or higher
- 2GB RAM minimum (4GB recommended)
- 500MB free disk space
- Internet connection

## Required API Keys

- **Google Gemini API Key**: Required for AI-powered content generation
  - Obtain from [Google AI Studio](https://ai.google.dev/)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://SakshamChouhan/linkedin-content-ai.git
cd linkedin-content-ai
```

### 2. Install Dependencies

All required dependencies are listed in `requirements.txt`.

```bash
pip install requirements.txt
```

### 3. Set up Your Gemini API Key with a .env File

Instead of configuring environment variables in your shell, this application loads the Gemini API key from a `.env` file.

1. **Create a file named `.env` in the project root (same folder as app.py).**
2. **Add this line:**  
   ```
   GOOGLE_API_KEY=your_gemini_api_key
   ```
   Replace `your_gemini_api_key` with your actual Gemini API key from [Google AI Studio](https://ai.google.dev/).

3. **Save the file.**  
   The application will automatically read this file when starting.

### 4. Initialize the Database

The application uses SQLite for data storage. The database will be automatically created when you first run the application.

### 5. Run the Application

```bash
streamlit run app.py
```

This will start the Streamlit server and open the application in your default web browser. If it doesn't open automatically, you can access it at http://localhost:5000.

## Troubleshooting

### Common Issues

1. **API Key Issues**
   - Error: "Invalid API key" or "Your default credentials were not found"
   - Solution: Make sure you've created the `.env` file as described and added your Gemini API key.

2. **Module Import Errors**
   - Error: "No module named X"
   - Solution: Make sure you've installed all required packages using pip

3. **Port Already in Use**
   - Error: "Address already in use"
   - Solution: Change the port in the command: `streamlit run app.py --server.port 8501`

## Additional Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Google Generative AI Documentation](https://ai.google.dev/docs)

## Support

For questions or support, please create an issue in the GitHub repository or contact the by mail :- raisaksham426@gmail.com directly.
