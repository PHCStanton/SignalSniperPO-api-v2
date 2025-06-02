# Test script to verify PocketOptionAPI-v2 installation
try:
    from pocketoptionapi.pocket import PocketOptionApi
    print("PocketOptionAPI-v2 library imported successfully!")
    print("Library version:", PocketOptionApi.__version__ if hasattr(PocketOptionApi, "__version__") else "Version not available")
except ImportError as e:
    print("Error importing PocketOptionAPI-v2:", e)
