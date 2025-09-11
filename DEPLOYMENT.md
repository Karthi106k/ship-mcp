# 🚀 Deploying MCP Hotel Assistant to Render

## Prerequisites
- GitHub repository with your code
- Render account (free tier available)
- Environment variables ready

## Step-by-Step Deployment

### 1. **Push Code to GitHub**
```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### 2. **Create New Web Service on Render**
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select your `ohip-mcp` repository

### 3. **Configure Deployment Settings**
- **Name**: `ohip-mcp-hotel-assistant`
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements-render.txt`
- **Start Command**: `chainlit run mcp_chainlit_app.py --port $PORT --host 0.0.0.0`

### 4. **Set Environment Variables**
In Render dashboard, add these environment variables:

**🔑 Required Variables:**
```
GEMINI_API_KEY=your_gemini_api_key_here
HOSTNAME=https://mucu2ua.hospitality-api.us-ashburn-1.ocs.oc-test.com
CLIENT_ID=deepweaverai-JAPAC-UAT-PSALES-mucu2ua-Client
CLIENT_SECRET=idcscs-229c39f5-3a28-4d35-8163-57509b8d3f9b
ENTERPRISE_ID=PSALES
APP_KEY=d54eeb10-0f7e-425b-8fcf-5552a43855cd
```

**🐍 Python Configuration:**
```
PYTHON_VERSION=3.11.9
PYTHONPATH=/opt/render/project/src
```

### 5. **Deploy**
1. Click "Create Web Service"
2. Render will automatically build and deploy
3. Your app will be available at: `https://your-app-name.onrender.com`

## 🔧 Troubleshooting

### Common Issues:
1. **Build Fails**: Check `requirements-render.txt` for correct package versions
2. **Import Errors**: Verify `PYTHONPATH` is set to `/opt/render/project/src`
3. **Port Issues**: Render automatically sets `$PORT` - don't hardcode port 8000

### Logs:
- View logs in Render dashboard under "Logs" tab
- Look for startup messages like "MCPAgent initialized with Gemini 2.5 Flash"

## ✅ Verification
Once deployed, test these features:
- OAuth connection test
- Reservation lookup with hotel SYDH3 and reservation 218290
- Conversation memory (ask follow-up questions)

## 🎯 Production Tips
- Use Render's **Starter Plan** ($7/month) for better performance
- Enable **Auto-Deploy** from GitHub for automatic updates
- Set up **Health Checks** for monitoring
