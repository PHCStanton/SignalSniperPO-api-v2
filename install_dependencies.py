import subprocess
import sys
import os

def install_dependencies():
    print("🔄 Installing required dependencies for Pocket Option WebSocket connection...")
    
    try:
        # Check if pip is available
        subprocess.check_call([sys.executable, "-m", "pip", "--version"])
        
        # Install from requirements.txt if it exists
        if os.path.exists("requirements.txt"):
            print("📦 Installing from requirements.txt...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        else:
            # Install the specific package needed
            print("📦 Installing websocket-client package...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "websocket-client>=1.3.2"])
        
        print("✅ Dependencies installed successfully!")
        print("🚀 You can now run the WebSocket connection test scripts.")
        
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        print("\n⚠️ Please install the required packages manually:")
        print("pip install websocket-client>=1.3.2")

if __name__ == "__main__":
    install_dependencies()
