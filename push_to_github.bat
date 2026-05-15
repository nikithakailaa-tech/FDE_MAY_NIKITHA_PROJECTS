@echo off
cd /d "C:\Users\nikitha.m\Downloads\complaint-tracker"
echo === Initializing Git repository ===
git init
git add .
git commit -m "Initial commit - Complaint Tracker"
git branch -M main
git remote remove origin 2>nul
git remote add origin https://github.com/nikithakailaa-tech/FDE_MAY15_NIKITHA_CMP_TR.git
echo === Pushing to GitHub ===
echo When asked for password, paste your GitHub Personal Access Token
git push -u origin main
echo.
echo === Done! Check GitHub for your code ===
pause
