# Installation Guide for LinkedIn Content Creator AI

This document provides step-by-step instructions for setting up and running the LinkedIn Content Creator AI application.

## System Requirements

- Python 3.11 or higher
- 2GB RAM minimum (4GB recommended)
- 500MB free disk space
- Internet connection
- Access to a MongoDB instance (local or remote)

## Required API Keys and Database Connection

- **Google Gemini API Key:** Required for AI-powered content generation  
  Obtain from [Google AI Studio](https://ai.google.dev/)
- **MongoDB URI:** Required to connect and save/retrieve profile, posts, feedback, and analysis  
  Typical local dev example: `mongodb://localhost:27017`

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/SakshamChouhan/linkedin-content-ai.git
cd linkedin-content-ai
```

### 2. Install Dependencies

All required dependencies are listed in `requirements.txt`.

```bash
pip install -r requirements.txt
```

### 3. Set Up Your Credentials in a .env File

1. **Create a file named `.env` in the project root (same folder as app.py)**
2. **Add these lines:**  
   ```
   GOOGLE_API_KEY=your_gemini_api_key
   MONGO_URI=your_mongodb_connection_string
   ```
   - *Do not wrap your API key or URI in quotes.*
   - `your_mongodb_connection_string` might look like `mongodb://localhost:27017` for a local setup.

3. **Save the file.**  
   The application will automatically read this file at startup.

### 4. Initialize the Database

The application uses MongoDB for all data storage (profiles, posts, feedback, analysis). Collections are created automatically when the app first runs and data is posted.

### 5. Run the Application

```bash
streamlit run app.py
```

This will start the Streamlit server and open the application in your default web browser.  
If it doesn't open automatically, go to [http://localhost:8501](http://localhost:8501) in your browser.

## Troubleshooting

### Common Issues

1. **Missing or Incorrect MongoDB URI**
   - Error: "Cannot connect" or "No database found"
   - Solution: Make sure you've added the `MONGO_URI` variable in your `.env` file and MongoDB is running/accessible.

2. **API Key Issues**
   - Error: "Invalid API key" or "Your default credentials were not found"
   - Solution: Make sure you've created the `.env` file as shown above and added your Gemini API key.

3. **Module Import Errors**
   - Error: "No module named X"
   - Solution: Make sure you've installed all required packages using pip.

4. **Port Already in Use**
   - Error: "Address already in use"
   - Solution: Change the port in the command:
     ```
     streamlit run app.py --server.port 8501
     ```

5. **Additional Dependency Errors**
   - You may need system-level dependencies (such as Python dev headers) for some packages, depending on your OS.

## Additional Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Google Generative AI Documentation](https://ai.google.dev/docs)
- [MongoDB Documentation](https://www.mongodb.com/docs/)

## Support

For questions or support, please create an issue in the GitHub repository or contact by email: raisaksham426@gmail.com directly.
