#!/bin/bash

echo "======================================"
echo "FileConverter - GitHub Setup Script"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d ".git" ]; then
    echo "Error: Please run this script from the FileConverter directory"
    exit 1
fi

echo "Step 1: Create GitHub Repository"
echo "================================"
echo ""
echo "Please go to: https://github.com/new"
echo ""
echo "Fill in:"
echo "  - Repository name: FileConverter (or your choice)"
echo "  - Description: Cross-platform file converter"
echo "  - Visibility: Public (for free GitHub Actions)"
echo "  - DON'T check any boxes (README, .gitignore, license)"
echo ""
read -p "Press ENTER once you've created the repository..."

echo ""
echo "Step 2: Enter Your GitHub Username"
echo "==================================="
echo ""
read -p "GitHub username: " GITHUB_USERNAME

if [ -z "$GITHUB_USERNAME" ]; then
    echo "Error: Username cannot be empty"
    exit 1
fi

REPO_URL="https://github.com/$GITHUB_USERNAME/FileConverter.git"

echo ""
echo "Step 3: Adding Remote"
echo "===================="
echo ""
git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"
echo "Remote added: $REPO_URL"

echo ""
echo "Step 4: Pushing Code to GitHub"
echo "=============================="
echo ""
echo "This will push your code (~50MB, no binaries)"
echo ""

git push -u origin main

if [ $? -ne 0 ]; then
    echo ""
    echo "Push failed! You may need to authenticate."
    echo ""
    echo "If you don't have SSH keys set up, you'll need a Personal Access Token:"
    echo "  1. Go to: https://github.com/settings/tokens"
    echo "  2. Generate new token (classic)"
    echo "  3. Select 'repo' scope"
    echo "  4. Use the token as your password when prompted"
    echo ""
    exit 1
fi

echo ""
echo "✅ Code pushed successfully!"
echo ""
echo "Step 5: Create First Release"
echo "============================"
echo ""
echo "This will tag version 1.0.0 and trigger GitHub Actions to build installers"
echo "for Linux, Windows, and macOS."
echo ""
read -p "Press ENTER to create v1.0.0 release..."

git tag v1.0.0
git push origin v1.0.0

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✅ SUCCESS!"
    echo "======================================"
    echo ""
    echo "Your release has been triggered!"
    echo ""
    echo "What's happening now:"
    echo "  - GitHub Actions is building on 3 platforms (Linux, Windows, macOS)"
    echo "  - Each platform is downloading FFmpeg and Pandoc"
    echo "  - Installers are being created"
    echo ""
    echo "This will take ~15-20 minutes."
    echo ""
    echo "Check progress:"
    echo "  https://github.com/$GITHUB_USERNAME/FileConverter/actions"
    echo ""
    echo "Download installers when ready:"
    echo "  https://github.com/$GITHUB_USERNAME/FileConverter/releases"
    echo ""
    echo "Expected files in release:"
    echo "  - FileConverter-1.0.0.AppImage (Linux, 620 MB)"
    echo "  - fileconverter_1.0.0_amd64.deb (Linux, 620 MB)"
    echo "  - FileConverter Setup 1.0.0.exe (Windows, 640 MB)"
    echo "  - FileConverter-1.0.0.dmg (macOS, 650 MB)"
    echo "  - FileConverter-1.0.0-mac.zip (macOS, 650 MB)"
    echo ""
else
    echo ""
    echo "Failed to push tag. Please check your network connection."
    exit 1
fi
