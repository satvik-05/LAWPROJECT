#!/bin/bash

# Hugging Face Space Deployment Script with Token Authentication
# This script will help you push your code to Hugging Face Spaces

echo "🚀 Hugging Face Spaces Deployment Helper"
echo "=========================================="
echo ""
echo "📝 First-time setup:"
echo "1. Create a new Space at https://huggingface.co/new-space"
echo "   - Choose SDK: Streamlit"
echo "   - Note your Space name"
echo ""
echo "2. Create an access token:"
echo "   - Go to https://huggingface.co/settings/tokens"
echo "   - Click 'New token'"
echo "   - Give it a name (e.g., 'spaces-deploy')"
echo "   - Select 'Write' access"
echo "   - Copy the token"
echo ""

# Prompt for Hugging Face username
read -p "Enter your Hugging Face username: " HF_USERNAME

# Prompt for Space name
read -p "Enter your Space name (e.g., ipc-legal-assistant): " SPACE_NAME

# Prompt for access token
echo ""
echo "⚠️  Your token will be hidden as you type"
read -s -p "Enter your Hugging Face access token (from settings/tokens): " HF_TOKEN
echo ""

# Construct the remote URL with token
SPACE_URL="https://${HF_USERNAME}:${HF_TOKEN}@huggingface.co/spaces/${HF_USERNAME}/${SPACE_NAME}"
SPACE_URL_DISPLAY="https://huggingface.co/spaces/${HF_USERNAME}/${SPACE_NAME}"

echo ""
echo "Space URL: ${SPACE_URL_DISPLAY}"
echo ""

# Check if remote already exists
if git remote get-url space > /dev/null 2>&1; then
    echo "Updating existing 'space' remote..."
    git remote set-url space "${SPACE_URL}"
else
    echo "Adding 'space' remote..."
    git remote add space "${SPACE_URL}"
fi

echo ""
echo "📦 Pushing to Hugging Face Spaces..."
echo ""

# Push to space
git push --force space main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to Hugging Face Spaces!"
    echo ""
    echo "🎯 Next steps:"
    echo "1. Go to: ${SPACE_URL_DISPLAY}"
    echo "2. Wait for the build to start (check 'Logs' tab)"
    echo "3. Go to Settings → Variables and secrets"
    echo "4. Add these secrets:"
    echo ""
    echo "   Secret 1:"
    echo "   Name:  GEMINI_API_KEY"
    echo "   Value: [Your NEW Gemini API key]"
    echo ""
    echo "   Secret 2:"
    echo "   Name:  USE_GEMINI_LLM"
    echo "   Value: true"
    echo ""
    echo "   Secret 3:"
    echo "   Name:  GEMINI_MODEL"
    echo "   Value: gemini-1.5-flash"
    echo ""
    echo "5. The Space will rebuild automatically"
    echo "6. Wait ~5-10 minutes for completion"
    echo "7. Test your app!"
    echo ""
    echo "⚠️  CRITICAL: Generate a new Gemini API key!"
    echo "   Old key was exposed in chat: https://makersuite.google.com/app/apikey"
    echo ""
    
    # Remove token from remote for security
    git remote set-url space "https://huggingface.co/spaces/${HF_USERNAME}/${SPACE_NAME}"
    echo "✅ Token removed from git config for security"
else
    echo ""
    echo "❌ Push failed. Please check:"
    echo "1. Your access token is valid (create one at https://huggingface.co/settings/tokens)"
    echo "2. The token has 'Write' access"
    echo "3. The Space exists at: ${SPACE_URL_DISPLAY}"
    echo "4. You have write access to the Space"
    echo ""
    echo "Alternative: Upload files manually via the web interface:"
    echo "${SPACE_URL_DISPLAY}/tree/main"
    echo ""
    
    # Remove token from remote for security even on failure
    if git remote get-url space > /dev/null 2>&1; then
        git remote set-url space "https://huggingface.co/spaces/${HF_USERNAME}/${SPACE_NAME}"
    fi
fi
