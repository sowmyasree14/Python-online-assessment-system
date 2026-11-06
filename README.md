# Python Basics Online Assessment

A Flask application for conducting a 20-question Python fundamentals assessment for multiple students.

## Features

- Student name and email collection
- 20 multiple-choice questions covering basic Python concepts
- Formatted Python code examples in each question
- Automatic scoring (1 mark per question, no negative marking)
- Result page with correct answers and explanations
- One attempt per email address
- Password-protected instructor dashboard
- CSV export of student results
- SQLite database by default; supports PostgreSQL through `DATABASE_URL`

## Project structure

```text
python-online-assessment/
├── app.py
├── requirements.txt
├── render.yaml
├── README.md
├── .gitignore
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── assessment.html
│   ├── result.html
│   ├── already_submitted.html
│   ├── admin_login.html
│   └── admin.html
└── static/
    └── style.css
```

## Run locally

Python 3.10 or newer is recommended.

1. Extract the project and open a terminal in its folder.
2. Create and activate a virtual environment:

   **Windows**
   ```bash
   py -m venv .venv
   .venv\\Scripts\\activate
   ```

   **macOS / Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set the required secrets. Use your own long, random values:

   **Windows PowerShell**
   ```powershell
   $env:SECRET_KEY = "replace-with-a-long-random-secret"
   $env:ADMIN_PASSWORD = "choose-a-strong-admin-password"
   ```

   **macOS / Linux**
   ```bash
   export SECRET_KEY="replace-with-a-long-random-secret"
   export ADMIN_PASSWORD="choose-a-strong-admin-password"
   ```

5. Start the app:

   ```bash
   python app.py
   ```

6. Open http://127.0.0.1:5000

The local SQLite database (`assessment.db`) is created automatically.

## Admin dashboard

Open `/admin/login` and enter the `ADMIN_PASSWORD` environment variable. The dashboard shows submissions, average score, and a CSV download.

For safety, set a strong `SECRET_KEY` and `ADMIN_PASSWORD` in the hosting provider's environment settings. Never commit passwords or `.env` files to GitHub.

## Deploy to GitHub

1. Create a new empty repository on GitHub.
2. Extract this project.
3. In a terminal opened in the extracted project folder, run:

   ```bash
   git init
   git add .
   git commit -m "Initial Python assessment app"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
   git push -u origin main
   ```

Replace the remote URL with your repository URL.

## Deploy on Render

This project includes `render.yaml` for a Render Blueprint deployment.

1. Push the project to GitHub.
2. In Render, choose **New → Blueprint** and connect the repository.
3. Review the resources and deploy.
4. When prompted for `ADMIN_PASSWORD`, enter a strong password.
5. After deployment, open the generated `onrender.com` URL. Add `/admin/login` to access the instructor dashboard.

The included Blueprint uses a **Starter web service and a 1 GB persistent disk** because student results must survive restarts and redeploys. Render's persistent disks are available on paid services. If you change to a free web service without a persistent disk or managed database, SQLite data can be lost when the service restarts or redeploys.

The app also supports PostgreSQL: set `DATABASE_URL` to your PostgreSQL connection string in Render instead of the SQLite URL. For a larger class or production use, managed PostgreSQL is generally preferable to SQLite.

## Important assessment notes

- The current version allows one attempt per email address. Email is used as a basic duplicate-submission check; it does not verify student identity.
- This is not a proctoring system. It does not prevent students from consulting other resources.
- Questions and correct answers are stored in `app.py`. Edit the `QUESTIONS` list to customize the assessment.
- The app creates database tables automatically on startup. Back up the database regularly.
- For a high-stakes exam, add verified student accounts, stronger anti-cheating controls, database migrations, and appropriate privacy notices.

## License

MIT. You may modify and use this project for educational purposes.
