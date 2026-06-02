import requests
import sys

def test_newsdata_io(api_key):
    print("\n--- Testing NewsData.io ---")
    # Fetching latest technology news
    url = f"https://newsdata.io/api/1/news?apikey={api_key}&q=technology"
    
    try:
        print("Sending request...")
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! NewsData.io API is working.")
            print(f"Status: {data.get('status')}")
            print(f"Total Results: {data.get('totalResults')}")
            
            if data.get('results'):
                print("\n--- First Article Snippet ---")
                first_article = data['results'][0]
                print(f"Title: {first_article.get('title')}")
                print(f"Source: {first_article.get('source_id')}")
                print(f"URL: {first_article.get('link')}")
            else:
                print("No articles found for the query.")
        else:
            print(f"❌ Failed! Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error occurred while connecting: {e}")

if __name__ == "__main__":
    api_key = input("Please enter your NewsData.io API key: ").strip()
    
    if not api_key:
        print("API key cannot be empty. Exiting.")
        sys.exit(1)
        
    test_newsdata_io(api_key)
