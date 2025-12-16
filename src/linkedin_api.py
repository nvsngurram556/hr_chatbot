import requests
import json

# --- Configuration (REPLACE THESE) ---
# Your LinkedIn Page's ID (Organizational URN, e.g., 'urn:li:organization:123456')

# The text content for your post

# --- End Configuration ---

def publish_linkedin_post(org_urn, access_token, post_text):
    """
    Publishes a text post to a LinkedIn Page and returns the URL.
    """
    
    # 1. Prepare the API Headers
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": "202510"
    }

    # 2. Prepare the Payload for the Share API
    # The 'author' is the URN of the organization posting.
    # The 'lifecycleState' must be 'PUBLISHED'.
    # The 'content.contentEntities' is optional for simple text shares.
    payload = {
        "author": org_urn,
        "lifecycleState": "PUBLISHED",
        "commentary": post_text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED"
        }
    }

    # 3. Make the POST request to the UGC Posts API
    api_url = "https://api.linkedin.com/rest/posts"
    
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        
        # The response headers will contain the UGC Post URN (ID)
        # e.g., /v2/ugcPosts/urn:li:ugcPost:6844437435133464576
        post_urn = response.headers.get("x-restli-id")

        if post_urn:
            # Construct the user-facing URL for the post.
            # The structure is typically: https://www.linkedin.com/feed/update/{ugcPost_urn}/
            # We need to extract the actual ID part (e.g., 6844437435133464576)
            post_id = post_urn.split(":")[-1]
            post_url = f"https://www.linkedin.com/feed/update/{post_id}/"
            
            # Create an object/dictionary to store the collected data
            post_object = {
                "post_urn": post_urn,
                "post_id": post_id,
                "post_url": post_url
            }
            
            print("✅ Post published successfully!")
            print(f"Post URL: {post_url}")
            return post_object
        else:
            print("⚠️ Success response but could not find 'x-restli-id' header.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ An error occurred during the API call: {e}")
        if 'response' in locals() and response.text:
            print(f"Error details: {response.text}")
        return None


def main():
    ORG_URN = "urn:li:organization:109573414"
# Your Developer Access Token (must have the w_organization_social permission)
    ACCESS_TOKEN = "AQXZ9DGnlPHsZImVe_4T_aqzij_i1Q1IpBtSRifpdO3xknIgHccIIHFg3HowXE4YO5LUFJ1Fw4iaHtR5Fw2mmKrcTkmvThJMVWRxj-CnCtBtKJxapdil7owOU9gLyG1DaRWEwZ5T_kNJWrPW_4yBn9GdW0s1b-yiDQkaPFNJJbbuWwaID0GD1Dl7I6y8v4nXBkWgepjI5POas0_g8yWJjX6oXHu4lIzx5jH22sTxv4AVmnojqQuzE2Rsdyox2g3dse5MZlbiPVB2Esh5k81gecNcu7nFeheUSGVanyjHpfqQThAF9fEBPvGSR8aI61htlv549qf0WLDCWl8xPxjhBx7v6_2Ozg"
    POST_TEXT = ("Hello Everyone! This is a post created for collecting sample resumes for my Dissertation project.\n"
             "Please help me by applying for the position with your resumes.\n"
             "For applying the position please fill the form below:\n"
             "https://docs.google.com/forms/d/e/1FAIpQLSdSACdRA6KOjY-SXQl0unwXJK3_dxDFSrQyECKqpWCZ1EfnPw/viewform?usp=sharing&ouid=111372244744191018484\n"
             "Thank you for your response!\n"
             "#LinkedInAPI #Automation #POC")
    post_info = publish_linkedin_post(ORG_URN, ACCESS_TOKEN, POST_TEXT)
    print(json.dumps(post_info, indent=4))

if __name__ == "__main__":
    main()

        # You can now use the 'post_info["post_urn"]' for deletion later
        # The deletion endpoint is: DELETE https://api.linkedin.com/v2/ugcPosts/{post_urn}
        # Example: print(f"URN for deletion: {post_info['post_urn']}")
